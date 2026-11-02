"""Supervisor Showcase server.

Serves the presentation web app and wraps the selected classifier in
classifier/engine. Nothing is copied or retrained here: recorded results are
read from the selected run, live results come from the same saved model.
Standard library HTTP server, bound to 127.0.0.1 only.
"""
import argparse
import base64
import binascii
import csv
import io
import json
import mimetypes
import re
import secrets
import sys
import tempfile
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
ENGINE = PROJECT / 'classifier' / 'engine'
WEB = HERE / 'web'
NOTES = HERE / 'meeting-notes'
APP_ID = 'supervisor-showcase-v1'
CLASSES = ['purchase_order', 'receipt', 'delivery_note', 'customer_copy']
IMAGE_TYPES = ['.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif', '.tif', '.tiff', '.bmp']

sys.path.insert(0, str(ENGINE))
from PIL import Image, ImageOps, UnidentifiedImageError  # noqa: E402

SOURCE_NAMES = {
    'curated': 'Curated development document',
    'printed_synthetic_photo': 'Phone photo of a printed synthetic document',
    'expressexpense_srd': 'ExpressExpense public receipt photo',
    'company_documents_v2': 'Company Documents v2 (synthetic)',
}


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def jpeg(path, longest):
    with Image.open(path) as raw:
        if raw.width * raw.height > 25_000_000:
            raise ValueError('Choose an image under 25 megapixels.')
        image = ImageOps.exif_transpose(raw).convert('RGB')
        image.thumbnail((longest, longest))
        out = io.BytesIO()
        image.save(out, format='JPEG', quality=84)
    return out.getvalue()


def load_catalog():
    """Build the 25-document validation gallery from the selected run's saved evidence."""
    active = read_json(ENGINE / 'active_text_model.json')
    run = ENGINE / 'runs' / active['run']
    completion = read_json(run / 'completion.json')
    manifest = {}
    with open(run / 'split_manifest.csv', encoding='utf-8-sig', newline='') as handle:
        for row in csv.DictReader(handle):
            manifest[row['sample_id']] = row
    gallery = []
    with open(run / 'validation_predictions.csv', encoding='utf-8-sig', newline='') as handle:
        for row in csv.DictReader(handle):
            sid = row['sample_id']
            meta = manifest.get(sid, {})
            image = ENGINE / 'data' / 'images' / f'{sid}.jpg'
            saved = read_json(run / 'explanations' / f'{sid}.json')
            gallery.append(dict(
                id=sid,
                actual=row['actual'],
                predicted=row['predicted'],
                correct=row['correct'] == 'True',
                decision_source=saved['result']['decision_source'],
                evidence=row['evidence'] or None,
                rule_kind=row['rule_kind'] or None,
                source=meta.get('source', ''),
                source_label=SOURCE_NAMES.get(meta.get('source', ''), meta.get('source', 'Unknown')),
                group=meta.get('development_group', ''),
                has_image=image.exists(),
            ))
    return active, run, completion, gallery


