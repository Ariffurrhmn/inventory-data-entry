"""Copy the curated demo documents into full_demo/shelf/ and write shelf.json.

The shelf is CURATED for a walkthrough: it deliberately includes clean passes, an injected
arithmetic error, a classifier miss and an error the verifier cannot catch. It is not a
sample for estimating accuracy; see data/evaluation.json for the full 86-document measurement.
"""
import json, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SYN = ROOT / 'synthetic_dataset'
DEMO = ROOT / 'classifier' / 'demo'

SYNTHETIC = [
    ('purchase_order_01', 'Purchase order - clean print', 'clean',
     'Heading rule fires, every field is read, and the line totals add up to the printed grand total. The happy path (under the strict contract it still waits for a printed subtotal and tax).'),
    ('customer_copy_02', 'Customer copy - clean print', 'clean',
     'A "CUSTOMER COPY" heading decides the class even though the layout looks like an invoice.'),
    ('delivery_note_06', 'Delivery note - clean print', 'clean',
     'Quantity table with prices; routed by its printed heading.'),
    ('purchase_order_03', 'Purchase order - printed total is wrong', 'caught',
     'The document itself contains an arithmetic inconsistency (injected by the generator). The checks catch it and flag the record.'),
    ('customer_copy_09', 'Customer copy - printed total is wrong', 'caught',
     'Same idea on another document type: a line total that does not equal quantity x unit price.'),
    ('purchase_order_09', 'Purchase order - OCR misreads an item name', 'limit',
     'LIMITATION: OCR reads "5kg" as "S5kg" in an item name. The numbers still add up, so nothing is flagged. Arithmetic cannot catch a wrong text value.'),
    ('receipt_13', 'Thermal receipt - routed correctly', 'limit',
     'Receipts have no heading rule, so the trained model decides (correctly here). OCR reads "1L" as "iL" in an item name, which arithmetic cannot catch.'),
    ('receipt_20', 'Thermal receipt - classifier miss', 'miss',
     'LIMITATION: this receipt is routed to delivery_note (receipts rely on the weaker learned model). Its arithmetic error is still caught, but the wrong type would reach the ERP.'),
]
PHOTOS = [
    ('76cc99d39da4', 'Phone photo - purchase request', 'photo',
     'Real camera noise and shadows. The table rows are too noisy to read reliably, so quantities stay empty rather than guessed, and the total "Tk 45,700" has a thousands comma that fails the literal-evidence rule. Flagged for review.'),
    ('5dffabcb47cb', 'Phone photo - thermal retail receipt', 'photo',
     'Hard photo with little readable text. The system finds no item rows and does not invent any, so it is flagged.'),
    ('f9918570b903', 'Phone photo - delivery challan', 'photo',
     'The "Challan" heading routes it correctly, but OCR garbles the table. No rows are extracted, and the record is flagged.'),
    ('e396ade11def', 'Phone photo - office copy invoice', 'photo',
     'An "OFFICE COPY" heading routes this to customer_copy. Noisy rows then fail the literal-evidence check, so it is flagged.'),
    ('cdd7aaa9004d', 'Phone photo - faint copy stamp', 'photo',
     'A faint stamp. The project\'s recorded evaluation mispredicted this one; with this machine\'s OCR data it routes correctly. Treat that as one observation, not a fix. Rows are unreadable, so it is flagged.'),
]


def main():
    out = HERE / 'shelf'
    out.mkdir(exist_ok=True)
    items = []
    for name, title, kind, note in SYNTHETIC:
        shutil.copyfile(SYN / 'images' / (name + '.jpg'), out / (name + '.jpg'))
        truth = json.loads((SYN / 'json' / (name + '.json')).read_text())
        items.append({'id': name, 'title': title, 'kind': kind, 'image': name + '.jpg', 'note': note,
                      'group': 'Clean synthetic documents',
                      'provenance': 'Synthetic document rendered from HTML (synthetic_dataset/). Fabricated data.',
                      'expected_type': truth['document_type'], 'truth': truth})
    for name, title, kind, note in PHOTOS:
        shutil.copyfile(DEMO / 'images' / (name + '.jpg'), out / (name + '.jpg'))
        manifest = {m['id']: m for m in json.loads((DEMO / 'manifest.json').read_text())}
        items.append({'id': name, 'title': title, 'kind': kind, 'image': name + '.jpg', 'note': note,
                      'group': 'Phone photos of printed documents',
                      'provenance': manifest[name]['provenance'],
                      'expected_type': manifest[name]['expected_label'], 'truth': None})
    (out / 'shelf.json').write_text(json.dumps(items, indent=1))
    print(len(items), 'shelf documents')


if __name__ == '__main__':
    main()
