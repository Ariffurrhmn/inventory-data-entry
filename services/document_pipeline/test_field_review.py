"""Controlled synthetic software fixtures; never corpus accuracy results."""
from copy import deepcopy
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from field_review import append_review, blank, evaluate, prepare, validate


class FieldReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.image = self.root / 'fixture.bin'
        self.image.write_bytes(b'synthetic source identity only')
        self.candidate = {'document_type': 'receipt', 'document_number': None, 'date': None,
                          'currency': None, 'totals': {k: None for k in ('subtotal', 'tax', 'discount', 'grand_total')},
                          'line_items': [{'raw_text': 'Wrong', 'quantity': '2.00', 'unit_price': None, 'line_total': None}]}
        self.path = self.root / 'candidate.json'
        self.path.write_text(json.dumps(self.candidate), encoding='utf-8')
        self.review = prepare(self.image, self.path)
        self.review['reviewer'] = 'fixture reviewer'

    def human(self):
        self.review.update(reviewer_type='human', human_verified=True,
                           independent_reference=True, reference_first_attestation=True)

    def test_blank_does_not_copy_candidate_or_row_count(self):
        self.assertEqual(self.review['rows'], [])
        self.assertEqual(self.review['fields']['document_type']['value'], None)
        self.assertFalse(self.review['human_verified'])

    def test_ai_cannot_assert_truth(self):
        self.review['human_verified'] = True
        with self.assertRaises(ValueError):
            validate(self.review, self.candidate)

    def test_unverified_cannot_measure_accuracy(self):
        with self.assertRaises(ValueError):
            evaluate(self.review, self.candidate)
        self.human()
        self.review['reference_first_attestation'] = False
        with self.assertRaises(ValueError):
            evaluate(self.review, self.candidate)

    def test_field_accuracy_row_mapping_and_exclusions(self):
        self.human()
        self.review['fields']['document_type'] = {'status': 'value', 'value': 'receipt'}
        self.review['fields']['document_number'] = {'status': 'absent', 'value': None}
        self.review['fields']['date'] = {'status': 'not_legible', 'value': None}
        self.review['fields']['currency'] = {'status': 'uncertain', 'value': None}
        fields = {key: blank() for key in ('raw_text', 'quantity', 'unit_price', 'line_total')}
        fields['raw_text'] = {'status': 'value', 'value': 'Right'}
        fields['quantity'] = {'status': 'value', 'value': '2'}
        self.review['rows'] = [{'candidate_index': 0, 'fields': fields},
                               {'candidate_index': None, 'fields': deepcopy(fields)}]
        self.review['rows_complete'] = True
        result = evaluate(self.review, self.candidate)
        self.assertEqual(result['eligible_fields'], 6)
        self.assertEqual(result['correct_fields'], 3)
        self.assertEqual(result['field_accuracy'], 0.5)
        self.assertEqual(result['missing_rows'], 1)
        self.assertEqual(result['row_recall'], 0.5)
        self.assertEqual(result['row_precision'], 1)
        self.assertEqual(result['excluded_not_legible'], 1)
        self.assertEqual(result['excluded_uncertain'], 1)

    def test_alignment_must_be_one_to_one_and_complete(self):
        self.review['rows_complete'] = True
        with self.assertRaises(ValueError):
            validate(self.review, self.candidate)
        self.review['spurious_candidate_rows'] = [0]
        validate(self.review, self.candidate)
        self.review['spurious_candidate_rows'] = [0, 0]
        with self.assertRaises(ValueError):
            validate(self.review, self.candidate)

    def test_source_binding_and_append_only_history(self):
        db = self.root / 'reviews.sqlite3'
        first = append_review(db, self.review, self.image, self.path)
        self.review['note'] = 'new revision'
        second = append_review(db, self.review, self.image, self.path)
        self.assertNotEqual(first, second)
        with closing(sqlite3.connect(db)) as connection, connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM field_reviews').fetchone()[0], 2)
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute('DELETE FROM field_reviews')
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("UPDATE field_reviews SET payload='{}'")
        self.image.write_bytes(b'changed')
        with self.assertRaises(ValueError):
            append_review(db, self.review, self.image, self.path)

    def test_nonvalue_states_cannot_smuggle_truth(self):
        self.review['fields']['date'] = {'status': 'uncertain', 'value': 'guess'}
        with self.assertRaises(ValueError):
            validate(self.review, self.candidate)

    def test_numeric_truth_never_guesses_locale(self):
        self.review['totals']['grand_total'] = {'status': 'value', 'value': '1,000'}
        with self.assertRaises(ValueError):
            validate(self.review, self.candidate)


if __name__ == '__main__':
    unittest.main()
