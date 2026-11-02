"""Local upload/OCR/classification app. No raw uploads are retained."""
import argparse,base64,binascii,json,mimetypes,secrets,tempfile,threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
from PIL import Image,UnidentifiedImageError
from inference import Predictor
from text_common import HERE

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send_json(self,data,status=200):
        raw=json.dumps(data,ensure_ascii=False).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
    def valid_host(self):return self.headers.get('Host') in [f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}']
    def do_GET(self):
        if not self.valid_host():return self.send_json({'error':'Use the local classifier address.'},403)
        path=urlparse(self.path).path
        if path=='/api/model':return self.send_json(dict(token=self.server.token,**self.server.predictor.metadata()))
        if path=='/':
            raw=(HERE/'classifier.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();return self.wfile.write(raw)
        self.send_json({'error':'Not found'},404)
    def do_POST(self):
        origin=self.headers.get('Origin')
        if not self.valid_host() or self.headers.get('X-Classifier-Token')!=self.server.token or (origin and origin not in [f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}']):return self.send_json({'error':'Reload the local classifier to start a new session.'},403)
        if urlparse(self.path).path!='/api/classify':return self.send_json({'error':'Not found'},404)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<=0 or length>32*1024*1024:raise ValueError('Choose an image smaller than 20 MB.')
            data=json.loads(self.rfile.read(length))
            with self.server.inference_lock:
                if 'text' in data:
                    if not isinstance(data['text'],str) or len(data['text'])>200000:raise ValueError('Invalid OCR text.')
                    result=self.server.predictor.predict_text(data['text'])
                else:
                    suffix=Path(data.get('filename','')).suffix.lower()
                    if suffix not in ['.jpg','.jpeg','.png','.webp','.heic','.heif','.tif','.tiff','.bmp']:raise ValueError('Choose a JPEG, PNG, WebP, HEIC or TIFF document image.')
                    raw=base64.b64decode(data.get('image_base64',''),validate=True)
                    if not raw or len(raw)>20*1024*1024:raise ValueError('Choose a nonempty image smaller than 20 MB.')
                    if suffix in ['.heic','.heif']:
                        from pillow_heif import register_heif_opener
                        register_heif_opener()
                    with tempfile.TemporaryDirectory(prefix='printed-classifier-') as temp:
                        image_path=Path(temp)/('document'+suffix);image_path.write_bytes(raw)
                        with Image.open(image_path) as image:image.verify()
                        result=self.server.predictor.predict_image(image_path)
                if data.get('explain',True):
                    from explain import explain_prediction
                    result['explanation']=explain_prediction(self.server.predictor,result['ocr_text'],heading_text=result.get('heading_ocr_text'),result=result)
            self.send_json(result)
        except (ValueError,KeyError,TypeError,binascii.Error,UnidentifiedImageError) as exc:self.send_json({'error':str(exc)},400)
        except Exception as exc:
            print(type(exc).__name__+': '+str(exc),flush=True)
            self.send_json({'error':'Could not process this document. Check the local server log or try another image.'},500)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8767);args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    server.predictor=Predictor();server.token=secrets.token_urlsafe(32);server.inference_lock=threading.Lock()
    print(f'Printed classifier: http://127.0.0.1:{server.server_port} | {server.predictor.run}/{server.predictor.name}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
