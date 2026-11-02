"""Twelve image-region OCR diagnostics; manual regions are not a deployed detector.

Run with the classifier runtime. Writes a new output directory, never overwrites.
Numeric agreement is against unverified AI observations, never measured accuracy.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageFilter, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SPECS = {
    '76cc99d39da4': {
        'table': (.07, .389, .905, .566),
        'rows': [(.456, .497), (.509, .551)],
        'columns': [(.095, .394), (.414, .507), (.531, .682), (.703, .886)],
    },
    'f9918570b903': {
        'table': (.104, .394, .944, .750),
        'rows': [(.462, .511), (.518, .568), (.576, .625), (.634, .681), (.690, .740)],
        'columns': [(.132, .222), (.244, .747), (.775, .920)],
    },
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def crop(im, box):
    x1, y1, x2, y2 = box
    return im.crop((round(x1 * im.width), round(y1 * im.height), round(x2 * im.width), round(y2 * im.height)))


def normalize(im):
    background = im.filter(ImageFilter.GaussianBlur(24))
    ratio = np.asarray(im, dtype=np.float32) / np.maximum(np.asarray(background, dtype=np.float32), 1)
    return Image.fromarray(np.clip(ratio * 235, 0, 255).astype('uint8'))


def montage(im, spec, cells):
    rows = []
    for y1, y2 in spec['rows']:
        if cells:
            tiles = [crop(im, (x1, y1, x2, y2)) for x1, x2 in spec['columns']]
        else:
            tiles = [crop(im, (spec['table'][0] + .015, y1, spec['table'][2] - .015, y2))]
        row = Image.new('L', (sum(tile.width for tile in tiles) + 45 * (len(tiles) - 1) + 40, max(tile.height for tile in tiles) + 40), 255)
        offset = 20
        for tile in tiles:
            row.paste(tile, (offset, 20))
            offset += tile.width + 45
        rows.append(row)
    result = Image.new('L', (max(row.width for row in rows), sum(row.height for row in rows) + 30 * (len(rows) - 1)), 255)
    offset = 0
    for row in rows:
        result.paste(row, (0, offset))
        offset += row.height + 30
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE / 'results')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit('Output already exists; choose a new --output path to preserve evidence.')
    output.mkdir(parents=True)
    tesseract = shutil.which('tesseract')
    tessdata = ROOT / 'classifier/engine/.cache/tessdata'
    observation_path = HERE.parent / 'outputs/image-assisted-observations.json'
    observations = json.loads(observation_path.read_text(encoding='utf-8-sig'))
    metadata = {
        'kind': 'bounded_development_ocr_region_diagnostic',
        'python': sys.executable, 'script_sha256': sha(Path(__file__)),
        'tesseract_executable': tesseract,
        'tesseract_version': subprocess.run([tesseract, '--version'], capture_output=True, text=True).stdout,
        'tessdata': str(tessdata), 'eng_traineddata_sha256': sha(tessdata / 'eng.traineddata'),
        'observation_sha256': sha(observation_path),
        'diagnostic_reference': 'AI image-assisted observation; human_verified=false; not ground truth',
        'manual_regions': SPECS,
        'limits': ['Two deliberately selected exposed development documents; no independent accuracy.',
                   'Manual image-specific crops are not deployed region detection.',
                   'Token presence cannot establish row or column assignment.',
                   'All twelve candidates, including failures, retained; no model promotion.'],
        'inputs': {}, 'candidates': [],
    }
    env = os.environ.copy()
    env['OMP_THREAD_LIMIT'] = '1'
    for sid, spec in SPECS.items():
        source = ROOT / f'classifier/demo/images/{sid}.jpg'
        with Image.open(source) as raw:
            gray = ImageOps.grayscale(ImageOps.exif_transpose(raw))
        metadata['inputs'][sid] = {'path': str(source.relative_to(ROOT)), 'sha256': sha(source), 'size': list(gray.size)}
        table_gray = crop(gray, spec['table'])
        table_normalized = crop(normalize(gray), spec['table'])
        normalized = normalize(gray)
        variants = [
            ('table_gray_psm6', table_gray, 6),
            ('table_normalized_psm6', table_normalized, 6),
            ('table_normalized_psm11', table_normalized, 11),
            ('table_binary190_psm6', table_normalized.point(lambda v: 0 if v < 190 else 255), 6),
            ('row_interiors_psm6', montage(normalized, spec, False), 6),
            ('cell_interiors_psm6', montage(normalized, spec, True), 6),
        ]
        for name, view, psm in variants:
            tag = sid + '_' + name
            # Uniform 2x upsample; border avoids clipping glyphs at crop boundaries.
            view = view.resize((view.width * 2, view.height * 2), Image.Resampling.LANCZOS)
            image_path = output / (tag + '.png')
            ImageOps.expand(view, border=30, fill=255).save(image_path)
            base = output / tag
            command = [tesseract, str(image_path), str(base), '--tessdata-dir', str(tessdata), '-l', 'eng', '--psm', str(psm), '-c', 'tessedit_create_txt=1', '-c', 'tessedit_create_tsv=1']
            start = time.perf_counter()
            proc = subprocess.run(command, capture_output=True, env=env, timeout=120)
            duration = time.perf_counter() - start
            text_path = base.with_suffix('.txt')
            text = text_path.read_text(encoding='utf-8') if text_path.exists() else ''
            tokens = re.findall(r'(?<![\w.])[0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?(?![\w.])', text)
            normalized_tokens = [token.replace(',', '') for token in tokens]
            expected_rows = observations[sid]['rows']
            presence = []
            for row in expected_rows:
                values = {key: value for key, value in row.items() if key != 'description' and value is not None}
                presence.append({'ai_observed_values': values, 'token_present_somewhere': {key: value in normalized_tokens for key, value in values.items()}})
            item = {'id': sid, 'variant': name, 'psm': psm, 'command': command,
                    'seconds': round(duration, 4), 'returncode': proc.returncode,
                    'stderr': proc.stderr.decode('utf-8', errors='replace'),
                    'image': image_path.name, 'image_sha256': sha(image_path),
                    'ocr_text': text, 'ocr_text_file': text_path.name,
                    'tsv_file': base.with_suffix('.tsv').name,
                    'numeric_tokens': tokens, 'ai_observation_token_diagnostic': presence}
            metadata['candidates'].append(item)
            print(json.dumps({'id': sid, 'variant': name, 'seconds': item['seconds'], 'returncode': proc.returncode, 'ocr': text}, ensure_ascii=False), flush=True)
    (output / 'manifest.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()


