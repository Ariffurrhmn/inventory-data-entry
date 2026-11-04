"""Verification for the demo: the project's unchanged contract checks plus two opt-in policies.

Default (strict, literal) is exactly ``services/document_pipeline/contract.validate_record``.
The two options exist so a supervisor can see the trade-off live; both are reported in the
output and neither is silently applied.

* numeric_policy='grouped_commas'  - the project's own diagnostic: accept "1,850" as 1850
  (assumes English digit grouping; flagged for review by the contract itself).
* policy='demo_reconcile' - DEMO OPTION, not part of the contract. (1) When a document prints
  only a grand total (no subtotal/tax/discount), compare the sum of line totals with it; this
  assumes no tax or discount exists, which the document does not state. (2) Flag documents
  that lack a document number, date or grand total.
"""
import sys
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'services' / 'document_pipeline'))
from contract import validate_record, TOLERANCE  # noqa: E402

NUMERIC_POLICIES = ('literal', 'grouped_commas')
POLICIES = ('strict', 'demo_reconcile')
UNAVAILABLE = ('Arithmetic unavailable: subtotal', 'Arithmetic unavailable: grand_total')


def verify(record, ocr_text, numeric_policy='literal', policy='strict'):
    if numeric_policy not in NUMERIC_POLICIES or policy not in POLICIES:
        raise ValueError('Unknown verification policy')
    report = deepcopy(validate_record(record, ocr_text, numeric_policy))
    report['policy'] = policy
    report['policy_notes'] = []
    if policy == 'demo_reconcile':
        t = record['totals']
        rows = record['line_items']
        applicable = (t['grand_total'] is not None and t['subtotal'] is None and t['tax'] is None
                      and t['discount'] is None and rows and all(r['line_total'] is not None for r in rows))
        if applicable:
            expected = sum((Decimal(r['line_total']) for r in rows), Decimal('0'))
            actual = Decimal(t['grand_total'])
            diff = abs(expected - actual)
            status = 'passed' if diff <= TOLERANCE else 'failed'
            report['checks'].append({'id': 'grand_total_vs_line_sum', 'status': status, 'expected': str(expected),
                                     'actual': str(actual), 'difference': str(diff), 'tolerance': str(TOLERANCE),
                                     'policy': 'demo_option_assumes_no_tax_or_discount'})
            report['review_reasons'] = [x for x in report['review_reasons'] if x not in UNAVAILABLE]
            if status == 'failed':
                report['review_reasons'].append('Arithmetic mismatch: grand_total_vs_line_sum')
            report['policy_notes'].append('Grand total compared with the sum of line totals; assumes the document has no tax or discount.')
        for label, value in (('document number', record['document_number']), ('date', record['date']),
                             ('grand total', t['grand_total'])):
            if value is None:
                report['review_reasons'].append(f'Required header missing: {label}')
                report['policy_notes'].append(f'Demo option requires a {label}.')
        report['review_required'] = bool(report['review_reasons'])
    return report


def summarize(report):
    """Compact counts used by the UI."""
    checks = report['checks']
    evid = report['evidence_findings']
    return {
        'review_required': report['review_required'],
        'reasons': report['review_reasons'],
        'checks_passed': sum(c['status'] == 'passed' for c in checks),
        'checks_failed': sum(c['status'] == 'failed' for c in checks),
        'checks_unavailable': sum(c['status'] == 'not_applicable' for c in checks),
        'evidence_supported': sum(f['status'] in ('supported', 'supported_normalized') for f in evid),
        'evidence_total': len(evid),
        'numeric_policy': report['numeric_policy'],
        'policy': report['policy'],
    }
