"""Optional region evidence adapter. Classifier OCR and routing remain immutable."""
import hashlib
from pathlib import Path

def combine(primary, region):
    return primary + '\n\nBEGIN_AUTOMATIC_REGION_OCR\n' + region + '\nEND_AUTOMATIC_REGION_OCR\n'

def make_region_processor(audit_root, tessdata):
    def process(image, submission_id, primary):
        from localization import analyze
        audit = Path(audit_root) / submission_id
        result = analyze(image, audit, tessdata)
        # Fixed geometry-only priority; never choose by expected values or OCR content.
        chosen = next((c for c in result['candidates'] if c['layout']['tables'] and c.get('ocr', {}).get('returncode') == 0), None)
        region = chosen['ocr']['ocr_text'] if chosen else ''
        text = combine(primary, region) if chosen else primary
        return {'kind': 'primary_plus_automatic_regions', 'ocr_text': text,
                'ocr_text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
                'primary_ocr_sha256': hashlib.sha256(primary.encode('utf-8')).hexdigest(),
                'source_image_sha256': result['source_sha256'], 'human_verified': False,
                'method': chosen['method'] if chosen else None,
                'status': 'regions_added' if chosen else 'no_grid_primary_only',
                'audit_directory': str(audit.resolve()),
                'audit_sha256': hashlib.sha256((audit/'result.json').read_bytes()).hexdigest(),
                'limitations': ['Detected cells and OCR are unverified candidates; text presence cannot establish field roles.',
                               'Repeated full-page and region views describe the same rows; do not duplicate them.']}
    return process