class Handler(BaseHTTPRequestHandler):
    server_version = 'SupervisorShowcase/1'

    def log_message(self, *args):
        pass

    # ---- helpers -------------------------------------------------------
    def send(self, data, status=200, mime='application/json', cache=False):
        raw = json.dumps(data, ensure_ascii=False).encode() if mime == 'application/json' else data
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'max-age=3600' if cache else 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        try:
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            pass

    def local(self):
        port = self.server.server_port
        return self.headers.get('Host') in (f'127.0.0.1:{port}', f'localhost:{port}')

    def body(self, limit=32 * 1024 * 1024):
        length = int(self.headers.get('Content-Length', 0))
        if not 0 < length <= limit:
            raise ValueError('Request is empty or too large (20 MB image limit).')
        data = json.loads(self.rfile.read(length))
        if not isinstance(data, dict):
            raise ValueError('Invalid request.')
        return data

    def predictor(self):
        if self.server.predictor is None:
            if self.server.load_error:
                raise RuntimeError('Live classifier failed to load: ' + self.server.load_error)
            raise LookupError('The live classifier is still loading. Try again in a few seconds.')
        return self.server.predictor

    def analyse(self, image_path=None, text=None, name=''):
        from explain import explain_prediction
        predictor = self.predictor()
        start = time.perf_counter()
        with self.server.inference_lock:
            result = predictor.predict_text(text) if text is not None else predictor.predict_image(image_path)
            explanation = explain_prediction(predictor, result['ocr_text'], heading_text=result.get('heading_ocr_text'), result=result)
        return dict(mode='live', name=name, result=result, explanation=explanation,
                    elapsed_seconds=round(time.perf_counter() - start, 2))

    # ---- GET -----------------------------------------------------------
    def do_GET(self):
        if not self.local():
            return self.send({'error': 'Open the showcase at its local address.'}, 403)
        url = urlparse(self.path)
        path = url.path
        s = self.server
        if path == '/api/info':
            return self.send(dict(
                app_id=APP_ID, app_root=str(HERE), token=s.token,
                model=dict(run=s.active['run'], backend=s.active['backend'], model_sha256=s.active['model_sha256'],
                           scope=s.active.get('scope_version')),
                live_ready=s.predictor is not None, live_error=s.load_error,
                tesseract=s.tesseract, evaluation=dict(validation=s.completion['validation'], training_oof=s.completion['training_oof']),
                classes=CLASSES))
        if path == '/api/showcase':
            return self.send(read_json(HERE / 'data' / 'showcase.json'))
        if path == '/api/gallery':
            return self.send(s.gallery)
        match = re.fullmatch(r'/api/gallery/([0-9a-f]{12})(/image)?', path)
        if match:
            sid = match.group(1)
            if sid not in s.gallery_map:
                return self.send({'error': 'Document not found.'}, 404)
            if match.group(2):
                size = parse_qs(url.query).get('size', ['full'])[0]
                key = (sid, size)
                if key not in s.image_cache:
                    s.image_cache[key] = jpeg(ENGINE / 'data' / 'images' / f'{sid}.jpg', 420 if size == 'thumb' else 1600)
                return self.send(s.image_cache[key], mime='image/jpeg', cache=True)
            saved = read_json(s.run / 'explanations' / f'{sid}.json')
            return self.send(dict(mode='recorded', name=sid, item=s.gallery_map[sid],
                                  result=saved['result'], explanation=saved['explanation']))
        if path == '/api/notes':
            return self.send(self.list_notes())
        if path == '/':
            path = '/index.html'
        target = (WEB / path.lstrip('/')).resolve()
        if WEB in target.parents and target.is_file():
            mime = mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
            if target.suffix == '.js':
                mime = 'text/javascript'
            return self.send(target.read_bytes(), mime=mime)
        return self.send({'error': 'Not found'}, 404)

    def list_notes(self):
        notes = []
        for file in sorted(NOTES.glob('*.json'), reverse=True)[:20]:
            try:
                data = read_json(file)
                notes.append(dict(file=file.name, saved_at=data.get('saved_at'), meeting_date=data.get('meeting_date'),
                                  supervisor=data.get('supervisor'), summary=data.get('summary', [])))
            except (OSError, ValueError):
                continue
        return notes

    # ---- POST ----------------------------------------------------------
    def do_POST(self):
        port = self.server.server_port
        origin = self.headers.get('Origin')
        allowed = (f'http://127.0.0.1:{port}', f'http://localhost:{port}')
        if not self.local() or self.headers.get('X-Showcase-Token') != self.server.token or (origin and origin not in allowed):
            return self.send({'error': 'Session expired. Reload the page.'}, 403)
        path = urlparse(self.path).path
        try:
            match = re.fullmatch(r'/api/gallery/([0-9a-f]{12})/live', path)
            if match:
                sid = match.group(1)
                if sid not in self.server.gallery_map:
                    return self.send({'error': 'Document not found.'}, 404)
                return self.send(self.analyse(image_path=ENGINE / 'data' / 'images' / f'{sid}.jpg', name=sid))
            if path == '/api/analyze':
                data = self.body()
                if 'text' in data:
                    text = data['text']
                    if not isinstance(text, str) or not text.strip() or len(text) > 200_000:
                        raise ValueError('Paste between 1 and 200,000 characters of OCR text.')
                    return self.send(self.analyse(text=text, name='Pasted text'))
                name = Path(str(data.get('filename', ''))).name
                suffix = Path(name).suffix.lower()
                if suffix not in IMAGE_TYPES:
                    raise ValueError('Choose a JPEG, PNG, WebP, HEIC, TIFF or BMP image.')
                raw = base64.b64decode(str(data.get('image_base64', '')), validate=True)
                if not 0 < len(raw) <= 20 * 1024 * 1024:
                    raise ValueError('Choose a non-empty image smaller than 20 MB.')
                if suffix in ('.heic', '.heif'):
                    try:
                        from pillow_heif import register_heif_opener
                    except ImportError:
                        raise ValueError('HEIC support is not installed on this PC. Convert the photo to JPEG first.')
                    register_heif_opener()
                with tempfile.TemporaryDirectory(prefix='showcase-') as folder:
                    image = Path(folder) / ('upload' + suffix)
                    image.write_bytes(raw)
                    with Image.open(image) as check:
                        check.verify()
                    preview = 'data:image/jpeg;base64,' + base64.b64encode(jpeg(image, 1600)).decode()
                    report = self.analyse(image_path=image, name=name)
                report['preview'] = preview
                return self.send(report)
            if path == '/api/notes':
                return self.send(self.save_notes(self.body(limit=512 * 1024)))
            return self.send({'error': 'Not found'}, 404)
        except LookupError as error:
            return self.send({'error': str(error)}, 503)
        except (ValueError, TypeError, KeyError, binascii.Error, UnidentifiedImageError, Image.DecompressionBombError) as error:
            return self.send({'error': str(error)}, 400)
        except Exception as error:  # keep the meeting going; details go to the log
            print(f'{type(error).__name__}: {error}', flush=True)
            return self.send({'error': 'Analysis failed. Try a clearer printed image.'}, 500)

    def save_notes(self, data):
        markdown = data.get('markdown')
        if not isinstance(markdown, str) or not markdown.strip():
            raise ValueError('Nothing to save yet.')
        NOTES.mkdir(exist_ok=True)
        stamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        record = dict(saved_at=datetime.now().isoformat(timespec='seconds'), **{k: data.get(k) for k in
                      ('meeting_date', 'supervisor', 'presenters', 'decisions', 'feedback', 'summary')})
        with open(NOTES / f'{stamp}.json', 'x', encoding='utf-8') as handle:
            json.dump(record, handle, ensure_ascii=False, indent=2)
        with open(NOTES / f'{stamp}.md', 'x', encoding='utf-8') as handle:
            handle.write(markdown)
        return dict(file=f'{stamp}.md', folder='supervisor_showcase/meeting-notes')


def tesseract_available():
    import shutil
    return shutil.which('tesseract') is not None


def make_server(port=8780, load_live=True):
    active, run, completion, gallery = load_catalog()
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.active, server.run, server.completion = active, run, completion
    server.gallery, server.gallery_map = gallery, {g['id']: g for g in gallery}
    server.token = secrets.token_urlsafe(32)
    server.inference_lock = threading.Lock()
    server.image_cache = {}
    server.predictor, server.load_error = None, None
    server.tesseract = tesseract_available()

    def load():
        try:
            from inference import Predictor
            predictor = Predictor()
            if predictor.model_hash != active['model_sha256']:
                raise ValueError('saved model does not match active_text_model.json')
            server.predictor = predictor
        except Exception as error:  # surfaced in /api/info and the UI status pill
            server.load_error = f'{type(error).__name__}: {error}'
            print('Live classifier unavailable: ' + server.load_error, flush=True)

    if load_live:
        threading.Thread(target=load, daemon=True).start()
    return server


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8780)
    args = parser.parse_args()
    with make_server(args.port) as srv:
        print(f'Supervisor Showcase ready: http://127.0.0.1:{srv.server_port}', flush=True)
        srv.serve_forever()
