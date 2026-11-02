import json,sys,tempfile,threading,unittest,urllib.request,urllib.error
from pathlib import Path
from unittest.mock import patch
HOME=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HOME/'app'))
import server

class DemoTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.server=server.make_server(0);cls.server.export_dir=Path(cls.temp.name)
  cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start();cls.url='http://127.0.0.1:'+str(cls.server.server_port)
 @classmethod
 def tearDownClass(cls):
  cls.server.shutdown();cls.server.server_close();cls.thread.join();cls.temp.cleanup()
 def request(self,path,data=None,token=True):
  headers={'Content-Type':'application/json'}
  if token:headers['X-Demo-Token']=self.server.token
  request=urllib.request.Request(self.url+path,data=json.dumps(data).encode() if data is not None else None,headers=headers)
  with urllib.request.urlopen(request,timeout=30) as response:return json.load(response)
 def test_recorded_example_is_traceable_and_does_not_run_ocr(self):
  example=self.server.examples[0]
  with patch.object(self.server.predictor,'predict_image',side_effect=AssertionError('Recorded mode ran OCR')):
   r=self.request('/api/examples/'+example['id']+'/recorded')
  self.assertEqual(r['mode'],'recorded');self.assertEqual(r['source_image_sha256'],example['image_sha256'])
  self.assertEqual(r['result']['model_sha256'],self.server.predictor.model_hash)
  self.assertIn('explanation',r)
 def test_live_text_includes_actual_rule_explanation_and_save_is_explicit(self):
  r=self.request('/api/analyze',{'text':'Purchase Order\nOrder No:42\nRequired By: Friday\nPlease supply goods'})
  self.assertEqual(r['mode'],'live');self.assertEqual(r['result']['label'],'purchase_order')
  self.assertTrue(r['explanation']['method'].startswith('deterministic'))
  self.assertFalse((self.server.export_dir/('analysis-'+r['analysis_id']+'.json')).exists())
  saved=self.request('/api/save',{'analysis_id':r['analysis_id']})
  report=json.loads((self.server.export_dir/saved['filename']).read_text(encoding='utf8'))
  self.assertEqual(report['result']['label'],'purchase_order');self.assertNotIn('preview',report)
 def test_token_required(self):
  with self.assertRaises(urllib.error.HTTPError) as caught:self.request('/api/analyze',{'text':'Purchase Order'},False)
  self.assertEqual(caught.exception.code,403);caught.exception.close()
 def test_empty_text_and_invalid_images_rejected(self):
  for payload in [{'text':''},{'filename':'bad.jpg','image_base64':'bm90IGFuIGltYWdl'},[]]:
   with self.subTest(payload=payload):
    with self.assertRaises(urllib.error.HTTPError) as caught:self.request('/api/analyze',payload)
    self.assertEqual(caught.exception.code,400);caught.exception.close()
 def test_example_paths_cannot_read_other_files(self):
  with self.assertRaises(urllib.error.HTTPError) as caught:self.request('/api/examples/../image')
  self.assertEqual(caught.exception.code,404);caught.exception.close()
if __name__=='__main__':unittest.main()

