"""Extraction backends for the end-to-end demo.

The project design puts a schema-constrained LLM in this slot. No unattended LLM is
provisioned (see Context/STATUS.md), so the demo ships two interchangeable backends:

* ``RulesExtractor``   - deterministic, offline, rule-based STAND-IN. Reads only literal
  OCR text, never infers a value with arithmetic, and refuses to assign ambiguous rows.
* ``CommandExtractor`` - pipes the project's real extraction prompt to any external
  command (for example a local LLM CLI) and strictly validates the JSON it prints.

Both return a contract-v1 record. The unchanged ``services/document_pipeline/contract.py``
then checks structure, literal evidence and arithmetic. Nothing here is a verifier.
"""
import json
import re
import subprocess

NUM = r'(?<![\w.,])\d[\d,]*(?:\.\d+)?(?![\w])'
NUM_RE = re.compile(NUM)
CURRENCY_RE = re.compile(r'(?<![A-Za-z])(Tk|BDT|USD|INR|Rs|\$)(?![A-Za-z])')
ID = r'[A-Z]{1,6}-?\d{2,}'
DOC_NO = [
    re.compile(r'(?:PO|Order|Invoice|Challan|DN|CC|Receipt|Rcpt|Delivery)\s*(?:No|Number|#)\.?\s*:?\s*(' + ID + ')', re.I),
    re.compile(r'(?<![A-Za-z])No\.?\s*:\s*(' + ID + ')'),
]
DATE_RE = re.compile(r'(?:Order\s+|Challan\s+|Invoice\s+)?Date\s*:?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})', re.I)
TOTAL_LINE = re.compile(r'^\W*(sub\s*-?\s*total|grand\s+total|total|vat|tax|discount)\b[^\d\n]*?(' + NUM + ')', re.I)
HEADER_LINE = re.compile(r'\b(qty|quantity|oty)\b.*\b(price|rate|amount|total)\b|\b(item|description|particulars)\b.*\b(qty|quantity)\b', re.I)
JUNK = re.compile(r'^[\s|@_:;,.~"\'`*-]+|[\s|@_:;,.~"\'`*-]+$')


def _clean_desc(text):
    text = re.sub(r'^[\W_]*\d{1,2}\s*[.)|]\s+', '', text)  # leading row serial like "1. "
    return JUNK.sub('', text)


def _row(line):
    """Return (description, [(token, start, end)]) for a candidate item row, or None."""
    tokens = [(m.group(0), m.start(), m.end()) for m in NUM_RE.finditer(line)]
    if not tokens:
        return None
    first = tokens[0][1]
    desc = _clean_desc(line[:first].replace('|', ' '))
    if len(re.findall(r'[A-Za-z]', desc)) < 3:
        return None
    return desc, tokens


class RulesExtractor:
    name = 'rules-standin'
    description = ('Deterministic rule-based stand-in for the LLM extraction stage. '
                   'Literal OCR evidence only; ambiguous rows are left unassigned and flagged.')

    def extract(self, document_type, ocr_text, prompt=None):
        record = {'schema_version': '1.0', 'document_type': document_type, 'document_number': None,
                  'date': None, 'currency': None, 'line_items': [],
                  'totals': {'subtotal': None, 'tax': None, 'discount': None, 'grand_total': None},
                  'evidence': {}, 'uncertainties': [], 'corrections': []}
        ev = record['evidence']
        for rx in DOC_NO:
            m = rx.search(ocr_text)
            if m:
                record['document_number'] = m.group(1)
                ev['/document_number'] = ocr_text[m.start():m.end()]
                break
        m = DATE_RE.search(ocr_text)
        if m:
            record['date'] = m.group(1)
            ev['/date'] = ocr_text[m.start():m.end()]
        m = CURRENCY_RE.search(ocr_text)
        if m:
            line = next((l for l in ocr_text.splitlines() if m.group(0) in l), m.group(0))
            record['currency'] = m.group(1)
            ev['/currency'] = line.strip()
        in_table = False
        for raw in ocr_text.splitlines():
            line = raw.strip()
            if not line:
                continue
            if HEADER_LINE.search(line):
                in_table = True
                continue
            tm = TOTAL_LINE.match(line)
            if tm:
                key = re.sub(r'[\s-]', '', tm.group(1).lower())
                field = {'subtotal': 'subtotal', 'grandtotal': 'grand_total', 'total': 'grand_total',
                         'vat': 'tax', 'tax': 'tax', 'discount': 'discount'}[key]
                if record['totals'][field] is None:
                    token = tm.group(2)
                    record['totals'][field] = token.replace(',', '')
                    ev['/totals/' + field] = line[:tm.end()].strip()
                in_table = False
                continue
            parsed = _row(line)
            if parsed is None:
                continue
            desc, tokens = parsed
            # Only table-like rows: inside a table, or thermal "qty x price = total" rows.
            thermal = re.search(r'\d\s*[x×]\s*[\d,.]+\s*=\s*[\d,.]+', line)
            if not in_table and not thermal:
                continue
            idx = len(record['line_items'])
            row = {'raw_text': desc, 'quantity': None, 'unit_price': None, 'line_total': None}
            start = line.find(desc[:3]) if desc[:3] in line else 0
            def quote(tok):
                return line[start:tok[2]].strip()
            nums = tokens
            if len(nums) == 1 or len(nums) == 3:
                row['quantity'] = nums[0][0].replace(',', '')
                ev[f'/line_items/{idx}/quantity'] = quote(nums[0])
            if len(nums) == 3:
                row['unit_price'] = nums[1][0].replace(',', '')
                row['line_total'] = nums[2][0].replace(',', '')
                ev[f'/line_items/{idx}/unit_price'] = quote(nums[1])
                ev[f'/line_items/{idx}/line_total'] = quote(nums[2])
            if len(nums) not in (1, 3):
                record['uncertainties'].append(
                    f'Row "{desc}": {len(nums)} numeric tokens; amounts not assigned rather than guessed')
                if len(nums):
                    row['quantity'] = None
            if desc in line:
                ev[f'/line_items/{idx}/raw_text'] = desc
            record['line_items'].append(row)
        return record


class CommandExtractor:
    name = 'external-command'
    description = 'Pipes the project extraction prompt to an external command; its stdout must be one JSON object.'

    def __init__(self, command, timeout=180):
        self.command = command
        self.timeout = timeout

    def extract(self, document_type, ocr_text, prompt=None):
        if not prompt:
            raise ValueError('CommandExtractor needs the extraction prompt')
        proc = subprocess.run(self.command, input=prompt.encode('utf-8'), capture_output=True,
                              timeout=self.timeout, shell=isinstance(self.command, str))
        if proc.returncode:
            raise RuntimeError('Extractor command failed: ' + proc.stderr.decode('utf-8', 'replace')[:300])
        text = proc.stdout.decode('utf-8', 'replace').strip()
        start, end = text.find('{'), text.rfind('}')
        if start < 0 or end < start:
            raise ValueError('Extractor command printed no JSON object')
        return json.loads(text[start:end + 1])


def make_extractor(command=None):
    return CommandExtractor(command) if command else RulesExtractor()
