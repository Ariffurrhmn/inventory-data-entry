"""End-to-end demo server: phone PWA -> OCR -> classifier -> extraction -> verification -> ERP stand-in.

Standard library HTTP server. It reuses, unchanged:
  * classifier/engine  (the selected printed_v3_explainable model + Tesseract OCR)
  * services/document_pipeline/gateway.Store  (idempotent persisted submissions)
  * services/document_pipeline/contract.py    (evidence + arithmetic checks, via verify.py)

What is NOT real: the extraction step is a rule-based stand-in unless --extractor-cmd is
given, and the ERP is a stand-in inbox. See README.md "What is real and what is stand-in".
"""
import argparse, base64, copy, hashlib, json, mimetypes, secrets, socket, sys, threading, time, uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'services' / 'document_pipeline'))
sys.path.insert(0, str(ROOT / 'classifier' / 'engine'))

from gateway import Store, Conflict, digest, strict_json, extraction_prompt  # noqa: E402
from extractor import make_extractor  # noqa: E402
from verify import verify, summarize, POLICIES, NUMERIC_POLICIES  # noqa: E402

MAX_BODY = 30 * 1024 * 1024
IMAGE_SUFFIXES = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff', '.heic', '.heif'}
FORWARD_HEADERS = ('x-forwarded-for', 'x-forwarded-host', 'forwarded', 'via', 'cf-connecting-ip', 'x-real-ip')
STAGES = ['queued', 'reading_document', 'extracting', 'verifying', 'delivering', 'done']


def now():
    return datetime.now(timezone.utc).isoformat()


