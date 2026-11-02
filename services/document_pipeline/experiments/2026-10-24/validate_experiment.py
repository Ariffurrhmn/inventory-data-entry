"""Replay blinded sub-agent outputs against the current extraction contract."""
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from services.document_pipeline.contract import validate_record


def run():
    inputs = {row['id']: row for row in json.loads((HERE / 'inputs/ocr-only.json').read_text(encoding='utf-8-sig'))}
    results = {}
    for path in sorted((HERE / 'outputs').glob('*agent-response.json')):
        trial_inputs = inputs
        if path.name.startswith('multiview'):
            trial_inputs = {row['id']: row for row in json.loads((HERE / 'inputs/multiview-ocr-only.json').read_text(encoding='utf-8-sig'))}
        records = json.loads(path.read_text(encoding='utf-8-sig'))
        audits = {}
        for key, original in trial_inputs.items():
            try:
                audit = validate_record(records[key], original['ocr_text'])
                audit['schema_valid'] = True
                audit['evidence_supported'] = all(f['status'] == 'supported' for f in audit['evidence_findings'])
                audit['classification_preserved'] = records[key]['document_type'] == original['document_type']
                audits[key] = audit
            except (KeyError, ValueError, TypeError) as error:
                audits[key] = {'schema_valid': False, 'error': str(error)}
        counts = {name: sum(bool(a.get(name)) for a in audits.values()) for name in ('schema_valid', 'evidence_supported', 'classification_preserved', 'review_required')}
        counts['arithmetic_passed'] = sum(c['status'] == 'passed' for a in audits.values() for c in a.get('checks', []))
        counts['arithmetic_failed'] = sum(c['status'] == 'failed' for a in audits.values() for c in a.get('checks', []))
        counts['arithmetic_unavailable'] = sum(c['status'] == 'not_applicable' for a in audits.values() for c in a.get('checks', []))
        results[path.name] = {'parse_valid': True, 'counts': counts, 'records': audits}
    contract_path = ROOT / 'services/document_pipeline/contract.py'
    result = {'contract_sha256': hashlib.sha256(contract_path.read_bytes()).hexdigest(), 'accuracy_measured': False, 'results': results}
    (HERE / (sys.argv[1] if len(sys.argv) > 1 else 'validation-final.json')).write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({key: value['counts'] for key, value in results.items()}, indent=2))


if __name__ == '__main__':
    run()


