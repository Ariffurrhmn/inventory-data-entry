"""Checks for the Supervisor Showcase server. Run: py -3.14 -m unittest discover -s supervisor_showcase/tests"""
import json
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import server as showcase  # noqa: E402


class ShowcaseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.notes = tempfile.TemporaryDirectory()
        showcase.NOTES = Path(cls.notes.name)
        cls.srv = showcase.make_server(0, load_live=True)
        cls.base = f'http://127.0.0.1:{cls.srv.server_port}'
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.info = cls.get('/api/info')

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        cls.notes.cleanup()

    @classmethod
    def get(cls, path, raw=False):
        with urllib.request.urlopen(cls.base + path, timeout=30) as res:
            data = res.read()
        return data if raw else json.loads(data)

    def post(self, path, body, token=True):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['X-Showcase-Token'] = self.info['token']
        req = urllib.request.Request(self.base + path, data=json.dumps(body).encode(), headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=120) as res:
                return res.status, json.loads(res.read())
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read())

    def wait_live(self):
        for _ in range(120):
            info = self.get('/api/info')
            if info['live_ready'] or info['live_error']:
                return info
            time.sleep(0.5)
        self.fail('live classifier did not load')

    def test_gallery_matches_recorded_validation(self):
        gallery = self.get('/api/gallery')
        self.assertEqual(len(gallery), 25)
        self.assertEqual(sum(g['correct'] for g in gallery), self.info['evaluation']['validation']['correct'])
        self.assertTrue(all(g['has_image'] for g in gallery))
        self.assertEqual({g['id'] for g in gallery if not g['correct']}, {'cdd7aaa9004d', '33a6690bb891'})

    def test_headline_numbers_match_completion(self):
        show = self.get('/api/showcase')
        ev = self.info['evaluation']
        values = {k['label']: k['value'] for k in show['headline']}
        v, t = ev['validation'], ev['training_oof']
        self.assertEqual(values['Validation documents correct'], f"{v['correct']} / {v['n']}")
        self.assertEqual(values['Grouped training check'], f"{t['correct']} / {t['n']}")
        selected = [j for j in show['journey'] if j['kept']]
        self.assertEqual((selected[0]['correct'], selected[0]['n']), (v['correct'], v['n']))
        val_counts = show['dataset']['splits'][1]['counts']
        self.assertEqual(sum(val_counts.values()), v['n'])
        for i, cls in enumerate(self.info['classes']):
            self.assertEqual(val_counts[cls], sum(v['confusion_matrix'][i]))
        train_counts = show['dataset']['splits'][0]['counts']
        for i, cls in enumerate(self.info['classes']):
            self.assertEqual(train_counts[cls], sum(t['confusion_matrix'][i]))

    def test_recorded_record_and_images(self):
        rec = self.get('/api/gallery/76cc99d39da4')
        self.assertEqual(rec['mode'], 'recorded')
        self.assertEqual(rec['result']['label'], 'purchase_order')
        self.assertEqual(rec['result']['model_sha256'], self.info['model']['model_sha256'])
        thumb = self.get('/api/gallery/76cc99d39da4/image?size=thumb', raw=True)
        full = self.get('/api/gallery/76cc99d39da4/image', raw=True)
        self.assertTrue(thumb.startswith(b'\xff\xd8') and full.startswith(b'\xff\xd8'))
        self.assertLess(len(thumb), len(full))

    def test_static_pages_and_unknown_paths(self):
        self.assertIn(b'Classifier Showcase', self.get('/', raw=True))
        self.assertIn(b'--c-po', self.get('/styles.css', raw=True))
        for path in ('/api/gallery/000000000000', '/../server.py', '/web/../server.py'):
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                self.get(path)
            self.assertEqual(ctx.exception.code, 404)

    def test_post_requires_token(self):
        status, _ = self.post('/api/analyze', {'text': 'PURCHASE ORDER'}, token=False)
        self.assertEqual(status, 403)

    def test_notes_save_and_list(self):
        status, body = self.post('/api/notes', {'meeting_date': '2026-11-05', 'supervisor': 'Test', 'summary': ['a → b'],
                                                'decisions': [], 'markdown': '# Notes\n'})
        self.assertEqual(status, 200)
        self.assertTrue((showcase.NOTES / body['file']).exists())
        notes = self.get('/api/notes')
        self.assertEqual(notes[0]['supervisor'], 'Test')
        status, _ = self.post('/api/notes', {'markdown': '  '})
        self.assertEqual(status, 400)

    def test_live_text_uses_selected_model(self):
        info = self.wait_live()
        self.assertTrue(info['live_ready'], info['live_error'])
        status, report = self.post('/api/analyze', {'text': 'DELIVERY CHALLAN\nChallan No: 22\nReceived the goods in good condition'})
        self.assertEqual(status, 200, report)
        self.assertEqual(report['result']['label'], 'delivery_note')
        self.assertEqual(report['result']['model_sha256'], info['model']['model_sha256'])
        self.assertEqual(report['explanation']['rule']['kind'], 'exact_heading')
        status, _ = self.post('/api/analyze', {'text': '   '})
        self.assertEqual(status, 400)


if __name__ == '__main__':
    unittest.main()
