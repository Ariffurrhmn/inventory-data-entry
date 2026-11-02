"""Strict extraction contract and conservative arithmetic/evidence review.

No extraction value is changed. Passing checks cannot establish document truth.
"""
from copy import deepcopy
from decimal import Decimal, localcontext
import re

DOCUMENT_TYPES = ('purchase_order', 'receipt', 'delivery_note', 'customer_copy')
DECIMAL_PATTERN = r'^[0-9]+(?:\.[0-9]+)?$'
ROOT_KEYS = {'schema_version', 'document_type', 'document_number', 'date', 'currency',
             'line_items', 'totals', 'evidence', 'uncertainties', 'corrections'}
LINE_KEYS = {'raw_text', 'quantity', 'unit_price', 'line_total'}
TOTAL_KEYS = {'subtotal', 'tax', 'discount', 'grand_total'}
TOLERANCE = Decimal('0.01')


def _object(value, keys, path):
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f'{path}: expected object with exactly {sorted(keys)}')


def _string(value, path, nullable=False):
    if nullable and value is None:
        return
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{path}: expected nonempty string' + (' or null' if nullable else ''))


def _number(value, path):
    if value is None:
        return
    if not isinstance(value, str) or re.fullmatch(DECIMAL_PATTERN, value) is None:
        raise ValueError(f'{path}: expected nonnegative plain decimal string or null')
    # Bound resource use without imposing ordinary currency precision limits.
    if len(value) > 128:
        raise ValueError(f'{path}: decimal exceeds 128 characters')


def validate_structure(record):
    """Raise ValueError if the JSON-compatible record violates contract v1."""
    _object(record, ROOT_KEYS, '/')
    if record['schema_version'] != '1.0':
        raise ValueError('/schema_version: expected 1.0')
    if record['document_type'] not in DOCUMENT_TYPES:
        raise ValueError('/document_type: unknown document class')
    for key in ('document_number', 'date', 'currency'):
        _string(record[key], '/' + key, nullable=True)
    if not isinstance(record['line_items'], list):
        raise ValueError('/line_items: expected array')
    for i, row in enumerate(record['line_items']):
        path = f'/line_items/{i}'
        _object(row, LINE_KEYS, path)
        _string(row['raw_text'], path + '/raw_text')
        for key in LINE_KEYS - {'raw_text'}:
            _number(row[key], path + '/' + key)
    _object(record['totals'], TOTAL_KEYS, '/totals')
    for key, value in record['totals'].items():
        _number(value, '/totals/' + key)
    if not isinstance(record['evidence'], dict):
        raise ValueError('/evidence: expected object')
    allowed = {'/document_number', '/date', '/currency'}
    allowed |= {'/totals/' + key for key in TOTAL_KEYS}
    allowed |= {f'/line_items/{i}/{key}' for i in range(len(record['line_items'])) for key in LINE_KEYS}
    for pointer, quote in record['evidence'].items():
        if pointer not in allowed:
            raise ValueError('/evidence: unknown or noncanonical JSON pointer ' + repr(pointer))
        _string(quote, '/evidence/' + pointer)
    if not isinstance(record['uncertainties'], list):
        raise ValueError('/uncertainties: expected array')
    for i, entry in enumerate(record['uncertainties']):
        _string(entry, f'/uncertainties/{i}')
    if not isinstance(record['corrections'], list):
        raise ValueError('/corrections: expected array')
    for i, entry in enumerate(record['corrections']):
        _object(entry, {'before', 'after', 'reason'}, f'/corrections/{i}')
        for key, value in entry.items():
            _string(value, f'/corrections/{i}/{key}')


