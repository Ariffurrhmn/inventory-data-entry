# Worked Example (Illustrative — No System Built Yet)

**This is a hypothetical walkthrough, not real output.** Nothing has been implemented yet. This example exists to make the pipeline concrete for the pre-defence presentation — every intermediate value below is hand-written to match the shape the report promises, not measured from a running system.

---

## Input: one fake supplier invoice

A plain-text sketch of what the source document looks like (in the real presentation, use a photo of any sample invoice/receipt — stock image or a real one from a shop, blurred/anonymized if needed):

```
        ACME BEVERAGE DISTRIBUTORS
        123 Market Road, Dhaka

        PURCHASE ORDER

Order Date: 2026-08-14          PO No: PO-88213
Bill To: Corner Store Mart

  Item                    Qty   Unit Price   Line Total
  ---------------------------------------------------
  Coca-Cola 500ml can      24      15.00        360.00
  Sprite 500ml can         12      15.00        180.00
  Mineral Water 1L          6      20.00        120.00
  ---------------------------------------------------
                                  Grand Total:   660.00
```

This is a **purchase order** — printed, clean layout, one supplier. Deliberately picked as the "easy" case for a first walkthrough; a thermal receipt or handwritten delivery note would be messier and is worth a second slide if time allows.

---

## Step-by-step through the 6 modules

### 1. Document Capture Module
- User photographs the invoice with the mobile app.
- Capture-quality checks pass (in-frame, no blur, no glare).
- Client generates idempotency key: `a1b2c3d4-...`
- **Output:** image + key, uploaded.

### 2. Character Recognition Module (OCR)
- Cloud OCR reads the image.
- Returns text tokens with bounding boxes, e.g.:
  - `"Coca-Cola 500ml can"` → box (120, 210, 340, 230), confidence 0.97
  - `"24"` → box (350, 210, 370, 230), confidence 0.94
  - `"360.00"` → box (520, 210, 570, 230), confidence 0.91
  - *(and so on for every token on the page)*

### 3. Document Structure and Type Recognition Module
- Classifies the page: `purchase_order`, confidence 0.96
- Locates regions: header block (supplier name, PO date/number), line-item table, totals block.

### 4. Schema-Constrained Extraction Module
- LLM reads the OCR text + regions, emits structured line items conforming to the schema.
- At this stage every field is just "extracted" — not yet verified.

### 5. Verification (arithmetic self-validation + confidence scoring)
- Check each line: `qty × unit_price == line_total`?
  - 24 × 15.00 = 360.00 ✓
  - 12 × 15.00 = 180.00 ✓
  - 6 × 20.00 = 120.00 ✓
- Check line totals sum to grand total: 360 + 180 + 120 = 660.00 ✓
- All checks pass, confidence high → `review_required: false`

**To make the demo interesting, show a second version where OCR misreads one field** — e.g. quantity "24" misread as "21":
  - 21 × 15.00 = 315.00 ≠ stated line total 360.00 → **arithmetic_check: failed**
  - `review_required: true`
  - This is the moment to say: *"this is what the system catches automatically — no human review queue, just a flag the consuming ERP sees."*

### 6. Digitization API Module
- Result stored against `submission_id`.
- Consuming ERP calls `GET /submissions/{id}` and receives the JSON below.

---

## Final output — clean case

```json
{
  "submission_id": "a1b2c3d4-5e6f-7890-abcd-ef1234567890",
  "document_type": "purchase_order",
  "document_type_confidence": 0.96,
  "supplier_name": "ACME Beverage Distributors",
  "document_date": "2026-08-14",
  "document_number": "PO-88213",
  "line_items": [
    {
      "raw_text": "Coca-Cola 500ml can",
      "quantity": 24,
      "unit_price": 15.00,
      "line_total": 360.00,
      "arithmetic_check": "passed"
    },
    {
      "raw_text": "Sprite 500ml can",
      "quantity": 12,
      "unit_price": 15.00,
      "line_total": 180.00,
      "arithmetic_check": "passed"
    },
    {
      "raw_text": "Mineral Water 1L",
      "quantity": 6,
      "unit_price": 20.00,
      "line_total": 120.00,
      "arithmetic_check": "passed"
    }
  ],
  "grand_total": 660.00,
  "review_required": false
}
```

## Final output — flagged case (OCR misread quantity)

```json
{
  "submission_id": "b2c3d4e5-6f70-8901-bcde-f21345678901",
  "document_type": "purchase_order",
  "document_type_confidence": 0.96,
  "supplier_name": "ACME Beverage Distributors",
  "document_date": "2026-08-14",
  "document_number": "PO-88213",
  "line_items": [
    {
      "raw_text": "Coca-Cola 500ml can",
      "quantity": 21,
      "unit_price": 15.00,
      "line_total": 360.00,
      "arithmetic_check": "failed"
    },
    {
      "raw_text": "Sprite 500ml can",
      "quantity": 12,
      "unit_price": 15.00,
      "line_total": 180.00,
      "arithmetic_check": "passed"
    },
    {
      "raw_text": "Mineral Water 1L",
      "quantity": 6,
      "unit_price": 20.00,
      "line_total": 120.00,
      "arithmetic_check": "passed"
    }
  ],
  "grand_total": 660.00,
  "review_required": true
}
```

**Note what's absent, deliberately:** no `standardized_item` field, no catalog match, no confirmation step. "Coca-Cola 500ml can" is returned exactly as printed — reconciling it against a shop's product catalog is the consuming ERP's job, not this system's.

---

## How to use this in the presentation

1. Show the fake invoice image.
2. Walk through the 6 module boxes (use Figure 4 from the report) one at a time, pointing at what changed.
3. Show the clean JSON output.
4. Show the flagged version side-by-side, highlighting `arithmetic_check: "failed"` and `review_required: true`.
5. Say explicitly: *"This is illustrative — hand-constructed to match our schema. No system has run yet. Real accuracy numbers come in Chapter 4."*
