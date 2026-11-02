"""Separate, append-only field review. No OCR/schema/arithmetic pass creates truth."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import uuid

HEADERS = ('document_type', 'document_number', 'date', 'currency')
TOTALS = ('subtotal', 'tax', 'discount', 'grand_total')
ITEMS = ('raw_text', 'quantity', 'unit_price', 'line_total')
STATES = {'value', 'absent', 'uncertain', 'not_legible', 'unreviewed'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def blank():
    return {'status': 'unreviewed', 'value': None, 'note': ''}


def prepare(image, candidate):
    """Blank reference deliberately never copies candidate values or row count."""
    return {'version': 1, 'image_sha256': digest(image),
            'candidate_sha256': digest(candidate), 'reviewer': '', 'reviewer_type': 'ai',
            'human_verified': False, 'independent_reference': False,
            'reference_first_attestation': False, 'rows_complete': False,
            'fields': {k: blank() for k in HEADERS},
            'totals': {k: blank() for k in TOTALS}, 'rows': [],
            'spurious_candidate_rows': [], 'note': ''}


def validate(review, candidate):
    if review.get('version') != 1:
        raise ValueError('Unknown review version')
    if not isinstance(review.get('reviewer'), str) or not review['reviewer'].strip():
        raise ValueError('Explicit reviewer identity required')
    if review.get('reviewer_type') not in ('human', 'ai'):
        raise ValueError('Reviewer type must be human or ai')
    for key in ('human_verified', 'independent_reference', 'reference_first_attestation', 'rows_complete'):
        if type(review.get(key)) is not bool:
            raise ValueError(key + ' must be boolean')
    if review['human_verified'] and review['reviewer_type'] != 'human':
        raise ValueError('AI reviews cannot assert human verification')
    if review['independent_reference'] and not (review['human_verified'] and review['reference_first_attestation']):
        raise ValueError('Independent reference needs verified human reference-first attestation')
    for key in ('image_sha256', 'candidate_sha256'):
        if not re.fullmatch('[a-f0-9]{64}', review.get(key, '')):
            raise ValueError('Invalid source hash')
    def fields(values, keys):
        if set(values) != set(keys):
            raise ValueError('Missing or unexpected reference fields')
        for key, value in values.items():
            if value.get('status') not in STATES:
                raise ValueError('Invalid field judgment')
            truth = value.get('value')
            if value['status'] == 'value':
                if not isinstance(truth, str) or not truth.strip():
                    raise ValueError('Readable field requires nonempty human transcription')
                if key in set(TOTALS) | {'quantity', 'unit_price', 'line_total'} and not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?', truth):
                    raise ValueError('Numeric truth requires plain nonnegative decimal; unresolved locale remains uncertain')
            elif truth is not None:
                raise ValueError('Non-value judgment must retain null truth')
    fields(review['fields'], HEADERS)
    fields(review['totals'], TOTALS)
    seen = set()
    for row in review['rows']:
        fields(row['fields'], ITEMS)
        index = row.get('candidate_index')
        if index is not None:
            if type(index) is not int or index < 0 or index >= len(candidate['line_items']) or index in seen:
                raise ValueError('Invalid or duplicate row alignment')
            seen.add(index)
    for index in review['spurious_candidate_rows']:
        if type(index) is not int or index < 0 or index >= len(candidate['line_items']) or index in seen:
            raise ValueError('Invalid or duplicate spurious row')
        seen.add(index)
    if review['rows_complete'] and seen != set(range(len(candidate['line_items']))):
        raise ValueError('Complete row review must account for every candidate row')


def append_review(database, review, image, candidate_path):
    if review['image_sha256'] != digest(image) or review['candidate_sha256'] != digest(candidate_path):
        raise ValueError('Image/candidate hash mismatch')
    candidate = json.loads(Path(candidate_path).read_text(encoding='utf-8-sig'))
    validate(review, candidate)
    payload = json.dumps(review, ensure_ascii=False, sort_keys=True)
    record_id = str(uuid.uuid4())
    with closing(sqlite3.connect(database)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS field_reviews (id TEXT PRIMARY KEY, created_utc TEXT NOT NULL, payload TEXT NOT NULL, payload_sha256 TEXT NOT NULL)')
        db.execute("CREATE TRIGGER IF NOT EXISTS no_review_update BEFORE UPDATE ON field_reviews BEGIN SELECT RAISE(ABORT, 'append only'); END")
        db.execute("CREATE TRIGGER IF NOT EXISTS no_review_delete BEFORE DELETE ON field_reviews BEGIN SELECT RAISE(ABORT, 'append only'); END")
        db.execute('INSERT INTO field_reviews VALUES (?,?,?,?)', (record_id, datetime.now(timezone.utc).isoformat(), payload, hashlib.sha256(payload.encode()).hexdigest()))
    return record_id


def evaluate(review, candidate):
    validate(review, candidate)
    if not (review['human_verified'] and review['independent_reference'] and review['reference_first_attestation']):
        raise ValueError('Accuracy requires independent, human-verified reference')
    counts = {'eligible_fields': 0, 'correct_fields': 0, 'populated_fields': 0,
              'excluded_uncertain': 0, 'excluded_not_legible': 0, 'unreviewed_fields': 0}
    findings = []
    def score(path, ref, actual, numeric=False):
        state = ref['status']
        if state not in ('value', 'absent'):
            counts[{'uncertain': 'excluded_uncertain', 'not_legible': 'excluded_not_legible', 'unreviewed': 'unreviewed_fields'}[state]] += 1
            return
        expected = ref['value']
        equal = actual == expected
        if numeric and state == 'value' and actual is not None:
            try:
                # No thousands/locale guesses; finite, nonnegative plain decimals only.
                if all(isinstance(v, str) and re.fullmatch(r'[0-9]+(?:\.[0-9]+)?', v) for v in (actual, expected)):
                    equal = Decimal(actual) == Decimal(expected)
            except InvalidOperation:
                equal = False
        counts['eligible_fields'] += 1
        counts['correct_fields'] += int(equal)
        counts['populated_fields'] += int(actual is not None)
        findings.append({'path': path, 'expected': expected, 'actual': actual, 'correct': equal})
    for key in HEADERS:
        score('/' + key, review['fields'][key], candidate.get(key))
    for key in TOTALS:
        score('/totals/' + key, review['totals'][key], candidate['totals'].get(key), True)
    missing = 0
    for index, row in enumerate(review['rows']):
        predicted = row['candidate_index']
        missing += int(predicted is None)
        for key in ITEMS:
            actual = None if predicted is None else candidate['line_items'][predicted].get(key)
            score('/reference_rows/' + str(index) + '/' + key, row['fields'][key], actual, key != 'raw_text')
    n = counts['eligible_fields']
    matched = len(review['rows']) - missing
    source_rows, candidate_rows = len(review['rows']), len(candidate['line_items'])
    return {'kind': 'independent_field_accuracy', **counts,
            'field_accuracy': counts['correct_fields'] / n if n else None,
            'prediction_coverage': counts['populated_fields'] / n if n else None,
            'rows_complete': review['rows_complete'], 'reference_rows': len(review['rows']),
            'missing_rows': missing, 'spurious_rows': len(review['spurious_candidate_rows']),
            'row_recall': matched / source_rows if review['rows_complete'] and source_rows else None,
            'row_precision': matched / candidate_rows if review['rows_complete'] and candidate_rows else None,
            'findings': findings, 'schema_validity': 'not_measured_here',
            'arithmetic_consistency': 'not_measured_here'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'append', 'evaluate'))
    parser.add_argument('--image', required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--review')
    parser.add_argument('--database')
    parser.add_argument('--output')
    args = parser.parse_args()
    if args.action == 'prepare':
        result = prepare(args.image, args.candidate)
    else:
        if not args.review:
            parser.error('--review required')
        review = json.loads(Path(args.review).read_text(encoding='utf-8-sig'))
        if review['image_sha256'] != digest(args.image) or review['candidate_sha256'] != digest(args.candidate):
            raise ValueError('Image/candidate hash mismatch')
        if args.action == 'append':
            if not args.database:
                parser.error('--database required')
            result = {'review_id': append_review(args.database, review, args.image, args.candidate)}
        else:
            result = evaluate(review, json.loads(Path(args.candidate).read_text(encoding='utf-8-sig')))
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        with Path(args.output).open('x', encoding='utf-8') as stream:
            stream.write(text + '\n')
    else:
        print(text)


if __name__ == '__main__':
    main()