def validate_record(record, ocr_text, numeric_policy="literal"):
    """Validate immutable OCR-backed extraction; return audit and review findings.

    Evidence matches literal substrings, including numeric formatting. Corrections
    are unverified proposals and cannot substitute for the original OCR evidence.
    Amounts use Decimal and an absolute 0.01 tolerance; rounding policy remains a
    consuming-system decision. Missing operands never become implicit zeroes.
    """
    if numeric_policy not in {'literal', 'grouped_commas'}:
        raise ValueError('Unknown numeric evidence policy')
    if not isinstance(ocr_text, str):
        raise ValueError('ocr_text: expected string')
    validate_structure(record)
    preserved = deepcopy(record)
    reasons = []
    findings = []
    checks = []
    quantity_only_delivery = record['document_type'] == 'delivery_note' and all(
        value is None for row in record['line_items'] for key, value in row.items() if key in {'unit_price', 'line_total'}) and all(
        value is None for value in record['totals'].values())
    if not record['line_items']:
        reasons.append('No extracted line items')
    for i, row in enumerate(record['line_items']):
        if row['quantity'] is None:
            reasons.append(f'Missing quantity: line_items/{i}')
    normalization_findings = []
    fields = [(f'/{key}', record[key]) for key in ('document_number', 'date', 'currency')]
    fields += [(f'/line_items/{i}/{key}', row[key]) for i, row in enumerate(record['line_items']) for key in sorted(LINE_KEYS)]
    fields += [(f'/totals/{key}', record['totals'][key]) for key in sorted(TOTAL_KEYS)]
    for pointer, value in fields:
        quote = record['evidence'].get(pointer)
        if value is None:
            if quote is not None:
                findings.append({'path': pointer, 'status': 'unexpected', 'quote': quote})
                reasons.append(f'Evidence supplied for null field {pointer}')
            continue
        if quote is None:
            status = 'missing'
        elif quote not in ocr_text:
            status = 'not_in_ocr'
        elif value not in quote:
            status = 'value_not_in_evidence'
        elif (pointer.startswith('/totals/') or pointer.rsplit('/', 1)[-1] in {'quantity', 'unit_price', 'line_total'}) and not re.search(r'(?<![0-9.,])' + re.escape(value) + r'(?![0-9.,])', quote):
            status = 'partial_numeric_token'
        else:
            status = 'supported'
        numeric_field = pointer.startswith('/totals/') or pointer.rsplit('/', 1)[-1] in {'quantity', 'unit_price', 'line_total'}
        if numeric_policy == 'grouped_commas' and numeric_field and status in {'value_not_in_evidence', 'partial_numeric_token'}:
            tokens = re.findall(r'(?<![0-9.,])[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?(?![0-9.,])', quote)
            matches = [token for token in tokens if token.replace(',', '') == value]
            if matches:
                status = 'supported_normalized'
                normalization_findings.append({'path': pointer, 'source_token': matches[0],
                    'normalized_value': value, 'rule': 'assumed_English_grouped_commas'})
        findings.append({'path': pointer, 'status': status, 'quote': quote})
        if status not in {'supported', 'supported_normalized'}:
            reasons.append(f'Evidence {status}: {pointer}')

    def check(check_id, operands, expected=None, actual=None):
        missing = [name for name, value in operands.items() if value is None]
        if missing:
            checks.append({'id': check_id, 'status': 'not_applicable', 'missing': missing})
            if not quantity_only_delivery:
                reasons.append(f'Arithmetic unavailable: {check_id}')
            return
        difference = abs(expected - actual)
        status = 'passed' if difference <= TOLERANCE else 'failed'
        checks.append({'id': check_id, 'status': status, 'expected': str(expected),
                       'actual': str(actual), 'difference': str(difference),
                       'tolerance': str(TOLERANCE)})
        if status == 'failed':
            reasons.append(f'Arithmetic mismatch: {check_id}')

    # 128-digit bounded inputs may create 256-digit products; avoid context rounding.
    with localcontext() as ctx:
        ctx.prec = max(300, 260 + len(str(len(record['line_items']))))
        for i, row in enumerate(record['line_items']):
            values = {key: None if row[key] is None else Decimal(row[key])
                      for key in ('quantity', 'unit_price', 'line_total')}
            complete = all(value is not None for value in values.values())
            expected = values['quantity'] * values['unit_price'] if complete else None
            check(f'line_items/{i}/multiplication', values, expected, values['line_total'])
        totals = {key: None if value is None else Decimal(value) for key, value in record['totals'].items()}
        line_totals = [None if row['line_total'] is None else Decimal(row['line_total']) for row in record['line_items']]
        subtotal_operands = {'subtotal': totals['subtotal']}
        subtotal_operands.update({f'line_items/{i}/line_total': value for i, value in enumerate(line_totals)})
        if not line_totals:
            subtotal_operands['line_items'] = None
        complete = all(value is not None for value in subtotal_operands.values())
        check('subtotal', subtotal_operands, sum(line_totals, Decimal('0')) if complete else None, totals['subtotal'])
        complete = all(value is not None for value in totals.values())
        expected = totals['subtotal'] + totals['tax'] - totals['discount'] if complete else None
        check('grand_total', totals, expected, totals['grand_total'])
    if normalization_findings:
        reasons.append('Numeric grouping normalization uses an explicit unverified locale assumption')
    if record['uncertainties']:
        reasons.append('Model reported unresolved uncertainties')
    if record['corrections']:
        reasons.append('OCR corrections are unverified proposals')
        for i, correction in enumerate(record['corrections']):
            if correction['before'] not in ocr_text:
                reasons.append(f'Correction {i} before text absent from original OCR')
    if not ocr_text.strip():
        reasons.append('Empty original OCR')
    return {'record': preserved, 'numeric_policy': numeric_policy, 'normalization_findings': normalization_findings, 'checks': checks, 'review_required': bool(reasons),
            'review_reasons': reasons, 'evidence_findings': findings,
            'limitations': ['Evidence proves substring presence, not the correct field or row assignment.',
                            'Arithmetic consistency cannot prove values match the source document.',
                            'Model self-confidence is not a calibrated confidence signal.',
                            'Absolute arithmetic tolerance is 0.01; currency and rounding policy are not inferred.',
                            'Quantity-only delivery notes do not require monetary operands; unavailable arithmetic stays not_applicable.']}