def lan_addresses():
    found = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        found.append(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith('127.') and ip not in found:
                found.append(ip)
    except OSError:
        pass
    return found


def qr_svg(text):
    try:
        import segno
    except ImportError:
        return None
    return segno.make(text, error='m').svg_inline(scale=5, border=2, dark='#111111', light='#ffffff')


def validate_payload(data):
    """Reject bad requests up front, before anything is registered or stored."""
    if not isinstance(data, dict):
        raise ValueError('Request must be an object.')
    if set(data) == {'text'}:
        if not isinstance(data['text'], str) or not data['text'].strip() or len(data['text']) > 200000:
            raise ValueError('Supply nonempty OCR text under 200000 characters.')
    elif set(data) == {'image_base64', 'filename'}:
        if not isinstance(data['filename'], str) or not isinstance(data['image_base64'], str):
            raise ValueError('Invalid image request.')
        if Path(data['filename']).suffix.lower() not in IMAGE_SUFFIXES:
            raise ValueError('Unsupported image format.')
        try:
            raw = base64.b64decode(data['image_base64'], validate=True)
        except Exception as exc:
            raise ValueError('Invalid base64 image.') from exc
        if not 0 < len(raw) <= 20 * 1024 * 1024:
            raise ValueError('Image must be nonempty and at most 20 MB.')
    else:
        raise ValueError('Supply exactly text, or image_base64 and filename.')


class Demo:
    """Application state shared by all requests."""

    def __init__(self, db_path, predictor, extractor, pin, port, lan, upload_dir, policy='demo_reconcile'):
        self.store = Store(db_path, predictor)
        self.predictor = predictor
        self.extractor = extractor
        self.pin = pin
        self.port = port
        self.lan = lan
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.session_token = secrets.token_urlsafe(24)
        self.settings = {'policy': policy, 'numeric': 'literal'}
        self.stage = {}
        self.inflight = set()
        self.lock = threading.Lock()
        self.pair_failures = []
        with self.store.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS devices (token TEXT PRIMARY KEY, name TEXT, created TEXT)')
            db.execute('''CREATE TABLE IF NOT EXISTS captures (
                key TEXT PRIMARY KEY, submission_id TEXT, source TEXT, filename TEXT, created TEXT,
                stage TEXT, error TEXT, backend TEXT, timings TEXT, replays INTEGER DEFAULT 0)''')
            db.execute('''CREATE TABLE IF NOT EXISTS erp_inbox (
                submission_id TEXT PRIMARY KEY, capture_key TEXT, received TEXT, acknowledged TEXT)''')
            for row in db.execute("SELECT key FROM captures WHERE stage NOT IN ('done','failed')").fetchall():
                db.execute("UPDATE captures SET stage='failed', error='Server restarted during processing; resend with a new key.' WHERE key=?", (row['key'],))

    # ---- auth -------------------------------------------------------------------------
    def valid_token(self, token):
        if not token:
            return False
        if secrets.compare_digest(token, self.session_token):
            return True
        with self.store.db() as db:
            return db.execute('SELECT 1 FROM devices WHERE token=?', (token,)).fetchone() is not None

    def pair(self, pin, name):
        cutoff = time.time() - 60
        self.pair_failures = [t for t in self.pair_failures if t > cutoff]
        if len(self.pair_failures) >= 5:
            raise PermissionError('Too many wrong codes. Wait a minute and try again.')
        if not isinstance(pin, str) or not secrets.compare_digest(pin.strip(), self.pin):
            self.pair_failures.append(time.time())
            raise PermissionError('Wrong pairing code.')
        token = secrets.token_urlsafe(24)
        with self.store.db() as db:
            db.execute('INSERT INTO devices VALUES (?,?,?)', (token, (name or 'phone')[:60], now()))
        return token

    # ---- capture pipeline -------------------------------------------------------------
    def capture_row(self, key):
        with self.store.db() as db:
            row = db.execute('SELECT * FROM captures WHERE key=?', (key,)).fetchone()
        return dict(row) if row else None

    def set_stage(self, key, stage, error=None, **extra):
        self.stage[key] = stage
        with self.store.db() as db:
            db.execute('UPDATE captures SET stage=?, error=COALESCE(?,error) WHERE key=?', (stage, error, key))
            if extra.get('timings') is not None:
                db.execute('UPDATE captures SET timings=? WHERE key=?', (json.dumps(extra['timings']), key))
            if extra.get('submission_id'):
                db.execute('UPDATE captures SET submission_id=? WHERE key=?', (extra['submission_id'], key))

    def start_capture(self, key, data, source):
        """Validate, enforce idempotency, then process in the background. Returns (status, replayed)."""
        if not isinstance(key, str) or not 1 <= len(key) <= 128:
            raise ValueError('Supply an Idempotency-Key of 1 to 128 characters.')
        validate_payload(data)
        fingerprint = digest(data)
        with self.lock:
            existing = self.capture_row(key)
            if existing:
                with self.store.db() as db:
                    row = db.execute('SELECT fingerprint FROM submissions WHERE idem=?', (key,)).fetchone()
                if row and row['fingerprint'] != fingerprint:
                    raise Conflict('This Idempotency-Key was already used for a different document.')
                with self.store.db() as db:
                    db.execute('UPDATE captures SET replays=replays+1 WHERE key=?', (key,))
                return 'replayed', True
            if key in self.inflight:
                return 'replayed', True
            filename = data.get('filename', 'pasted-text.txt')
            with self.store.db() as db:
                db.execute('INSERT INTO captures(key,source,filename,created,stage) VALUES (?,?,?,?,?)',
                           (key, source, filename, now(), 'queued'))
            if 'image_base64' in data:
                try:
                    raw = base64.b64decode(data['image_base64'], validate=True)
                except Exception as exc:
                    raise ValueError('Invalid base64 image.') from exc
                suffix = Path(filename).suffix.lower()
                if suffix in IMAGE_SUFFIXES:
                    (self.upload_dir / (hashlib.sha256(key.encode()).hexdigest()[:24] + suffix)).write_bytes(raw)
            self.inflight.add(key)
        threading.Thread(target=self.process, args=(key, data), daemon=True).start()
        return 'accepted', False

    def process(self, key, data):
        timings = {}
        try:
            t0 = time.time()
            self.set_stage(key, 'reading_document')
            result, _ = self.store.submit(key, data)
            sid = result['submission_id']
            self.set_stage(key, 'reading_document', submission_id=sid)
            timings['read_and_classify_s'] = round(time.time() - t0, 2)
            if result['state'] == 'failed':
                err = result.get('error', {}).get('message', 'Document could not be read.')
                self.set_stage(key, 'failed', error=err, timings=timings)
                return
            self.set_stage(key, 'extracting')
            t1 = time.time()
            cl = result['classification']
            record = self.extractor.extract(cl['label'], cl['ocr_text'], prompt=result['prompt'])
            timings['extract_s'] = round(time.time() - t1, 2)
            self.set_stage(key, 'verifying')
            t2 = time.time()
            self.store.attach(sid, record)
            timings['verify_s'] = round(time.time() - t2, 3)
            self.set_stage(key, 'delivering')
            with self.store.db() as db:
                db.execute('INSERT OR IGNORE INTO erp_inbox VALUES (?,?,?,NULL)', (sid, key, now()))
                db.execute('UPDATE captures SET backend=? WHERE key=?', (self.extractor.name, key))
            timings['total_s'] = round(time.time() - t0, 2)
            self.set_stage(key, 'done', timings=timings)
        except Exception as exc:  # recorded, never silently dropped
            self.set_stage(key, 'failed', error=f'{type(exc).__name__}: {exc}', timings=timings)
        finally:
            self.inflight.discard(key)

    # ---- views ------------------------------------------------------------------------
    def verification_for(self, submission, policy=None, numeric=None):
        policy = policy or self.settings['policy']
        numeric = numeric or self.settings['numeric']
        record = submission['verification']['record']
        ocr = submission.get('extraction_source', {}).get('ocr_text', submission['classification']['ocr_text'])
        return verify(record, ocr, numeric, policy)

    def capture_view(self, key, policy=None, numeric=None, full=True):
        cap = self.capture_row(key)
        if not cap:
            raise KeyError('Capture not found')
        out = {'key': key, 'stage': cap['stage'], 'error': cap['error'], 'source': cap['source'],
               'filename': cap['filename'], 'created': cap['created'], 'replays': cap['replays'] or 0,
               'timings': json.loads(cap['timings']) if cap['timings'] else {}, 'submission_id': cap['submission_id'],
               'extractor': cap['backend'], 'settings': dict(self.settings)}
        out['has_image'] = self.image_path(key) is not None
        if cap['submission_id']:
            sub = self.store.get(cap['submission_id'])
            out['state'] = sub['state']
            cl = sub.get('classification')
            if cl:
                trace = cl['decision_trace']
                out['classification'] = {
                    'label': cl['label'], 'decision_source': cl['decision_source'],
                    'heading_evidence': cl['heading_evidence'], 'scores': cl['scores'],
                    'statistical_label': cl['statistical_label'], 'scores_calibrated': False,
                    'trace': trace, 'model_run': cl['run'], 'model_sha256': cl['model_sha256'],
                    'ocr_text': cl['ocr_text'] if full else None}
            if sub['state'] == 'completed':
                report = self.verification_for(sub, policy, numeric)
                out['extraction'] = report['record']
                out['verification'] = summarize(report)
                out['verification']['checks'] = report['checks']
                out['verification']['evidence'] = report['evidence_findings']
                out['verification']['policy_notes'] = report['policy_notes']
                out['verification']['limitations'] = report['limitations']
                out['extraction_human_verified'] = False
                out['extraction_provenance'] = sub.get('extraction_provenance')
        return out

    def image_path(self, key):
        stem = hashlib.sha256(key.encode()).hexdigest()[:24]
        for suffix in IMAGE_SUFFIXES:
            p = self.upload_dir / (stem + suffix)
            if p.exists():
                return p
        return None

    def feed(self, limit=30):
        with self.store.db() as db:
            rows = db.execute('SELECT key FROM captures ORDER BY created DESC LIMIT ?', (limit,)).fetchall()
        out = []
        for r in rows:
            v = self.capture_view(r['key'], full=False)
            out.append({k: v.get(k) for k in ('key', 'stage', 'error', 'source', 'filename', 'created', 'timings', 'replays', 'has_image', 'submission_id')}
                       | {'label': (v.get('classification') or {}).get('label'),
                          'review_required': (v.get('verification') or {}).get('review_required'),
                          'document_number': (v.get('extraction') or {}).get('document_number')})
        return out

    def erp_inbox(self):
        with self.store.db() as db:
            rows = db.execute('SELECT * FROM erp_inbox ORDER BY received DESC').fetchall()
        items = []
        for r in rows:
            sub = self.store.get(r['submission_id'])
            report = self.verification_for(sub)
            rec = report['record']
            status = 'blocked_for_review' if report['review_required'] else 'eligible_for_external_review'
            items.append({'submission_id': r['submission_id'], 'capture_key': r['capture_key'], 'received': r['received'],
                          'acknowledged': r['acknowledged'], 'document_type': rec['document_type'],
                          'document_number': rec['document_number'], 'date': rec['date'],
                          'grand_total': rec['totals']['grand_total'], 'line_count': len(rec['line_items']),
                          'status': status, 'review_reasons': report['review_reasons'],
                          'inventory_updated': False})
        return items

    def acknowledge(self, sid):
        with self.store.db() as db:
            cur = db.execute('UPDATE erp_inbox SET acknowledged=? WHERE submission_id=? AND acknowledged IS NULL', (now(), sid))
            if cur.rowcount == 0 and not db.execute('SELECT 1 FROM erp_inbox WHERE submission_id=?', (sid,)).fetchone():
                raise KeyError('Not in ERP inbox')
        return {'submission_id': sid, 'acknowledged': True, 'inventory_updated': False}

    def simulate(self, key, mutation):
        """Apply a deliberate wrong extraction to a completed capture and verify it. Nothing is stored."""
        cap = self.capture_row(key)
        sub = self.store.get(cap['submission_id'])
        if sub['state'] != 'completed':
            raise Conflict('Extraction is not complete.')
        ocr = sub.get('extraction_source', {}).get('ocr_text', sub['classification']['ocr_text'])
        record = copy.deepcopy(sub['verification']['record'])
        rows = record['line_items']
        if mutation == 'inflate_quantity':
            idx = next((i for i, r in enumerate(rows) if r['quantity'] and r['unit_price']), None)
            if idx is None:
                raise ValueError('This document has no row with a quantity and unit price to alter.')
            rows[idx]['quantity'] = str(int(float(rows[idx]['quantity'])) * 10)
            what = f"Changed line {idx + 1} quantity from {sub['verification']['record']['line_items'][idx]['quantity']} to {rows[idx]['quantity']} but kept the original evidence."
        elif mutation == 'wrong_total':
            if record['totals']['grand_total'] is None:
                raise ValueError('This document has no grand total to alter.')
            old = record['totals']['grand_total']
            record['totals']['grand_total'] = str(int(float(old)) + 100)
            what = f'Changed the grand total from {old} to {record["totals"]["grand_total"]}.'
        elif mutation == 'invented_row':
            rows.append({'raw_text': 'Premium Basmati Rice 25kg', 'quantity': '5', 'unit_price': '1200', 'line_total': '6000'})
            idx = len(rows) - 1
            for k in ('raw_text', 'quantity', 'unit_price', 'line_total'):
                record['evidence'][f'/line_items/{idx}/{k}'] = {'raw_text': 'Premium Basmati Rice 25kg', 'quantity': '5', 'unit_price': '1200', 'line_total': '6000'}[k]
            what = 'Added a line item that is not in the document, with made-up evidence quotes.'
        else:
            raise ValueError('Unknown simulation.')
        report = verify(record, ocr, self.settings['numeric'], self.settings['policy'])
        return {'mutation': mutation, 'what_changed': what, 'caught': report['review_required'],
                'summary': summarize(report), 'checks': report['checks'], 'evidence': report['evidence_findings'],
                'note': 'Simulation only. This wrong record is not stored and nothing was sent to the ERP.'}

    def reset(self):
        """Clear demo submissions, ERP inbox and stored photos. Paired phones stay paired."""
        with self.lock:
            if self.inflight:
                raise Conflict('A document is still being processed; wait a moment and try again.')
            with self.store.db() as db:
                for table in ('erp_inbox', 'captures', 'attempts', 'submissions'):
                    db.execute(f'DELETE FROM {table}')
            for p in self.upload_dir.iterdir():
                if p.is_file():
                    p.unlink()
            self.stage.clear()
        return {'reset': True}

    def info(self):
        meta = self.predictor.metadata()
        evaluation = None
        ev_path = HERE / 'data' / 'evaluation.json'
        if ev_path.exists():
            evaluation = json.loads(ev_path.read_text())
            evaluation.pop('documents_detail', None)
        showcase = None
        sp = ROOT / 'supervisor_showcase' / 'data' / 'showcase.json'
        if sp.exists():
            sc = json.loads(sp.read_text(encoding='utf-8-sig'))
            showcase = {k: sc.get(k) for k in ('headline', 'gaps', 'classes', 'rejected', 'journey')}
        return {'model': meta, 'extractor': {'name': self.extractor.name, 'description': self.extractor.description},
                'settings': dict(self.settings), 'policies': list(POLICIES), 'numeric_policies': list(NUMERIC_POLICIES),
                'evaluation_synthetic': evaluation, 'classifier_evidence': showcase, 'llm_available': self.extractor.name == 'external-command'}


class Handler(BaseHTTPRequestHandler):
    server_version = 'InventoryDemo/1.0'

    def log_message(self, *_):
        pass

    @property
    def demo(self):
        return self.server.demo

    def send(self, value, status=200, mime='application/json', headers=None):
        data = json.dumps(value, ensure_ascii=False).encode() if mime == 'application/json' else value
        self.send_response(status)
        self.send_header('Content-Type', mime + ('; charset=utf-8' if mime.startswith('text') or mime == 'application/json' else ''))
        self.send_header('Content-Length', str(len(data)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def local_direct(self):
        port = self.server.server_port
        host_ok = self.headers.get('Host') in {f'127.0.0.1:{port}', f'localhost:{port}'}
        forwarded = any(self.headers.get(h) for h in FORWARD_HEADERS)
        return host_ok and not forwarded and self.client_address[0] in ('127.0.0.1', '::1')

    def token_ok(self, query):
        auth = self.headers.get('Authorization', '')
        token = auth[7:] if auth.startswith('Bearer ') else None
        if token is None and query.get('token'):
            token = query['token'][0]
        return self.demo.valid_token(token)

    # ---- static -----------------------------------------------------------------------
    def serve_file(self, base, rel, extra=None):
        base = base.resolve()
        target = (base / rel).resolve()
        if not target.is_relative_to(base) or not target.is_file():
            return self.send({'error': 'Not found.'}, 404)
        mime = mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
        if target.suffix == '.webmanifest':
            mime = 'application/manifest+json'
        if target.suffix == '.js':
            mime = 'text/javascript'
        return self.send(target.read_bytes(), mime=mime, headers=extra)

    def do_GET(self):
        url = urlparse(self.path)
        path, query = url.path, parse_qs(url.query)
        try:
            if path == '/api/health':
                return self.send({'ok': True, 'time': now()})
            if path == '/api/session':
                if not self.local_direct():
                    return self.send({'error': 'The dashboard session is only available on this computer.'}, 403)
                addrs = lan_addresses() if self.demo.lan else []
                urls = [f'http://{a}:{self.demo.port}/m/' for a in addrs]
                return self.send({'token': self.demo.session_token, 'pin': self.demo.pin, 'lan': self.demo.lan,
                                  'phone_urls': urls, 'phone_url_local': f'http://127.0.0.1:{self.demo.port}/m/',
                                  'qr_svg': qr_svg(urls[0] + '?pair=' + self.demo.pin) if urls else None})
            if path.startswith('/api/'):
                if not self.token_ok(query):
                    return self.send({'error': 'Pair this device first.'}, 401)
                return self.api_get(path, query)
            # static
            if path == '/':
                return self.serve_file(HERE / 'web', 'index.html')
            if path == '/m':
                return self.send(b'', 301, headers={'Location': '/m/'})
            if path == '/m/sw.js':
                return self.serve_file(HERE / 'web' / 'm', 'sw.js', {'Service-Worker-Allowed': '/m/', 'Cache-Control': 'no-cache'})
            if path.startswith('/m/'):
                return self.serve_file(HERE / 'web' / 'm', path[3:] or 'index.html')
            if path.startswith('/shelf/'):
                return self.serve_file(HERE / 'shelf', path[7:])
            return self.serve_file(HERE / 'web', path.lstrip('/'))
        except KeyError as exc:
            return self.send({'error': str(exc).strip("'\"")}, 404)
        except Conflict as exc:
            return self.send({'error': str(exc)}, 409)
        except ValueError as exc:
            return self.send({'error': str(exc)}, 400)

    def api_get(self, path, query):
        d = self.demo
        bits = path.strip('/').split('/')
        policy = query.get('policy', [None])[0]
        numeric = query.get('numeric', [None])[0]
        if path == '/api/info':
            return self.send(d.info())
        if path == '/api/shelf':
            shelf = json.loads((HERE / 'shelf' / 'shelf.json').read_text())
            return self.send([{k: v for k, v in item.items() if k != 'truth'} | {'has_truth': item['truth'] is not None} for item in shelf])
        if bits[:2] == ['api', 'shelf'] and len(bits) == 3:
            shelf = {i['id']: i for i in json.loads((HERE / 'shelf' / 'shelf.json').read_text())}
            if bits[2] not in shelf:
                raise KeyError('Shelf document not found')
            return self.send(shelf[bits[2]])
        if path == '/api/feed':
            return self.send(d.feed())
        if path == '/api/settings':
            return self.send(d.settings)
        if path == '/api/erp/inbox':
            return self.send(d.erp_inbox())
        if bits[:2] == ['api', 'captures'] and len(bits) == 3:
            return self.send(d.capture_view(bits[2], policy, numeric))
        if bits[:2] == ['api', 'captures'] and len(bits) == 4 and bits[3] == 'image':
            p = d.image_path(bits[2])
            if not p:
                raise KeyError('No stored image for this capture')
            return self.send(p.read_bytes(), mime=mimetypes.guess_type(p.name)[0] or 'image/jpeg')
        raise KeyError('Not found')

    def do_POST(self):
        url = urlparse(self.path)
        path, query = url.path, parse_qs(url.query)
        d = self.demo
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 <= length <= MAX_BODY:
                raise ValueError('Request size invalid.')
            raw = self.rfile.read(length) if length else b'{}'
            if self.headers.get_content_type() != 'application/json':
                raise ValueError('Use application/json.')
            data = strict_json(raw)
            if path == '/api/pair':
                try:
                    token = d.pair(data.get('pin'), data.get('name'))
                except PermissionError as exc:
                    return self.send({'error': str(exc)}, 403)
                return self.send({'token': token})
            if not self.token_ok(query):
                return self.send({'error': 'Pair this device first.'}, 401)
            bits = path.strip('/').split('/')
            if path == '/api/captures':
                key = self.headers.get('Idempotency-Key')
                source = str(data.pop('source', 'unknown'))[:40]
                status, replay = d.start_capture(key, data, source)
                return self.send({'key': key, 'status': status, 'replayed': replay}, 200 if replay else 202)
            if path == '/api/reset':
                return self.send(d.reset())
            if path == '/api/settings':
                if data.get('policy') in POLICIES:
                    d.settings['policy'] = data['policy']
                if data.get('numeric') in NUMERIC_POLICIES:
                    d.settings['numeric'] = data['numeric']
                return self.send(d.settings)
            if bits[:2] == ['api', 'shelf'] and len(bits) == 4 and bits[3] == 'send':
                shelf = {i['id']: i for i in json.loads((HERE / 'shelf' / 'shelf.json').read_text())}
                if bits[2] not in shelf:
                    raise KeyError('Shelf document not found')
                item = shelf[bits[2]]
                key = data.get('key') or f'shelf-{bits[2]}-{uuid.uuid4().hex[:8]}'
                payload = {'image_base64': base64.b64encode((HERE / 'shelf' / item['image']).read_bytes()).decode(), 'filename': item['image']}
                status, replay = d.start_capture(key, payload, 'dashboard-shelf')
                return self.send({'key': key, 'status': status, 'replayed': replay}, 200 if replay else 202)
            if bits[:2] == ['api', 'captures'] and len(bits) == 4 and bits[3] == 'simulate':
                return self.send(d.simulate(bits[2], data.get('mutation')))
            if bits[:2] == ['api', 'erp'] and len(bits) == 4 and bits[3] == 'acknowledge':
                return self.send(d.acknowledge(bits[2]))
            raise KeyError('Not found')
        except KeyError as exc:
            return self.send({'error': str(exc).strip("'\"")}, 404)
        except Conflict as exc:
            return self.send({'error': str(exc)}, 409)
        except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
            return self.send({'error': str(exc)}, 400)


def make_server(port=8790, host='127.0.0.1', db_path=None, predictor=None, extractor=None, pin=None, lan=False, runtime=None, policy='demo_reconcile'):
    runtime = Path(runtime or HERE / '.runtime')
    runtime.mkdir(parents=True, exist_ok=True)
    if predictor is None:
        from inference import Predictor
        predictor = Predictor()
    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    server.demo = Demo(db_path or runtime / 'demo.sqlite3', predictor, extractor or make_extractor(),
                       pin or f'{secrets.randbelow(10**6):06d}', server.server_port, lan, runtime / 'uploads', policy)
    return server


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--port', type=int, default=8790)
    ap.add_argument('--lan', action='store_true', help='Listen on all interfaces so a phone on the same Wi-Fi can connect (pairing code required).')
    ap.add_argument('--extractor-cmd', help='External command that reads the extraction prompt on stdin and prints one JSON object (for example a local LLM CLI).')
    ap.add_argument('--pin', help='Pairing code (default: random 6 digits).')
    ap.add_argument('--policy', choices=POLICIES, default='demo_reconcile', help='Starting verification policy. strict = project contract; demo_reconcile = reconcile a lone grand total with the line sum (assumes no tax/discount). Switchable live in the dashboard.')
    ap.add_argument('--runtime', help='Folder for the demo database and uploaded photos (default full_demo/.runtime).')
    args = ap.parse_args()
    server = make_server(args.port, '0.0.0.0' if args.lan else '127.0.0.1', extractor=make_extractor(args.extractor_cmd),
                         pin=args.pin, lan=args.lan, runtime=args.runtime, policy=args.policy)
    d = server.demo
    print('Dashboard (this computer):  http://127.0.0.1:%d/' % d.port)
    print('Pairing code for phones:    %s' % d.pin)
    if args.lan:
        for a in lan_addresses():
            print('Phone PWA on the same Wi-Fi: http://%s:%d/m/' % (a, d.port))
    else:
        print('Phone access is off. Restart with --lan to let a phone on the same Wi-Fi connect.')
    print('Extractor: %s   Verification policy: %s' % (d.extractor.name, d.settings['policy']), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
