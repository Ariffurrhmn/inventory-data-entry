"""Controlled evidence-boundary tests, not document accuracy measurements."""
import base64,io,json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from PIL import Image
from gateway import Store,extraction_prompt
from region_evidence import combine,make_region_processor
from test_contract import fixture

class RegionEvidenceTests(unittest.TestCase):
    def test_gateway_keeps_classifier_ocr_and_verifies_against_exact_region_source(self):
        text,record=fixture()
        class Predictor:
            def predict_image(self,path):return {'label':'receipt','ocr_text':'original primary'}
        calls=[]
        def process(path,sid,primary):
            calls.append(sid)
            return {'ocr_text':combine(primary,text),'human_verified':False}
        image=io.BytesIO();Image.new('RGB',(20,20),'white').save(image,format='PNG')
        data={'filename':'input.png','image_base64':base64.b64encode(image.getvalue()).decode()}
        with TemporaryDirectory() as temp:
            store=Store(Path(temp)/'test.sqlite3',Predictor(),process)
            result,replay=store.submit('region-test',data)
            self.assertFalse(replay)
            self.assertEqual(result['classification']['ocr_text'],'original primary')
            self.assertIn(text,json.loads(result['prompt'].split('BEGIN_UNTRUSTED_DOCUMENT_JSON\n')[1].split('\nEND_UNTRUSTED_DOCUMENT_JSON')[0])['ocr_text'])
            complete=store.attach(result['submission_id'],record)
            self.assertTrue(all(x['status']=='supported' for x in complete['verification']['evidence_findings']))
            replayed,flag=store.submit('region-test',data)
            self.assertTrue(flag);self.assertEqual(len(calls),1)
            self.assertEqual(replayed['extraction_source'],result['extraction_source'])
            reopened=Store(Path(temp)/'test.sqlite3',Predictor())
            self.assertEqual(reopened.get(result['submission_id'])['extraction_source'],result['extraction_source'])
    def test_geometry_priority_never_chooses_by_ocr_values_and_no_grid_stays_primary(self):
        with TemporaryDirectory() as temp:
            root=Path(temp)
            def analyze(image,output,tessdata):
                output.mkdir();(output/'result.json').write_text('{}')
                return {'source_sha256':'a'*64,'candidates':[
                    {'method':'axis_grid','layout':{'tables':[{}]},'ocr':{'returncode':1,'ocr_text':'failed'}},
                    {'method':'deskew_grid','layout':{'tables':[{}]},'ocr':{'returncode':0,'ocr_text':'exact region'}}]}
            with patch('localization.analyze',side_effect=analyze):
                result=make_region_processor(root,'unused')('unused','s1','primary')
            self.assertEqual(result['method'],'deskew_grid');self.assertEqual(result['ocr_text'],combine('primary','exact region'))
            self.assertFalse(result['human_verified'])
            def empty(image,output,tessdata):
                output.mkdir();(output/'result.json').write_text('{}')
                return {'source_sha256':'a'*64,'candidates':[]}
            with patch('localization.analyze',side_effect=empty):
                result=make_region_processor(root,'unused')('unused','s2','primary')
            self.assertEqual(result['ocr_text'],'primary');self.assertEqual(result['status'],'no_grid_primary_only')
if __name__=='__main__':unittest.main()
