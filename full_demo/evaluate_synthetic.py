"""Measure the demo pipeline on the repo's synthetic dataset against its generator ground truth.

Scope: the 86 printed/thermal synthetic documents (handwritten ones are out of the project's
printed-only scope). These images were explicitly EXCLUDED from classifier training and tuning
(classifier/engine/prepare.py excluded_sources), but they are synthetic, clean renders, so the
numbers below are NOT a real-world accuracy estimate.

    python full_demo/evaluate_synthetic.py            # use cached OCR (fast)
    python full_demo/evaluate_synthetic.py --live-ocr # re-run OCR + classifier (about 3 min)
"""
import argparse, json, sys, time, collections, hashlib, subprocess
from decimal import Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from extractor import RulesExtractor  # noqa: E402
from verify import verify  # noqa: E402

CACHE = HERE / 'data' / 'synthetic_ocr_cache.json'
OUT = HERE / 'data' / 'evaluation.json'


def dec(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def live_ocr():
    sys.path.insert(0, str(ROOT / 'classifier' / 'engine'))
    from inference import Predictor
    predictor = Predictor()
    meta = json.loads((ROOT / 'synthetic_dataset' / 'manifest.json').read_text())
    docs = {}
    for row in meta:
        if row['production_method'] not in ('printed', 'thermal'):
            continue
        res = predictor.predict_image(ROOT / 'synthetic_dataset' / 'images' / (row['file'] + '.jpg'))
        docs[row['file']] = {'label': res['label'], 'decision_source': res['decision_source'], 'ocr_text': res['ocr_text']}
    tess = subprocess.run(['tesseract', '--version'], capture_output=True, text=True).stdout.splitlines()[0]
    CACHE.write_text(json.dumps({'tesseract': tess, 'model_sha256': predictor.model_hash, 'docs': docs}, indent=1))


def field_errors(rec, truth):
    errs = []
    if rec['document_number'] != truth['document_number']: errs.append('document_number')
    if rec['date'] != truth['document_date']: errs.append('date')
    if dec(rec['totals']['grand_total']) != dec(truth['grand_total']): errs.append('grand_total')
    rows, trows = rec['line_items'], truth['line_items']
    if len(rows) != len(trows):
        errs.append('line_count')
    for i, t in enumerate(trows[:len(rows)]):
        r = rows[i]
        if r['raw_text'] != t['raw_text']: errs.append('description')
        for k in ('quantity', 'unit_price', 'line_total'):
            if dec(r[k]) != dec(t[k]): errs.append(k)
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--live-ocr', action='store_true')
    args = ap.parse_args()
    if args.live_ocr or not CACHE.exists():
        live_ocr()
    cache = json.loads(CACHE.read_text())
    meta = {r['file']: r for r in json.loads((ROOT / 'synthetic_dataset' / 'manifest.json').read_text())}
    extractor = RulesExtractor()
    per_doc, cls = [], collections.defaultdict(collections.Counter)
    for name, doc in cache['docs'].items():
        truth = json.loads((ROOT / 'synthetic_dataset' / 'json' / (name + '.json')).read_text())
        true_type = truth['document_type']
        cls[true_type][(doc['label'], doc['decision_source'])] += 1
        rec = extractor.extract(doc['label'], doc['ocr_text'])
        errs = field_errors(rec, truth)
        entry = {'file': name, 'true_type': true_type, 'routed_type': doc['label'], 'decision_source': doc['decision_source'],
                 'production_method': truth['production_method'], 'truth_review_required': truth['review_required'],
                 'field_errors': errs}
        for key, pol in (('strict', ('literal', 'strict')), ('demo_reconcile', ('literal', 'demo_reconcile'))):
            entry[key + '_flagged'] = verify(rec, doc['ocr_text'], *pol)['review_required']
        per_doc.append(entry)
    n = len(per_doc)
    routed_ok = sum(d['true_type'] == d['routed_type'] for d in per_doc)
    by_class = {}
    for t, c in cls.items():
        total = sum(c.values()); ok = sum(v for (lab, _), v in c.items() if lab == t)
        by_class[t] = {'n': total, 'correct': ok, 'by_decision_source': {f'{lab}|{src}': v for (lab, src), v in sorted(c.items())}}
    by_source = collections.defaultdict(lambda: [0, 0])
    for d in per_doc:
        by_source[d['decision_source']][0] += 1; by_source[d['decision_source']][1] += d['true_type'] == d['routed_type']
    exact = sum(not d['field_errors'] for d in per_doc)
    err_counts = collections.Counter(e for d in per_doc for e in set(d['field_errors']))
    policies = {}
    for key in ('strict', 'demo_reconcile'):
        cat = collections.Counter()
        for d in per_doc:
            wrong = bool(d['field_errors']) or d['true_type'] != d['routed_type']
            flagged = d[key + '_flagged']
            cat['wrong_flagged' if wrong and flagged else 'wrong_unflagged' if wrong else
                'correct_flagged' if flagged else 'correct_passed'] += 1
        inj = [d for d in per_doc if d['truth_review_required']]
        causes = collections.Counter()
        for d in per_doc:
            if d[key + '_flagged']:
                continue
            fe = set(d['field_errors']); mis = d['true_type'] != d['routed_type']
            if not fe and not mis:
                continue
            causes['misrouted_type_only' if mis and not fe else 'item_description_only' if fe == {'description'} and not mis
                   else 'header_or_number_error' if fe & {'document_number', 'date', 'grand_total', 'quantity', 'unit_price', 'line_total', 'line_count'}
                   else 'other'] += 1
        policies[key] = {'wrong_unflagged_by_cause': dict(causes), 'flagged': sum(d[key + '_flagged'] for d in per_doc),
                         'injected_error_docs': len(inj),
                         'injected_error_docs_flagged': sum(d[key + '_flagged'] for d in inj),
                         'outcomes': dict(cat)}
    result = {
        'scope': '86 printed/thermal synthetic documents (handwritten excluded). Clean renders; not a real-world estimate.',
        'ocr_environment': {'tesseract': cache['tesseract'], 'classifier_model_sha256': cache['model_sha256']},
        'documents': n,
        'classifier': {'routed_correctly': routed_ok, 'accuracy': round(routed_ok / n, 4), 'by_class': by_class,
                       'by_decision_source': {k: {'n': v[0], 'correct': v[1]} for k, v in by_source.items()}},
        'extraction': {'extractor': extractor.name, 'documents_with_all_fields_exact': exact,
                       'documents_with_any_error': n - exact, 'error_field_counts': dict(err_counts),
                       'note': 'Documents are counted wrong if any header, total, row count or row value differs from generator truth. Classifier misroutes are counted separately.'},
        'verification': policies,
        'verification_notes': {
            'strict': 'Project contract unchanged: needs printed subtotal, tax and discount for the grand-total check, so most documents are flagged.',
            'demo_reconcile': 'Demo option: compare sum of line totals with a printed grand total (assumes no tax or discount) and require document number, date and grand total.'},
        'documents_detail': per_doc,
    }
    OUT.write_text(json.dumps(result, indent=1))
    print(json.dumps({k: v for k, v in result.items() if k != 'documents_detail'}, indent=1))


if __name__ == '__main__':
    main()
