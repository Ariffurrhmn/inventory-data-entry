"""Local annotation review portal. Python standard library only; no model execution."""
import argparse
import csv
import hashlib
import json
import mimetypes
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CLASSIFIER = ROOT / 'classifier/engine'
ANNOTATIONS = ROOT / 'Dataset/annotations'
LABELS = ['purchase_order', 'receipt', 'delivery_note', 'customer_copy']


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def read_csv(path):
    if not path.exists():
        return []
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Conflict(Exception):
    pass


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS revisions (sample_id TEXT NOT NULL, revision INTEGER NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(sample_id, revision))')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        try:
            db.execute('PRAGMA synchronous=FULL')
            with db:
                yield db
        finally:
            db.close()

    def latest(self, sample_id):
        with self.connect() as db:
            row = db.execute('SELECT payload FROM revisions WHERE sample_id=? ORDER BY revision DESC LIMIT 1', (sample_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def all_latest(self):
        with self.connect() as db:
            rows = db.execute('SELECT r.payload FROM revisions r JOIN (SELECT sample_id, MAX(revision) revision FROM revisions GROUP BY sample_id) m ON r.sample_id=m.sample_id AND r.revision=m.revision').fetchall()
        return {item['sample_id']: item for item in (json.loads(row[0]) for row in rows)}

    def history(self, sample_id):
        with self.connect() as db:
            rows = db.execute('SELECT payload FROM revisions WHERE sample_id=? ORDER BY revision DESC', (sample_id,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def save(self, sample_id, expected_revision, payload):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            current = db.execute('SELECT COALESCE(MAX(revision),0) FROM revisions WHERE sample_id=?', (sample_id,)).fetchone()[0]
            if current != expected_revision:
                raise Conflict('Another tab saved this document. Your edits are retained in this browser. Reload the saved record before merging them.')
            saved = dict(payload, sample_id=sample_id, revision=current + 1, saved_at=datetime.now(timezone.utc).isoformat())
            db.execute('INSERT INTO revisions VALUES (?,?,?)', (sample_id, current + 1, json.dumps(saved, ensure_ascii=False)))
        return saved


class Catalog:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.service = self.root / ('classifier/engine' if (self.root/'classifier/engine').is_dir() else 'services/document_classifier')
        self.service_relative = self.service.relative_to(self.root).as_posix()
        self.annotations = self.root / 'Dataset/annotations'
        self.version = self.annotations / 'versions/utf8-v2'
        self.rows = {}
        self.references = {p.stem: p for p in (self.version / 'transcriptions').glob('*.json')}
        legacy = {p.stem: p for p in (self.annotations / 'transcriptions').glob('*.json')}
        for sid, path in legacy.items():
            self.references.setdefault(sid, path)
        self.queues = {r['sample_id']: r for r in read_csv(self.version / 'review_queue.csv')}
        self.ocr = {}
        for folder, name in [
            (self.annotations / 'ocr_drafts', 'Initial OCR draft · PSM3'),
            (self.service / 'runs/text_preliminary/ocr', 'Experiment OCR · PSM3'),
            (self.service / 'runs/text_delivery_v2/ocr_sparse', 'Sparse OCR · PSM11'),
        ]:
            for path in folder.glob('*.json'):
                self.ocr.setdefault(path.stem, []).append((name, path))
        for row in read_csv(self.service / 'data/manifest.csv'):
            sid = row['sample_id']
            self.rows[sid] = dict(sample_id=sid, source_path=row.get('source_path', ''), image_path=self.service_relative+'/' + row['image_path'].replace('\\', '/'), label=row['label'], split='excluded', group_id=row.get('group_id', ''), included=row.get('include') == 'yes', source=row.get('source', 'original'))
        for row in read_csv(self.service / 'data/splits.csv'):
            if row['sample_id'] in self.rows:
                self.rows[row['sample_id']]['split'] = row['split']
        for row in read_csv(self.service / 'runs/text_preliminary/experiment_manifest.csv'):
            sid = row['sample_id']
            if sid not in self.rows:
                self.rows[sid] = dict(sample_id=sid, source_path=row['image_path'].replace('\\', '/'), image_path=row['image_path'].replace('\\', '/'), label=row['label'], split=row['split'], group_id=row.get('group_id', ''), included=row.get('include') == 'yes', source=row.get('source', 'intake'))
        # Expose cached OCR even if it has no corresponding manifest/reference entry.
        for sid in self.ocr.keys() - self.rows.keys():
            draft = read_json(self.ocr[sid][0][1])
            image = draft.get('image_path') or draft.get('prepared_image_path', '')
            if image.startswith('data/'):
                image = self.service_relative+'/' + image
            self.rows[sid] = dict(sample_id=sid, source_path=draft.get('source_path', image), image_path=image.replace('\\', '/'), label=draft.get('label', ''), split=draft.get('split', 'unassigned'), group_id='', included=False, source='orphan_ocr')

        active_path = self.annotations / 'scope/active.json'
        self.scope_version = None
        scope_rows = {}
        if active_path.exists():
            active = read_json(active_path)
            self.scope_version = active['version']
            scope_path = (self.root / active['manifest']).resolve()
            if not scope_path.is_relative_to((self.annotations / 'scope').resolve()):
                raise ValueError('Scope manifest must be within the annotation scope folder.')
            scope_rows = {r['sample_id']: r for r in read_csv(scope_path)}
        for sid, row in self.rows.items():
            scope = scope_rows.get(sid)
            row.update(scope_version=self.scope_version, scope_eligible=(scope['include'] == 'yes') if scope else (False if self.scope_version else None), scope_status=scope['scope_status'] if scope else 'unassessed', content_style=scope['content_style'] if scope else 'unassessed', scope_reason=scope['scope_reason'] if scope else 'Awaiting content-style screening.' if self.scope_version else '')

    def image_path(self, sid):
        row = self.rows[sid]
        if not row['image_path']:
            return None
        path = (self.root / row['image_path']).resolve()
        if not path.is_relative_to(self.root.resolve()) or not path.is_file():
            return None
        return path

    def listing(self, saved):
        result = []
        for sid, row in self.rows.items():
            review = saved.get(sid)
            result.append(dict(row, has_reference=sid in self.references, ocr_sources=len(self.ocr.get(sid, [])), flagged=sid in self.queues, human_status=review['status'] if review else 'unreviewed', human_verified=bool(review and review['human_verified']), revision=review['revision'] if review else 0, display_label=review['label'] if review else row['label']))
        return result

    def detail(self, sid, store):
        row = self.rows[sid]
        reference_path = self.references.get(sid)
        reference = read_json(reference_path) if reference_path else None
        drafts = []
        for name, path in self.ocr.get(sid, []):
            raw = read_json(path)
            drafts.append(dict(name=name, path=path.relative_to(self.root).as_posix(), text=raw.get('full_text', ''), status=raw.get('status', 'unreviewed'), policy=raw.get('policy'), sha256=digest(path)))
        return dict(record=row, reference=reference, reference_path=reference_path.relative_to(self.root).as_posix() if reference_path else None, reference_sha256=digest(reference_path) if reference_path else None, drafts=drafts, saved=store.latest(sid), history=store.history(sid), image_available=self.image_path(sid) is not None)


def validate_review(data, detail):
    if detail['record'].get('scope_eligible') is False:
        raise ValueError('Outside the printed working set. This record is available as read-only history.')
    if not isinstance(data, dict):
        raise ValueError('Expected a JSON object.')
    text = data.get('text')
    if not isinstance(text, str) or not text.strip() or len(text) > 200000:
        raise ValueError('Enter a transcription (maximum 200,000 characters).')
    if data.get('label') not in LABELS:
        raise ValueError('Choose one of the four document classes.')
    if data.get('status') not in ['draft', 'needs_review', 'verified']:
        raise ValueError('Choose a valid review status.')
    revision = data.get('expected_revision')
    if type(revision) is not int or revision < 0:
        raise ValueError('Invalid revision.')
    for name in ['reviewer', 'notes', 'uncertainties', 'text_source']:
        if not isinstance(data.get(name, ''), str) or len(data.get(name, '')) > 20000:
            raise ValueError('Invalid ' + name)
    reviewer_type = data.get('reviewer_type', 'human')
    if reviewer_type not in ['human', 'ai']:
        raise ValueError('Reviewer type must be human or ai.')
    verified = data['status'] == 'verified'
    if verified and reviewer_type == 'ai':
        raise ValueError('AI reviews cannot be marked human verified.')
    if verified and (data.get('verified_confirmation') is not True or not data.get('reviewer', '').strip()):
        raise ValueError('Verification requires your name and explicit confirmation that you checked the image, text and class.')
    row = detail['record']
    return dict(schema_version='1.0', reviewer_type=reviewer_type, scope_version=detail['record'].get('scope_version'), scope_status=detail['record'].get('scope_status'), text=text, lines=text.splitlines(), label=data['label'], original_label=row['label'], split=row['split'], status=data['status'], reviewer=data.get('reviewer', '').strip(), notes=data.get('notes', ''), uncertainties=data.get('uncertainties', ''), human_verified=verified, verified_confirmation=verified, text_source=data.get('text_source', 'manual'), reference_path=detail['reference_path'], reference_sha256=detail['reference_sha256'], image_path=row['image_path'], source_path=row['source_path'], image_sha256=digest(Path(detail['_image_path'])) if detail.get('_image_path') else None, application='local_annotation_portal')


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def json_response(self, value, status=200, filename=None):
        data = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        if filename:
            self.send_header('Content-Disposition', 'attachment; filename="' + filename + '"')
        self.end_headers()
        self.wfile.write(data)

    def valid_host(self):
        return self.headers.get('Host') in [f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}']

    def do_GET(self):
        if not self.valid_host():
            return self.json_response({'error': 'Use the local portal address.'}, 403)
        path = unquote(urlparse(self.path).path)
        app = self.server
        if path == '/api/catalog':
            rows = app.catalog.listing(app.store.all_latest())
            return self.json_response(dict(records=rows, labels=LABELS, token=app.token, storage='Dataset/annotations/human_review/reviews.sqlite3', reference_version='utf8-v2'))
        if path == '/api/export':
            saved = app.store.all_latest()
            records = [review for sid, review in saved.items() if sid in app.catalog.rows and app.catalog.rows[sid].get('scope_eligible') is not False]
            return self.json_response(dict(schema_version='1.0', scope_version=app.catalog.scope_version, exported_at=datetime.now(timezone.utc).isoformat(), records=records, withheld_out_of_scope=len(saved)-len(records), automatic_merge_into_training=False), filename='printed-reviews.json')
        if path == '/api/export-catalog':
            rows = [app.catalog.detail(sid, app.store) for sid in app.catalog.rows]
            return self.json_response(dict(schema_version='1.0', records=rows, automatic_merge_into_training=False), filename='annotation-catalog.json')
        if path.startswith('/api/record/'):
            sid = path.rsplit('/', 1)[-1]
            if sid not in app.catalog.rows:
                return self.json_response({'error': 'Unknown document.'}, 404)
            return self.json_response(app.catalog.detail(sid, app.store))
        if path.startswith('/image/'):
            sid = path.rsplit('/', 1)[-1]
            image = app.catalog.image_path(sid) if sid in app.catalog.rows else None
            if image:
                return self.file_response(image)
            return self.json_response({'error': 'No image available.'}, 404)
        assets = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css'}
        if path in assets:
            return self.file_response(HERE / assets[path])
        self.json_response({'error': 'Not found.'}, 404)

    def file_response(self, path):
        content = path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
        self.send_header('Content-Length', str(len(content)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        app = self.server
        origin = self.headers.get('Origin')
        if not self.valid_host() or self.headers.get('X-Review-Token') != app.token or (origin and origin not in [f'http://127.0.0.1:{app.server_port}', f'http://localhost:{app.server_port}']):
            return self.json_response({'error': 'Local session required. Reload the portal.'}, 403)
        path = unquote(urlparse(self.path).path)
        sid = path.rsplit('/', 1)[-1]
        if not path.startswith('/api/record/') or sid not in app.catalog.rows:
            return self.json_response({'error': 'Unknown document.'}, 404)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length <= 0 or length > 1000000:
                raise ValueError('Invalid request size.')
            data = json.loads(self.rfile.read(length))
            detail = app.catalog.detail(sid, app.store)
            detail['_image_path'] = app.catalog.image_path(sid)
            if data.get('status') == 'verified' and not detail['_image_path']:
                raise ValueError('An image is required to verify this record.')
            payload = validate_review(data, detail)
            saved = app.store.save(sid, data['expected_revision'], payload)
            self.json_response(saved)
        except Conflict as exc:
            self.json_response({'error': str(exc)}, 409)
        except (ValueError, TypeError, KeyError, UnicodeError) as exc:
            self.json_response({'error': str(exc)}, 400)
        except (OSError, sqlite3.Error):
            self.json_response({'error': 'Could not save to disk. Your browser draft is retained; check the server and try again.'}, 500)


def make_server(port=8765, database=None, catalog=None):
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.catalog = catalog or Catalog()
    server.store = Store(database or ANNOTATIONS / 'human_review/reviews.sqlite3')
    server.token = secrets.token_urlsafe(32)
    return server


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--database', type=Path, help='Alternate review database (for testing)')
    args = parser.parse_args()
    server = make_server(args.port, args.database)
    print(f'Annotation portal: http://127.0.0.1:{server.server_port}', flush=True)
    print(f'Review database: {server.store.path}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
