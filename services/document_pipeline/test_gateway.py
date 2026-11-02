"""Isolated HTTP/SQLite integration checks; no real OCR, dataset or runtime writes."""
import base64
from concurrent.futures import ThreadPoolExecutor
import http.client
import json
import gc
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import unittest

from gateway import make_server, strict_json
from test_contract import fixture


class FakePredictor:
    def __init__(self):
        self.calls = 0
        self.image_calls = 0
        self.lock = threading.Lock()
        self.entered = threading.Event()
        self.release = None
        self.fail = False

    def predict_text(self, text):
        with self.lock:
            self.calls += 1
        self.entered.set()
        if self.release is not None:
            if not self.release.wait(5):
                raise TimeoutError('test did not release inference')
        if self.fail:
            raise RuntimeError('controlled OCR/classifier failure')
        return {'label': 'receipt', 'ocr_text': text}

    def predict_image(self, path):
        self.image_calls += 1
        raise AssertionError('corrupt image should not reach predictor')


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(prefix='gateway-integration-')
        self.database = Path(self.temp.name) / 'test.sqlite3'
        self.predictor = FakePredictor()
        self.server = make_server(0, self.database, self.predictor)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        gc.collect()
        self.temp.cleanup()

    def request(self, method, path, data=None, headers=None, auth=True, raw=None):
        merged = {'Host': f'127.0.0.1:{self.server.server_port}'}
        if auth:
            merged['Authorization'] = 'Bearer ' + self.server.token
        if data is not None or raw is not None:
            merged['Content-Type'] = 'application/json'
        if headers:
            merged.update(headers)
        body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=10)
        try:
            connection.request(method, path, body=body, headers=merged)
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    def submit(self, key='key-1', text=None):
        if text is None:
            text = fixture()[0]
        return self.request('POST', '/api/submissions', {'text': text}, {'Idempotency-Key': key})

    def test_handoff_preserves_exact_ocr_and_no_automatic_llm(self):
        status, body = self.submit()
        self.assertEqual(status, 201)
        result = body['result']
        self.assertEqual(result['state'], 'awaiting_extraction')
        self.assertEqual(result['classification']['ocr_text'], fixture()[0])
        self.assertIn('BEGIN_UNTRUSTED_DOCUMENT_JSON', result['prompt'])
        self.assertIn('Provisional downstream extraction contract', result['prompt'])
        self.assertFalse(result['automatic_llm_available'])
        self.assertFalse(body['replayed'])
        self.assertEqual(self.predictor.calls, 1)

    def test_same_key_replays_and_different_payload_conflicts(self):
        _, first = self.submit()
        status, replay = self.submit()
        self.assertEqual(status, 200)
        self.assertTrue(replay['replayed'])
        self.assertEqual(first['result']['submission_id'], replay['result']['submission_id'])
        status, _ = self.submit(text='Different request')
        self.assertEqual(status, 409)
        self.assertEqual(self.predictor.calls, 1)

    def test_concurrent_same_key_runs_predictor_once(self):
        self.predictor.release = threading.Event()
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(self.submit)
            self.assertTrue(self.predictor.entered.wait(3))
            try:
                status, replay = self.submit()
                self.assertEqual(status, 200)
                self.assertTrue(replay['replayed'])
                self.assertEqual(replay['result']['state'], 'processing')
            finally:
                self.predictor.release.set()
            status, original = first.result(timeout=5)
        self.assertEqual(status, 201)
        self.assertEqual(original['result']['submission_id'], replay['result']['submission_id'])
        self.assertEqual(self.predictor.calls, 1)

    def test_rejected_extraction_logged_then_valid_retry_and_immutable_result(self):
        _, body = self.submit()
        sid = body['result']['submission_id']
        path = f'/api/submissions/{sid}/extraction'
        status, _ = self.request('POST', path, {'bad': 'record'})
        self.assertEqual(status, 400)
        self.assertEqual(self.server.store.get(sid)['state'], 'awaiting_extraction')
        with self.server.store.db() as db:
            attempts = db.execute('SELECT content,outcome FROM attempts WHERE submission=? ORDER BY id', (sid,)).fetchall()
        self.assertEqual(len(attempts), 1)
        self.assertEqual(json.loads(attempts[0]['content']), {'bad': 'record'})
        self.assertTrue(attempts[0]['outcome'].startswith('rejected:'))
        record = fixture()[1]
        status, result = self.request('POST', path, record)
        self.assertEqual(status, 200)
        self.assertEqual(result['state'], 'completed')
        self.assertFalse(result['verification']['review_required'])
        status, repeated = self.request('POST', path, record)
        self.assertEqual(status, 200)
        self.assertEqual(repeated['extraction_sha256'], result['extraction_sha256'])
        record['uncertainties'] = ['New interpretation']
        status, _ = self.request('POST', path, record)
        self.assertEqual(status, 409)
        self.assertEqual(self.server.store.get(sid)['verification']['record']['uncertainties'], [])
        with self.server.store.db() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM attempts WHERE submission=?', (sid,)).fetchone()[0], 2)

    def test_wrong_route_rejected_and_consumer_preserves_review(self):
        _, body = self.submit()
        sid = body['result']['submission_id']
        self.assertEqual(self.request('GET', f'/api/consumer/{sid}')[0], 409)
        record = fixture()[1]
        record['document_type'] = 'delivery_note'
        self.assertEqual(self.request('POST', f'/api/submissions/{sid}/extraction', record)[0], 400)
        record['document_type'] = 'receipt'
        record['evidence'].pop('/totals/tax')
        self.assertEqual(self.request('POST', f'/api/submissions/{sid}/extraction', record)[0], 200)
        status, consumer = self.request('GET', f'/api/consumer/{sid}')
        self.assertEqual(status, 200)
        self.assertEqual(consumer['status'], 'blocked_for_review')
        self.assertTrue(consumer['review_required'])
        self.assertFalse(consumer['inventory_updated'])
        self.assertEqual(consumer['record'], record)

    def test_consumer_never_claims_real_inventory_update(self):
        _, body = self.submit()
        sid = body['result']['submission_id']
        self.request('POST', f'/api/submissions/{sid}/extraction', fixture()[1])
        status, consumer = self.request('GET', f'/api/consumer/{sid}')
        self.assertEqual(status, 200)
        self.assertEqual(consumer['status'], 'eligible_for_external_review')
        self.assertEqual(consumer['consumer'], 'demonstration_stub')
        self.assertFalse(consumer['inventory_updated'])

    def test_token_host_and_origin_authorization(self):
        self.assertEqual(self.request('GET', '/api/session', auth=False)[0], 200)
        self.assertEqual(self.request('GET', '/api/submissions/missing', auth=False)[0], 403)
        self.assertEqual(self.request('POST', '/api/submissions', {'text': 'x'}, auth=False)[0], 403)
        self.assertEqual(self.request('GET', '/api/session', headers={'Host': 'attacker.invalid'})[0], 403)
        self.assertEqual(self.request('GET', '/api/session', headers={'Origin': 'http://attacker.invalid'})[0], 403)
        self.assertEqual(self.request('GET', '/api/session', headers={'Origin': 'null'})[0], 403)
        self.assertEqual(self.request('GET', '/api/session', headers={'Origin': f'http://localhost:{self.server.server_port}'})[0], 200)
        self.assertEqual(self.request('GET', '/api/submissions/missing', headers={'Authorization': 'Bearer wrong'})[0], 403)
        self.assertEqual(self.request('GET', '/api/submissions/missing')[0], 404)

    def test_duplicate_nonfinite_json_rejected(self):
        for raw in [b'{"text":"a","text":"b"}', b'{"text":NaN}', b'{"text":Infinity}', b'{"text":-Infinity}', b'{"text":1e999}', b'{"text":"a","meta":{"x":1,"x":2}}']:
            with self.subTest(raw=raw):
                status, _ = self.request('POST', '/api/submissions', headers={'Idempotency-Key': 'bad-json'}, raw=raw)
                self.assertEqual(status, 400)
        for raw in ['1e999', '-1e999', '{"nested":[1e999]}']:
            with self.subTest(parser=raw):
                with self.assertRaises(ValueError):
                    strict_json(raw)
        self.assertEqual(self.predictor.calls, 0)

    def test_failed_inference_persists_and_replays_without_reexecution(self):
        self.predictor.fail = True
        status, body = self.submit()
        self.assertEqual(status, 201)
        result = body['result']
        self.assertEqual(result['state'], 'failed')
        self.assertEqual(result['error']['type'], 'RuntimeError')
        self.assertIn('controlled', result['error']['message'])
        self.assertEqual(self.request('GET', f'/api/submissions/{result["submission_id"]}')[1]['state'], 'failed')
        self.assertEqual(self.submit()[1]['result']['state'], 'failed')
        self.assertEqual(self.predictor.calls, 1)
        self.assertEqual(self.request('POST', f'/api/submissions/{result["submission_id"]}/extraction', fixture()[1])[0], 409)

    def test_restart_marks_interrupted_processing_as_failed(self):
        # Seed a crash checkpoint in a temporary DB; never interrupt a real worker.
        with self.server.store.db() as db:
            db.execute('INSERT INTO submissions VALUES (?,?,?,?,?,?)', ('interrupted', 'restart-key', 'fingerprint', 'processing', '{}', 'test-time'))
        recovered = make_server(0, self.database, FakePredictor())
        try:
            result = recovered.store.get('interrupted')
            self.assertEqual(result['state'], 'failed')
            self.assertEqual(result['error']['type'], 'Interrupted')
        finally:
            recovered.server_close()

    def test_invalid_image_inputs(self):
        for data in [
            {'image_base64': '!!!', 'filename': 'x.png'},
            {'image_base64': '', 'filename': 'x.png'},
            {'image_base64': 'YWJj', 'filename': 'x.exe'},
            {'image_base64': 'YWJj', 'filename': True},
        ]:
            with self.subTest(data=data):
                self.assertEqual(self.request('POST', '/api/submissions', data, {'Idempotency-Key': 'image-bad'})[0], 400)
        data = {'image_base64': base64.b64encode(b'not an actual png').decode(), 'filename': '../../x.png'}
        status, result = self.request('POST', '/api/submissions', data, {'Idempotency-Key': 'corrupt-image'})
        self.assertEqual(status, 201)
        self.assertEqual(result['result']['state'], 'failed')
        self.assertEqual(self.predictor.image_calls, 0)
        try:
            import PIL
        except ImportError:
            self.assertEqual(result['result']['error']['type'], 'ModuleNotFoundError')
        else:
            self.assertEqual(result['result']['error']['type'], 'UnidentifiedImageError')

    def test_malformed_http_json_and_metadata_return_client_errors(self):
        for raw, headers in [
            (b'{', {}),
            (b'{"text":"x"} trailing', {}),
            (b'\xff', {}),
            (b'', {}),
            (b'{"text":"x"}', {'Content-Type': 'text/plain'}),
            (b'{"text":"x"}', {'Content-Length': '-1'}),
            (b'{"text":"x"}', {'Content-Length': 'invalid'}),
            (b'[' * 2000 + b'0' + b']' * 2000, {}),
        ]:
            with self.subTest(length=len(raw), headers=headers):
                supplied = {'Idempotency-Key': 'malformed'}
                supplied.update(headers)
                status, body = self.request('POST', '/api/submissions', raw=raw, headers=supplied)
                self.assertEqual(status, 400)
                self.assertIn('error', body)
        self.assertEqual(self.predictor.calls, 0)

    def test_invalid_requests_do_not_create_records(self):
        for data in [{'text': ''}, {'text': True}, {'text': 'x', 'extra': 1}, [], {'text': 'x' * 200001}]:
            with self.subTest(kind=type(data).__name__):
                self.assertEqual(self.request('POST', '/api/submissions', data, {'Idempotency-Key': 'invalid'})[0], 400)
        self.assertEqual(self.request('POST', '/api/submissions', {'text': 'okay'})[0], 400)
        with self.server.store.db() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM submissions').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()


