"""Contract checks use hand-built controlled fixtures, not measured corpus results."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from contract import validate_record, validate_structure


def fixture():
    text = 'Receipt R-17 24/10/2026 BDT\nWidget 2 3.50 7.00\nSubtotal 7.00\nTax 0.00\nDiscount 0.00\nGrand total 7.00'
    record = {
        'schema_version': '1.0', 'document_type': 'receipt',
        'document_number': 'R-17', 'date': '24/10/2026', 'currency': 'BDT',
        'line_items': [{'raw_text': 'Widget 2 3.50 7.00', 'quantity': '2', 'unit_price': '3.50', 'line_total': '7.00'}],
        'totals': {'subtotal': '7.00', 'tax': '0.00', 'discount': '0.00', 'grand_total': '7.00'},
        'evidence': {'/document_number': 'Receipt R-17', '/date': '24/10/2026', '/currency': 'BDT'},
        'uncertainties': [], 'corrections': []}
    for key in record['line_items'][0]:
        record['evidence']['/line_items/0/' + key] = 'Widget 2 3.50 7.00'
    for key in record['totals']:
        record['evidence']['/totals/' + key] = record['totals'][key]
    return text, record


class ContractTests(unittest.TestCase):
    def test_numeric_evidence_cannot_match_partial_digits(self):
        for quote in ['Qty 12', 'Qty 2.0', 'Qty 2,000']:
            with self.subTest(quote=quote):
                text, record = fixture()
                record['evidence']['/line_items/0/quantity'] = quote
                report = validate_record(record, text + '\n' + quote)
                finding = next(f for f in report['evidence_findings'] if f['path'] == '/line_items/0/quantity')
                self.assertEqual(finding['status'], 'partial_numeric_token')
                self.assertTrue(report['review_required'])

    def test_opt_in_grouping_normalization_records_source_token(self):
        text, record = fixture()
        record['line_items'][0]['unit_price'] = '1850'
        record['evidence']['/line_items/0/unit_price'] = 'Rate 1,850'
        text += '\nRate 1,850'
        literal = validate_record(record, text)
        self.assertEqual(literal['normalization_findings'], [])
        audited = validate_record(record, text, numeric_policy='grouped_commas')
        self.assertEqual(audited['normalization_findings'][0]['source_token'], '1,850')
        self.assertEqual(audited['normalization_findings'][0]['normalized_value'], '1850')
        self.assertEqual(audited['record'], record)
        self.assertTrue(audited['review_required'])

    def test_grouping_policy_does_not_guess_other_locale_formats(self):
        text, record = fixture()
        for token in ['1,85', '1.850,00', '1 850', '1850.00']:
            record['line_items'][0]['unit_price'] = '1850'
            record['evidence']['/line_items/0/unit_price'] = token
            audit = validate_record(record, text + '\n' + token, numeric_policy='grouped_commas')
            self.assertEqual(audit['normalization_findings'], [])
        with self.assertRaises(ValueError):
            validate_record(record, text, numeric_policy='unknown')

    def test_quantity_only_delivery_note_does_not_require_prices(self):
        text = 'Challan\nRice bags 6'
        record = {'schema_version':'1.0', 'document_type':'delivery_note',
            'document_number':None,'date':None,'currency':None,
            'line_items':[{'raw_text':'Rice bags','quantity':'6','unit_price':None,'line_total':None}],
            'totals':{'subtotal':None,'tax':None,'discount':None,'grand_total':None},
            'evidence':{'/line_items/0/raw_text':'Rice bags 6','/line_items/0/quantity':'Rice bags 6'},
            'uncertainties':[],'corrections':[]}
        report = validate_record(record,text)
        self.assertFalse(report['review_required'])
        self.assertTrue(all(c['status']=='not_applicable' for c in report['checks']))
        record['line_items'][0]['quantity'] = None
        del record['evidence']['/line_items/0/quantity']
        self.assertTrue(validate_record(record,text)['review_required'])
        record['line_items'] = []
        record['evidence'] = {}
        self.assertTrue(validate_record(record,text)['review_required'])

    def test_complete_consistent_record(self):
        text, record = fixture()
        report = validate_record(record, text)
        self.assertFalse(report['review_required'])
        self.assertEqual([c['status'] for c in report['checks']], ['passed'] * 3)
        self.assertEqual(report['record'], record)

    def test_input_and_report_do_not_alias_or_mutate(self):
        text, record = fixture()
        snapshot = deepcopy(record)
        report = validate_record(record, text)
        report['record']['totals']['tax'] = '999'
        self.assertEqual(record, snapshot)

    def test_decimal_input_rejections(self):
        for value in [True, False, 0, 1.2, 'NaN', 'Infinity', '-1', '1e3', '1,000', ' 2', '.5', '2.', '2\n', '', '9' * 129]:
            with self.subTest(value=value):
                text, record = fixture()
                record['line_items'][0]['quantity'] = value
                with self.assertRaises(ValueError):
                    validate_record(record, text)

    def test_extra_keys_at_every_level(self):
        for location in ['root', 'line', 'totals', 'correction']:
            with self.subTest(location=location):
                text, record = fixture()
                target = record
                if location == 'line': target = record['line_items'][0]
                if location == 'totals': target = record['totals']
                if location == 'correction':
                    record['corrections'] = [{'before': '2', 'after': '3', 'reason': 'uncertain'}]
                    target = record['corrections'][0]
                target['confidence'] = 0.999
                with self.assertRaises(ValueError): validate_record(record, text)

    def test_missing_required_keys(self):
        text, record = fixture()
        del record['date']
        with self.assertRaises(ValueError): validate_record(record, text)

    def test_bad_types_and_unknown_class(self):
        for key, value in [('schema_version', 1), ('document_type', 'invoice'), ('document_number', True), ('line_items', {}), ('totals', []), ('evidence', []), ('uncertainties', 'none'), ('corrections', {})]:
            with self.subTest(key=key):
                text, record = fixture()
                record[key] = value
                with self.assertRaises(ValueError): validate_record(record, text)

    def test_missing_evidence_is_review_not_rejection(self):
        text, record = fixture()
        del record['evidence']['/line_items/0/quantity']
        report = validate_record(record, text)
        self.assertTrue(report['review_required'])
        self.assertIn('Evidence missing: /line_items/0/quantity', report['review_reasons'])

    def test_evidence_must_be_literal_and_contain_value(self):
        for quote, status in [('Widget 2 3.50 7.01', 'not_in_ocr'), ('Receipt R-17', 'value_not_in_evidence')]:
            with self.subTest(status=status):
                text, record = fixture()
                record['evidence']['/line_items/0/quantity'] = quote
                report = validate_record(record, text)
                self.assertIn(status, [finding['status'] for finding in report['evidence_findings']])
                self.assertTrue(report['review_required'])

    def test_noncanonical_or_spoof_evidence_rejected(self):
        for pointer in ['/totals/fake', '/line_items/00/quantity', '/document_type', 'document_number', '/line_items/99/raw_text']:
            text, record = fixture()
            record['evidence'][pointer] = 'Receipt'
            with self.assertRaises(ValueError): validate_record(record, text)

    def test_null_field_with_evidence_requires_review(self):
        text, record = fixture()
        record['currency'] = None
        report = validate_record(record, text)
        self.assertIn('unexpected', [entry['status'] for entry in report['evidence_findings']])
        self.assertTrue(report['review_required'])

    def test_missing_tax_is_not_zero(self):
        text, record = fixture()
        record['totals']['tax'] = None
        del record['evidence']['/totals/tax']
        report = validate_record(record, text)
        check = report['checks'][-1]
        self.assertEqual(check['status'], 'not_applicable')
        self.assertIn('tax', check['missing'])
        self.assertTrue(report['review_required'])

    def test_missing_line_operands_and_empty_items_require_review(self):
        for empty in [False, True]:
            text, record = fixture()
            if empty:
                record['line_items'] = []
                record['evidence'] = {key: value for key, value in record['evidence'].items() if not key.startswith('/line_items/')}
            else:
                record['line_items'][0]['unit_price'] = None
                del record['evidence']['/line_items/0/unit_price']
            report = validate_record(record, text)
            self.assertTrue(report['review_required'])
            self.assertIn('not_applicable', [entry['status'] for entry in report['checks']])

    def test_arithmetic_failures(self):
        text, record = fixture()
        record['line_items'][0]['line_total'] = '8.00'
        report = validate_record(record, text)
        self.assertEqual(report['checks'][0]['status'], 'failed')
        self.assertEqual(report['checks'][1]['status'], 'failed')
        self.assertTrue(report['review_required'])

    def test_decimal_exactness_and_tolerance_boundary(self):
        for total, status in [('7.01', 'passed'), ('7.0101', 'failed')]:
            text, record = fixture()
            record['line_items'][0]['line_total'] = total
            report = validate_record(record, text)
            self.assertEqual(report['checks'][0]['status'], status)
            self.assertEqual(report['checks'][0]['expected'], '7.00')

    def test_corrections_remain_proposals(self):
        text, record = fixture()
        record['corrections'] = [{'before': 'R-17', 'after': 'R-18', 'reason': 'possible OCR error'}]
        report = validate_record(record, text)
        self.assertEqual(report['record']['document_number'], 'R-17')
        self.assertTrue(report['review_required'])
        record['document_number'] = 'R-18'
        record['evidence']['/document_number'] = 'R-18'
        report = validate_record(record, text)
        self.assertIn('Evidence not_in_ocr: /document_number', report['review_reasons'])

    def test_uncertainty_requires_review(self):
        text, record = fixture()
        record['uncertainties'] = ['quantity unclear']
        self.assertTrue(validate_record(record, text)['review_required'])

    def test_consistent_but_wrong_values_can_pass(self):
        # Controlled adversarial fixture: old amounts also appear in the document.
        # Substring support cannot establish that the model chose the current row.
        text, record = fixture()
        text += '\nCurrent sale: Widget 4 3.50 14.00; current subtotal 14.00; current total 14.00\nPrevious sale above is void.'
        report = validate_record(record, text)
        self.assertFalse(report['review_required'])
        self.assertEqual([entry['status'] for entry in report['checks']], ['passed'] * 3)
        self.assertTrue(any('correct field or row' in message for message in report['limitations']))

    def test_schema_description_and_root_contract(self):
        schema = json.loads(Path(__file__).with_name('schema.json').read_text(encoding='utf-8-sig'))
        text, record = fixture()
        self.assertEqual(set(schema['required']), set(record))
        self.assertFalse(schema['additionalProperties'])
        validate_structure(record)


if __name__ == '__main__':
    unittest.main()
