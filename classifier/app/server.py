"""Supervisor demo. Local inference, explicit recorded examples, deliberate report saves."""
import argparse,base64,binascii,io,json,mimetypes,secrets,sys,tempfile,threading,time,uuid
from collections import OrderedDict
from datetime import datetime,timezone
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
APP=Path(__file__).resolve().parent;HOME=APP.parent;ENGINE=HOME/'engine'
sys.path.insert(0,str(ENGINE))
from PIL import Image,ImageOps,UnidentifiedImageError
from inference import Predictor
from explain import explain_prediction
from text_common import sha
APP_ID='document-lab-supervisor-v1'

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def preview(path):
 with Image.open(path) as raw:
  if raw.width*raw.height>25000000:raise ValueError('Choose an image under 25 megapixels.')
  image=ImageOps.exif_transpose(raw).convert('RGB');image.thumbnail((1600,1600))
  data=io.BytesIO();image.save(data,format='JPEG',quality=86)
 return 'data:image/jpeg;base64,'+base64.b64encode(data.getvalue()).decode()
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def send(self,data,status=200,mime='application/json',filename=None):
  raw=json.dumps(data,ensure_ascii=False).encode() if mime=='application/json' else data
  self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
  if filename:self.send_header('Content-Disposition','attachment; filename="'+filename+'"')
  self.end_headers()
  try:self.wfile.write(raw)
  except (BrokenPipeError,ConnectionAbortedError,ConnectionResetError):pass
 def local(self):return self.headers.get('Host') in [f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}']
 def remember(self,report):
  report['analysis_id']=uuid.uuid4().hex;report['created_at']=datetime.now(timezone.utc).isoformat()
  with self.server.records_lock:
   self.server.records[report['analysis_id']]={k:v for k,v in report.items() if k!='preview'}
   while len(self.server.records)>20:self.server.records.popitem(last=False)
  return report
 def do_GET(self):
  if not self.local():return self.send({'error':'Open the local demo address.'},403)
  path=urlparse(self.path).path
  if path=='/api/info':
   return self.send(dict(app_id=APP_ID,app_root=str(HOME),token=self.server.token,model=self.server.predictor.metadata(),evaluation=self.server.evaluation,classes=['purchase_order','receipt','delivery_note','customer_copy']))
  if path=='/api/examples':return self.send(self.server.examples)
  if path.startswith('/api/examples/'):
   pieces=path.strip('/').split('/')
   if len(pieces)!=4 or pieces[2] not in self.server.example_map:return self.send({'error':'Example not found'},404)
   item=self.server.example_map[pieces[2]]
   if pieces[3]=='image':
    return self.send((HOME/item['image']).read_bytes(),mime='image/jpeg')
   if pieces[3]=='recorded':
    saved=read(HOME/item['record'])
    if saved['result']['model_sha256']!=self.server.predictor.model_hash:return self.send({'error':'This example belongs to a different model.'},409)
    return self.send(self.remember(dict(result=saved['result'],explanation=saved['explanation'],mode='recorded',file_name=item['title'],sample_id=item['id'],expected_label=item['expected_label'],provenance=item['provenance'],source_image_sha256=item['image_sha256'],note='Recorded development analysis using actual cached OCR. No new inference performed.')))
  assets={'/':APP/'index.html','/assets/style.css':APP/'assets/style.css','/assets/app.js':APP/'assets/app.js'}
  if path in assets:
   file=assets[path];return self.send(file.read_bytes(),mime=mimetypes.guess_type(file.name)[0] or 'application/octet-stream')
  self.send({'error':'Not found'},404)
 def do_POST(self):
  origin=self.headers.get('Origin')
  allowed=[f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}']
  if not self.local() or self.headers.get('X-Demo-Token')!=self.server.token or (origin and origin not in allowed):return self.send({'error':'Reload the demo to start a new session.'},403)
  try:
   length=int(self.headers.get('Content-Length',0))
   if not 0<length<=32*1024*1024:raise ValueError('Choose an image smaller than 20 MB.')
   data=json.loads(self.rfile.read(length))
   if not isinstance(data,dict):raise ValueError('Invalid request.')
   path=urlparse(self.path).path
   if path=='/api/save':
    with self.server.records_lock:record=self.server.records.get(data.get('analysis_id'))
    if record is None:raise ValueError('Analyze or load a document before saving.')
    folder=self.server.export_dir;folder.mkdir(exist_ok=True);name='analysis-'+record['analysis_id']+'.json';target=folder/name
    if not target.exists():
     with target.open('x',encoding='utf8') as handle:json.dump(record,handle,ensure_ascii=False,indent=2)
    return self.send(dict(filename=name,folder='classifier/exports'))
   if path!='/api/analyze':return self.send({'error':'Not found'},404)
   start=time.perf_counter();image_preview=None
   with self.server.inference_lock:
    if 'text' in data:
     text=data['text']
     if not isinstance(text,str) or len(text)>200000:raise ValueError('Paste less than 200,000 characters of OCR text.')
     result=self.server.predictor.predict_text(text);name='Pasted OCR text'
    else:
     name=Path(str(data.get('filename',''))).name;suffix=Path(name).suffix.lower()
     if suffix not in ['.jpg','.jpeg','.png','.webp','.heic','.heif','.tif','.tiff','.bmp']:raise ValueError('Choose a JPEG, PNG, WebP, HEIC or TIFF image.')
     encoded=data.get('image_base64')
     if not isinstance(encoded,str):raise ValueError('Choose a document image.')
     raw=base64.b64decode(encoded,validate=True)
     if not 0<len(raw)<=20*1024*1024:raise ValueError('Choose a nonempty image smaller than 20 MB.')
     if suffix in ['.heic','.heif']:
      from pillow_heif import register_heif_opener
      register_heif_opener()
     with tempfile.TemporaryDirectory(prefix='document-lab-') as temporary:
      image=Path(temporary)/('upload'+suffix);image.write_bytes(raw)
      with Image.open(image) as check:check.verify()
      image_preview=preview(image)
      result=self.server.predictor.predict_image(image)
    explanation=explain_prediction(self.server.predictor,result['ocr_text'],heading_text=result.get('heading_ocr_text'),result=result)
   self.send(self.remember(dict(result=result,explanation=explanation,mode='live',file_name=name,elapsed_seconds=round(time.perf_counter()-start,2),preview=image_preview,note='Computed locally from this input. Uploaded images are not retained.')))
  except (ValueError,TypeError,KeyError,binascii.Error,UnidentifiedImageError,Image.DecompressionBombError) as error:self.send({'error':str(error)},400)
  except Exception as error:
   print(type(error).__name__+': '+str(error),flush=True);self.send({'error':'Analysis failed. Try a clearer printed image or inspect the local log.'},500)
def make_server(port=8770):
 predictor=Predictor();server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
 server.export_dir=HOME/'exports'
 server.predictor=predictor;server.token=secrets.token_urlsafe(32);server.inference_lock=threading.Lock();server.records_lock=threading.Lock();server.records=OrderedDict()
 server.examples=read(HOME/'demo/manifest.json');server.example_map={x['id']:x for x in server.examples}
 for item in server.examples:
  if sha(HOME/item['image'])!=item['image_sha256']:raise ValueError('Example integrity check failed.')
 completion=read(ENGINE/'runs'/predictor.run/'completion.json')
 server.evaluation=dict(validation=completion['validation'],training_oof=completion['training_oof'],training_n=150,validation_n=25,historical_test_excluded=27,scope='Printed documents only',limitations='Adaptive development evidence, not an independent final accuracy estimate. Two validation customer copies remain misclassified.')
 return server
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8770);args=parser.parse_args()
 with make_server(args.port) as server:
  print('Document Lab ready: http://127.0.0.1:'+str(server.server_port),flush=True)
  server.serve_forever()


