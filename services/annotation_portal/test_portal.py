"""Persistence and local API integration checks using temporary fixture data."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from server import Catalog, Store, Conflict, make_server, validate_review

class PersistenceTests(unittest.TestCase):
    def test_utf8_persistence_and_history_survive_reopen(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'reviews.sqlite3';store=Store(path)
            first=store.save('sample',0,{'text':'Total ₹25 • é','status':'draft'})
            second=store.save('sample',1,{'text':'Total ₹30','status':'needs_review'})
            reopened=Store(path)
            self.assertEqual(reopened.latest('sample')['text'],'Total ₹30')
            self.assertEqual(reopened.history('sample')[1]['text'],first['text'])
            self.assertEqual(reopened.all_latest()['sample']['revision'],2)
    def test_stale_save_does_not_destroy_another_review(self):
        with tempfile.TemporaryDirectory() as temp:
            store=Store(Path(temp)/'reviews.sqlite3');store.save('sample',0,{'text':'First'})
            with self.assertRaises(Conflict):store.save('sample',0,{'text':'Stale'})
            self.assertEqual(store.latest('sample')['text'],'First')
            self.assertEqual(len(store.history('sample')),1)
    def test_verification_requires_name_and_explicit_confirmation(self):
        data=dict(text='Receipt',label='receipt',status='verified',expected_revision=0)
        detail=dict(record=dict(label='receipt',split='train',image_path='image.jpg',source_path='source.jpg'),reference_path=None,reference_sha256=None)
        with self.assertRaises(ValueError):validate_review(data,detail)
        data.update(reviewer='Test reviewer',verified_confirmation=True)
        self.assertTrue(validate_review(data,detail)['human_verified'])
        data['reviewer_type']='ai'
        with self.assertRaises(ValueError):validate_review(data,detail)
        data['reviewer_type']='human'
        data['status']='draft'
        self.assertFalse(validate_review(data,detail)['human_verified'])

class PortalAPITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name);self.root=root;service=root/'services/document_classifier';service.mkdir(parents=True)
        (service/'data').mkdir();(service/'data/manifest.csv').write_text('sample_id,image_path,label,source_path,include\nfixture,data/fixture.jpg,receipt,source.jpg,yes\n',encoding='utf-8')
        (service/'data/fixture.jpg').write_bytes(b'fixture-image')
        (service/'data/splits.csv').write_text('sample_id,split\nfixture,train\n',encoding='utf-8')
        drafts=root/'Dataset/annotations/ocr_drafts';drafts.mkdir(parents=True)
        (drafts/'fixture.json').write_text(json.dumps(dict(full_text='Raw OCR',sample_id='fixture',status='unreviewed_ocr_draft')),encoding='utf-8')
        self.server=make_server(0,root/'test.sqlite3',Catalog(root))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url='http://127.0.0.1:'+str(self.server.server_port)
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()
    def request(self,path,data=None,headers=None):
        req=Request(self.url+path,data=json.dumps(data).encode('utf-8') if data is not None else None,headers=headers or {})
        with urlopen(req) as response:return json.load(response)
    def activate_scope(self,known=True):
        folder=self.root/'Dataset/annotations/scope/test-version';folder.mkdir(parents=True)
        (folder/'manifest.csv').write_text('sample_id,include,scope_status,content_style,scope_reason\n'+('fixture,no,excluded_handwriting,handwriting_dependent,Handwritten transaction fields\n' if known else 'other,yes,eligible,printed,Printed\n'),encoding='utf-8')
        (folder.parent/'active.json').write_text(json.dumps(dict(version='test-version',manifest='Dataset/annotations/scope/test-version/manifest.csv')),encoding='utf-8')
        self.server.catalog=Catalog(self.root)
    def test_excluded_scope_is_read_only_but_history_remains(self):
        self.server.store.save('fixture',0,dict(text='Historic review',label='receipt',status='draft',human_verified=False))
        self.activate_scope()
        catalog=self.request('/api/catalog');self.assertFalse(catalog['records'][0]['scope_eligible'])
        detail=self.request('/api/record/fixture');self.assertEqual(detail['saved']['text'],'Historic review')
        payload=dict(text='New review',label='receipt',status='draft',expected_revision=1)
        with self.assertRaises(HTTPError) as caught:self.request('/api/record/fixture',payload,{'X-Review-Token':catalog['token']})
        self.assertEqual(caught.exception.code,400);caught.exception.close()
        exported=self.request('/api/export');self.assertEqual(exported['records'],[]);self.assertEqual(exported['withheld_out_of_scope'],1)
        full=self.request('/api/export-catalog');self.assertEqual(full['records'][0]['history'][0]['text'],'Historic review')
    def test_unassessed_sample_is_not_admitted_when_scope_active(self):
        self.activate_scope(known=False)
        row=self.request('/api/catalog')['records'][0]
        self.assertFalse(row['scope_eligible']);self.assertEqual(row['scope_status'],'unassessed')
    def test_ocr_without_reference_is_visible_and_save_is_revisioned(self):
        catalog=self.request('/api/catalog');r=catalog['records'][0]
        self.assertFalse(r['has_reference']);self.assertEqual(r['ocr_sources'],1)
        detail=self.request('/api/record/fixture');self.assertEqual(detail['drafts'][0]['text'],'Raw OCR')
        payload=dict(text='Receipt ₹25',label='receipt',status='draft',expected_revision=0,reviewer='Fixture reviewer')
        headers={'Content-Type':'application/json','X-Review-Token':catalog['token']}
        saved=self.request('/api/record/fixture',payload,headers);self.assertEqual(saved['revision'],1)
        self.assertFalse(saved['human_verified'])
        self.assertEqual(self.request('/api/export')['records'][0]['text'],'Receipt ₹25')
        with self.assertRaises(HTTPError) as caught:self.request('/api/record/fixture',payload,headers)
        self.assertEqual(caught.exception.code,409);caught.exception.close()
        self.assertEqual(len(self.request('/api/record/fixture')['history']),1)
    def test_cross_origin_write_and_unknown_image_are_rejected(self):
        token=self.request('/api/catalog')['token']
        with self.assertRaises(HTTPError) as caught:self.request('/api/record/fixture',{}, {'X-Review-Token':token,'Origin':'http://example.invalid'})
        self.assertEqual(caught.exception.code,403);caught.exception.close()
        with self.assertRaises(HTTPError) as caught:self.request('/image/unknown')
        self.assertEqual(caught.exception.code,404);caught.exception.close()
    def test_invalid_payload_does_not_create_review(self):
        token=self.request('/api/catalog')['token']
        with self.assertRaises(HTTPError) as caught:self.request('/api/record/fixture',{'text':'','label':'receipt','status':'draft','expected_revision':0},{'X-Review-Token':token})
        self.assertEqual(caught.exception.code,400);caught.exception.close()
        self.assertEqual(self.request('/api/export')['records'],[])

if __name__=='__main__':unittest.main()
