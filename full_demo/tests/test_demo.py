"""Tests for the end-to-end demo. Run from the project root:

    python -m unittest discover -s full_demo/tests -v

Most tests use a tiny fake predictor so they are fast and need no OCR. One test loads the
real selected classifier on text only (skipped if the model files are unavailable).
"""
import json, os, stat, sys, tempfile, threading, time, unittest, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEMO = HERE.parent
sys.path.insert(0, str(DEMO))

from extractor import RulesExtractor, CommandExtractor  # noqa: E402
from verify import verify  # noqa: E402
import server as srv  # noqa: E402

CLEAN = """Prime Foods Distributors
PURCHASE ORDER

Date: 2026-07-19 PO No: PO-84686

Item Qty Unit Price Line Total

Instant Noodles pack 18 20.00 360.00

Basmati Rice 5kg bag 28 650.00 18200.00
Grand Total: 18560.00
"""
WRONG_ROW = CLEAN.replace('360.00', '460.00')


class FakePredictor:
    model_hash = 'fake'

    def metadata(self):
        return {'run': 'fake', 'model': 'fake', 'model_sha256': 'fake'}

    def predict_text(self, text, origin='provided_text', heading_text=None):
        return dict(decision_trace={'selected_component': 'printed_heading'}, label='purchase_order', decision_source='printed_heading',
                    heading_evidence='purchase order', ambiguous_heading=False, statistical_label='purchase_order',
                    scores_kind='x', scores={'purchase_order': .9, 'receipt': .05, 'delivery_note': .03, 'customer_copy': .02},
                    scores_calibrated=False, ocr_empty=False, text_characters=len(text), input_origin=origin, ocr_text=text,
                    heading_ocr_text=None, validation_only=True, **self.metadata())


class ExtractorTests(unittest.TestCase):
    def test_reads_clean_document(self):
        rec = RulesExtractor().extract('purchase_order', CLEAN)
        self.assertEqual(rec['document_number'], 'PO-84686')
        self.assertEqual(rec['date'], '2026-07-19')
        self.assertEqual(rec['totals']['grand_total'], '18560.00')
        self.assertEqual([r['quantity'] for r in rec['line_items']], ['18', '28'])
        self.assertEqual(rec['line_items'][0]['raw_text'], 'Instant Noodles pack')

    def test_every_value_has_literal_evidence(self):
        rep = verify(RulesExtractor().extract('purchase_order', CLEAN), CLEAN)
        self.assertTrue(all(f['status'] == 'supported' for f in rep['evidence_findings']))

    def test_ambiguous_row_is_not_guessed(self):
        text = "Item Qty Price Total\nMiniket Rice 25kg 24 | Tk 1,850 1 Tk 44,400 1.\n"
        rec = RulesExtractor().extract('purchase_order', text)
        self.assertEqual(len(rec['line_items']), 1)
        row = rec['line_items'][0]
        self.assertIsNone(row['unit_price']); self.assertIsNone(row['line_total'])
        self.assertTrue(rec['uncertainties'])

    def test_never_uses_arithmetic_to_pick_values(self):
        rec = RulesExtractor().extract('purchase_order', WRONG_ROW)
        self.assertEqual(rec['line_items'][0]['line_total'], '460.00')  # printed value kept, not corrected


class VerifyTests(unittest.TestCase):
    def test_strict_flags_missing_subtotal(self):
        rep = verify(RulesExtractor().extract('purchase_order', CLEAN), CLEAN, 'literal', 'strict')
        self.assertTrue(rep['review_required'])
        self.assertIn('Arithmetic unavailable: subtotal', rep['review_reasons'])

    def test_demo_reconcile_passes_clean_document(self):
        rep = verify(RulesExtractor().extract('purchase_order', CLEAN), CLEAN, 'literal', 'demo_reconcile')
        self.assertFalse(rep['review_required'], rep['review_reasons'])
        self.assertTrue(any(c['id'] == 'grand_total_vs_line_sum' and c['status'] == 'passed' for c in rep['checks']))

    def test_both_policies_catch_wrong_row(self):
        for policy in ('strict', 'demo_reconcile'):
            rep = verify(RulesExtractor().extract('purchase_order', WRONG_ROW), WRONG_ROW, 'literal', policy)
            self.assertIn('Arithmetic mismatch: line_items/0/multiplication', rep['review_reasons'])

    def test_demo_reconcile_catches_total_that_disagrees_with_lines(self):
        text = CLEAN.replace('18560.00', '18999.00')
        rep = verify(RulesExtractor().extract('purchase_order', text), text, 'literal', 'demo_reconcile')
        self.assertIn('Arithmetic mismatch: grand_total_vs_line_sum', rep['review_reasons'])

    def test_demo_reconcile_requires_headers(self):
        text = CLEAN.replace('PO No: PO-84686', '')
        rep = verify(RulesExtractor().extract('purchase_order', text), text, 'literal', 'demo_reconcile')
        self.assertIn('Required header missing: document number', rep['review_reasons'])

    def test_missing_headers_do_not_trigger_in_strict(self):
        text = CLEAN.replace('PO No: PO-84686', '')
        rep = verify(RulesExtractor().extract('purchase_order', text), text, 'literal', 'strict')
        self.assertNotIn('Required header missing: document number', rep['review_reasons'])

    def test_unknown_policy_rejected(self):
        with self.assertRaises(ValueError):
            verify(RulesExtractor().extract('purchase_order', CLEAN), CLEAN, 'literal', 'lenient')

    def test_wrong_but_consistent_value_passes(self):
        # Documented limitation: arithmetic cannot see a consistently wrong item name.
        text = CLEAN.replace('Instant Noodles pack', 'Instant Noodles pacl')
        rep = verify(RulesExtractor().extract('purchase_order', text), text, 'literal', 'demo_reconcile')
        self.assertFalse(rep['review_required'])


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.server = srv.make_server(port=0, predictor=FakePredictor(), pin='424242', runtime=cls.tmp.name, policy='strict')
        cls.port = cls.server.server_port
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f'http://127.0.0.1:{cls.port}'
        cls.token = cls.call('/api/session')[1]['token']

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.tmp.cleanup()

    @classmethod
    def call(cls, path, method='GET', data=None, token=None, key=None, headers=None):
        h = {'Content-Type': 'application/json'}
        if token: h['Authorization'] = 'Bearer ' + token
        if key: h['Idempotency-Key'] = key
        h.update(headers or {})
        req = urllib.request.Request(cls.base + path, method=method, headers=h,
                                     data=None if data is None else json.dumps(data).encode())
        try:
            with urllib.request.urlopen(req) as r:
                body = r.read()
                return r.status, (json.loads(body) if r.headers.get_content_type() == 'application/json' else body)
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b'{}')

    def wait_done(self, key):
        for _ in range(100):
            _, v = self.call('/api/captures/' + key, token=self.token)
            if v['stage'] in ('done', 'failed'):
                return v
            time.sleep(.1)
        self.fail('capture did not finish')

    def test_api_needs_pairing(self):
        self.assertEqual(self.call('/api/info')[0], 401)
        self.assertEqual(self.call('/api/erp/inbox', token='nope')[0], 401)

    def test_pairing_wrong_and_right_code(self):
        self.assertEqual(self.call('/api/pair', 'POST', {'pin': '000000'})[0], 403)
        status, body = self.call('/api/pair', 'POST', {'pin': '424242', 'name': 'test phone'})
        self.assertEqual(status, 200)
        self.assertEqual(self.call('/api/info', token=body['token'])[0], 200)

    def test_pairing_is_rate_limited(self):
        tmp = tempfile.TemporaryDirectory()
        s2 = srv.make_server(port=0, predictor=FakePredictor(), pin='111111', runtime=tmp.name)
        threading.Thread(target=s2.serve_forever, daemon=True).start()
        base = f'http://127.0.0.1:{s2.server_port}'
        def pair(pin):
            req = urllib.request.Request(base + '/api/pair', method='POST', data=json.dumps({'pin': pin}).encode(), headers={'Content-Type': 'application/json'})
            try: return urllib.request.urlopen(req).status
            except urllib.error.HTTPError as e: return e.code
        for _ in range(5): self.assertEqual(pair('000000'), 403)
        self.assertEqual(pair('111111'), 403)  # locked out even with the right code
        s2.shutdown(); s2.server_close(); tmp.cleanup()

    def test_demo_starts_on_reconcile_policy_and_says_so(self):
        tmp = tempfile.TemporaryDirectory()
        s2 = srv.make_server(port=0, predictor=FakePredictor(), runtime=tmp.name)
        self.assertEqual(s2.demo.settings['policy'], 'demo_reconcile')
        s2.server_close(); tmp.cleanup()

    def test_session_refused_behind_a_proxy(self):
        status, _ = self.call('/api/session', headers={'X-Forwarded-For': '203.0.113.9'})
        self.assertEqual(status, 403)

    def test_text_capture_runs_full_pipeline(self):
        status, r = self.call('/api/captures', 'POST', {'text': CLEAN, 'source': 'test'}, self.token, key='t-full')
        self.assertEqual(status, 202)
        v = self.wait_done('t-full')
        self.assertEqual(v['stage'], 'done', v.get('error'))
        self.assertEqual(v['classification']['label'], 'purchase_order')
        self.assertEqual(v['extraction']['document_number'], 'PO-84686')
        self.assertTrue(v['verification']['review_required'])  # strict default
        self.assertFalse(v['extraction_human_verified'])
        inbox = self.call('/api/erp/inbox', token=self.token)[1]
        mine = [i for i in inbox if i['capture_key'] == 't-full']
        self.assertEqual(mine[0]['status'], 'blocked_for_review')
        self.assertFalse(mine[0]['inventory_updated'])

    def test_same_key_same_payload_replays(self):
        self.call('/api/captures', 'POST', {'text': CLEAN}, self.token, key='t-idem')
        self.wait_done('t-idem')
        status, r = self.call('/api/captures', 'POST', {'text': CLEAN}, self.token, key='t-idem')
        self.assertEqual((status, r['replayed']), (200, True))
        inbox = self.call('/api/erp/inbox', token=self.token)[1]
        self.assertEqual(len([i for i in inbox if i['capture_key'] == 't-idem']), 1)

    def test_same_key_different_payload_conflicts(self):
        self.call('/api/captures', 'POST', {'text': CLEAN}, self.token, key='t-conf')
        self.wait_done('t-conf')
        status, r = self.call('/api/captures', 'POST', {'text': WRONG_ROW}, self.token, key='t-conf')
        self.assertEqual(status, 409)

    def test_policy_setting_changes_verdict_and_erp_status(self):
        self.call('/api/captures', 'POST', {'text': CLEAN}, self.token, key='t-pol')
        self.wait_done('t-pol')
        try:
            self.call('/api/settings', 'POST', {'policy': 'demo_reconcile'}, self.token)
            v = self.call('/api/captures/t-pol', token=self.token)[1]
            self.assertFalse(v['verification']['review_required'], v['verification']['reasons'])
            row = [i for i in self.call('/api/erp/inbox', token=self.token)[1] if i['capture_key'] == 't-pol'][0]
            self.assertEqual(row['status'], 'eligible_for_external_review')
        finally:
            self.call('/api/settings', 'POST', {'policy': 'strict'}, self.token)

    def test_simulated_wrong_extraction_is_detected_and_not_stored(self):
        self.call('/api/captures', 'POST', {'text': CLEAN}, self.token, key='t-sim')
        self.wait_done('t-sim')
        s, r = self.call('/api/captures/t-sim/simulate', 'POST', {'mutation': 'inflate_quantity'}, self.token)
        self.assertEqual(s, 200)
        self.assertTrue(any('mismatch' in x.lower() for x in r['summary']['reasons']))
        v = self.call('/api/captures/t-sim', token=self.token)[1]
        self.assertEqual(v['extraction']['line_items'][0]['quantity'], '18')  # stored record untouched

    def test_reset_clears_demo_data_but_keeps_pairing(self):
        tmp = tempfile.TemporaryDirectory()
        s2 = srv.make_server(port=0, predictor=FakePredictor(), pin='777777', runtime=tmp.name)
        threading.Thread(target=s2.serve_forever, daemon=True).start()
        base = f'http://127.0.0.1:{s2.server_port}'
        def call(path, method='GET', data=None, token=None, key=None):
            h = {'Content-Type': 'application/json'}
            if token: h['Authorization'] = 'Bearer ' + token
            if key: h['Idempotency-Key'] = key
            req = urllib.request.Request(base + path, method=method, headers=h, data=None if data is None else json.dumps(data).encode())
            with urllib.request.urlopen(req) as r: return json.loads(r.read())
        token = call('/api/session')['token']
        call('/api/captures', 'POST', {'text': CLEAN}, token, key='r1')
        for _ in range(100):
            if call('/api/captures/r1', token=token)['stage'] == 'done': break
            time.sleep(.1)
        self.assertEqual(len(call('/api/erp/inbox', token=token)), 1)
        call('/api/reset', 'POST', {}, token)
        self.assertEqual(call('/api/erp/inbox', token=token), [])
        self.assertEqual(call('/api/feed', token=token), [])
        call('/api/captures', 'POST', {'text': CLEAN}, token, key='r1')  # same key is usable again
        s2.shutdown(); s2.server_close(); tmp.cleanup()

    def test_acknowledge(self):
        self.call('/api/captures', 'POST', {'text': CLEAN}, self.token, key='t-ack')
        v = self.wait_done('t-ack')
        s, r = self.call(f"/api/erp/{v['submission_id']}/acknowledge", 'POST', {}, self.token)
        self.assertEqual((s, r['inventory_updated']), (200, False))

    def test_bad_requests(self):
        self.assertEqual(self.call('/api/captures', 'POST', {'text': ''}, self.token, key='t-bad')[0], 400)
        self.assertEqual(self.call('/api/captures', 'POST', {'text': CLEAN}, self.token)[0], 400)  # no key
        self.assertEqual(self.call('/api/captures/missing', token=self.token)[0], 404)

    def test_static_files_do_not_escape_web_folder(self):
        status, _ = self.call('/..%2f..%2fREADME.md')
        self.assertEqual(status, 404)

    def test_pwa_assets_served(self):
        for path, mime in (('/m/', 'text/html'), ('/m/manifest.webmanifest', 'application/manifest+json'), ('/m/sw.js', 'text/javascript'), ('/reasons.js', 'text/javascript')):
            req = urllib.request.Request(self.base + path)
            with urllib.request.urlopen(req) as r:
                self.assertEqual(r.status, 200, path)
                self.assertEqual(r.headers.get_content_type(), mime, path)
        with urllib.request.urlopen(self.base + '/m/sw.js') as r:
            self.assertEqual(r.headers['Service-Worker-Allowed'], '/m/')

    def test_shelf_images_and_truth(self):
        shelf = self.call('/api/shelf', token=self.token)[1]
        self.assertEqual(len(shelf), 13)
        for item in shelf:
            self.assertTrue((DEMO / 'shelf' / item['image']).is_file(), item['image'])
        full = self.call('/api/shelf/purchase_order_03', token=self.token)[1]
        self.assertEqual(full['truth']['document_type'], 'purchase_order')


class CommandExtractorTests(unittest.TestCase):
    def test_external_command_result_goes_through_the_same_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / 'fake_llm.py'
            record = RulesExtractor().extract('purchase_order', CLEAN)
            record['totals']['grand_total'] = '99999.00'  # a hallucinated value with no support in the text
            script.write_text('import sys,json\nsys.stdin.read()\nprint("Sure! " + json.dumps(%r))\n' % record)
            ex = CommandExtractor([sys.executable, str(script)])
            got = ex.extract('purchase_order', CLEAN, prompt='x')
            rep = verify(got, CLEAN)
            self.assertTrue(any('/totals/grand_total' in r for r in rep['review_reasons']))

    def test_command_failure_is_reported(self):
        with self.assertRaises(RuntimeError):
            CommandExtractor([sys.executable, '-c', 'import sys; sys.exit(3)']).extract('receipt', 'x', prompt='x')


class RealModelTests(unittest.TestCase):
    def test_real_classifier_reads_heading_from_text(self):
        try:
            from inference import Predictor
            predictor = Predictor()
        except Exception as exc:  # model files or scikit-learn unavailable
            self.skipTest(str(exc))
        res = predictor.predict_text(CLEAN)
        self.assertEqual(res['label'], 'purchase_order')
        self.assertEqual(res['decision_source'], 'printed_heading')


if __name__ == '__main__':
    unittest.main()
