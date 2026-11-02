---
language:
- en
- fr
license: apache-2.0
size_categories:
- 100K<n<1M
task_categories:
- document-question-answering
- image-to-text
- token-classification
- text-classification
- text-generation
pretty_name: Company Documents v2
tags:
- finance
- document-ai
- synthetic
- invoices
- pdf
- ocr
- key-information-extraction
configs:
- config_name: all
  default: true
  data_files:
  - split: train
    path:
    - data/account_statement/train-*.parquet
    - data/credit_note/train-*.parquet
    - data/employment_certificate/train-*.parquet
    - data/goods_received_note/train-*.parquet
    - data/inventory_report/train-*.parquet
    - data/invoice/train-*.parquet
    - data/packing_slip/train-*.parquet
    - data/payslip/train-*.parquet
    - data/purchase_order/train-*.parquet
    - data/quote/train-*.parquet
    - data/receipt/train-*.parquet
    - data/shipping_order/train-*.parquet
    - data/work_order/train-*.parquet
  - split: validation
    path:
    - data/account_statement/validation-*.parquet
    - data/credit_note/validation-*.parquet
    - data/employment_certificate/validation-*.parquet
    - data/goods_received_note/validation-*.parquet
    - data/inventory_report/validation-*.parquet
    - data/invoice/validation-*.parquet
    - data/packing_slip/validation-*.parquet
    - data/payslip/validation-*.parquet
    - data/purchase_order/validation-*.parquet
    - data/quote/validation-*.parquet
    - data/receipt/validation-*.parquet
    - data/shipping_order/validation-*.parquet
    - data/work_order/validation-*.parquet
  - split: test
    path:
    - data/account_statement/test-*.parquet
    - data/credit_note/test-*.parquet
    - data/employment_certificate/test-*.parquet
    - data/goods_received_note/test-*.parquet
    - data/inventory_report/test-*.parquet
    - data/invoice/test-*.parquet
    - data/packing_slip/test-*.parquet
    - data/payslip/test-*.parquet
    - data/purchase_order/test-*.parquet
    - data/quote/test-*.parquet
    - data/receipt/test-*.parquet
    - data/shipping_order/test-*.parquet
    - data/work_order/test-*.parquet
- config_name: account_statement
  data_files:
  - split: train
    path: data/account_statement/train-*.parquet
  - split: validation
    path: data/account_statement/validation-*.parquet
  - split: test
    path: data/account_statement/test-*.parquet
- config_name: credit_note
  data_files:
  - split: train
    path: data/credit_note/train-*.parquet
  - split: validation
    path: data/credit_note/validation-*.parquet
  - split: test
    path: data/credit_note/test-*.parquet
- config_name: employment_certificate
  data_files:
  - split: train
    path: data/employment_certificate/train-*.parquet
  - split: validation
    path: data/employment_certificate/validation-*.parquet
  - split: test
    path: data/employment_certificate/test-*.parquet
- config_name: goods_received_note
  data_files:
  - split: train
    path: data/goods_received_note/train-*.parquet
  - split: validation
    path: data/goods_received_note/validation-*.parquet
  - split: test
    path: data/goods_received_note/test-*.parquet
- config_name: inventory_report
  data_files:
  - split: train
    path: data/inventory_report/train-*.parquet
  - split: validation
    path: data/inventory_report/validation-*.parquet
  - split: test
    path: data/inventory_report/test-*.parquet
- config_name: invoice
  data_files:
  - split: train
    path: data/invoice/train-*.parquet
  - split: validation
    path: data/invoice/validation-*.parquet
  - split: test
    path: data/invoice/test-*.parquet
- config_name: packing_slip
  data_files:
  - split: train
    path: data/packing_slip/train-*.parquet
  - split: validation
    path: data/packing_slip/validation-*.parquet
  - split: test
    path: data/packing_slip/test-*.parquet
- config_name: payslip
  data_files:
  - split: train
    path: data/payslip/train-*.parquet
  - split: validation
    path: data/payslip/validation-*.parquet
  - split: test
    path: data/payslip/test-*.parquet
- config_name: purchase_order
  data_files:
  - split: train
    path: data/purchase_order/train-*.parquet
  - split: validation
    path: data/purchase_order/validation-*.parquet
  - split: test
    path: data/purchase_order/test-*.parquet
- config_name: quote
  data_files:
  - split: train
    path: data/quote/train-*.parquet
  - split: validation
    path: data/quote/validation-*.parquet
  - split: test
    path: data/quote/test-*.parquet
- config_name: receipt
  data_files:
  - split: train
    path: data/receipt/train-*.parquet
  - split: validation
    path: data/receipt/validation-*.parquet
  - split: test
    path: data/receipt/test-*.parquet
- config_name: shipping_order
  data_files:
  - split: train
    path: data/shipping_order/train-*.parquet
  - split: validation
    path: data/shipping_order/validation-*.parquet
  - split: test
    path: data/shipping_order/test-*.parquet
- config_name: work_order
  data_files:
  - split: train
    path: data/work_order/train-*.parquet
  - split: validation
    path: data/work_order/validation-*.parquet
  - split: test
    path: data/work_order/test-*.parquet
- config_name: scans
  data_files:
  - split: train
    path:
    - scans/account_statement/train-*.parquet
    - scans/credit_note/train-*.parquet
    - scans/employment_certificate/train-*.parquet
    - scans/goods_received_note/train-*.parquet
    - scans/inventory_report/train-*.parquet
    - scans/invoice/train-*.parquet
    - scans/packing_slip/train-*.parquet
    - scans/payslip/train-*.parquet
    - scans/purchase_order/train-*.parquet
    - scans/quote/train-*.parquet
    - scans/receipt/train-*.parquet
    - scans/shipping_order/train-*.parquet
    - scans/work_order/train-*.parquet
  - split: validation
    path:
    - scans/account_statement/validation-*.parquet
    - scans/credit_note/validation-*.parquet
    - scans/employment_certificate/validation-*.parquet
    - scans/goods_received_note/validation-*.parquet
    - scans/inventory_report/validation-*.parquet
    - scans/invoice/validation-*.parquet
    - scans/packing_slip/validation-*.parquet
    - scans/payslip/validation-*.parquet
    - scans/purchase_order/validation-*.parquet
    - scans/quote/validation-*.parquet
    - scans/receipt/validation-*.parquet
    - scans/shipping_order/validation-*.parquet
    - scans/work_order/validation-*.parquet
  - split: test
    path:
    - scans/account_statement/test-*.parquet
    - scans/credit_note/test-*.parquet
    - scans/employment_certificate/test-*.parquet
    - scans/goods_received_note/test-*.parquet
    - scans/inventory_report/test-*.parquet
    - scans/invoice/test-*.parquet
    - scans/packing_slip/test-*.parquet
    - scans/payslip/test-*.parquet
    - scans/purchase_order/test-*.parquet
    - scans/quote/test-*.parquet
    - scans/receipt/test-*.parquet
    - scans/shipping_order/test-*.parquet
    - scans/work_order/test-*.parquet
---

# Company Documents v2

**Generation complete:** all 13 document types have completed export and upload checkpoints.

Synthetic, born-digital business documents rendered from four open sample databases, with exact gold
labels: 353,580 PDFs (404,514 pages) of 13 document types in
English and French, issued by 60 synthetic companies,
each with its own letterhead, numbering and wording. Successor of
[CompanyDocuments](https://huggingface.co/datasets/AyoubChLin/CompanyDocuments) (2,677 PDFs, 4 types).

## Dataset overview

| property | value |
|---|---|
| PDF documents | 353,580 |
| PDF pages | 404,514 |
| Document types | 13 |
| Synthetic issuing companies | 60 |
| Languages | English / French |
| Degraded scan/photo page images | 120,523 |
| Export format | parquet |
| Split unit | issuing company, grouped by sector |

## Intended uses

Document classification, OCR evaluation, key information extraction, layout-aware field extraction,
and document question answering using the gold fields to construct task-specific examples.
The dataset provides document text, structured fields and coordinates; it does not include a separate
set of question-answer pairs.

## Subsets

Pick a document type, or `all`. Every subset has the same train / validation / test split.

| subset | document | documents | train | validation | test | sources |
|---|---|---|---|---|---|---|
| `all` (default) | every type below | 353,580 | 259,497 | 47,114 | 46,969 | all four |
| `account_statement` | a customer's invoices and payments over a period, running balance and aging | 728 | 522 | 99 | 107 | adventureworks, northwind |
| `credit_note` | credit against an invoice, with a reason (damaged, wrong item, price...) | 47,747 | 35,107 | 6,337 | 6,303 | adventureworks, northwind |
| `employment_certificate` | letter certifying an employee's job title, department and hire date | 290 | 202 | 43 | 45 | adventureworks |
| `goods_received_note` | delivery check against a purchase order: ordered, received, accepted, rejected | 3,689 | 2,667 | 512 | 510 | adventureworks |
| `inventory_report` | stock on hand per product, with value and reorder status | 51 | 35 | 6 | 10 | adventureworks, northwind |
| `invoice` | sales invoice: line items, discounts, tax, totals, payment terms | 48,158 | 35,342 | 6,446 | 6,370 | adventureworks, chinook, northwind |
| `packing_slip` | items packed for a shipment: ordered vs shipped quantities | 47,740 | 35,040 | 6,456 | 6,244 | adventureworks, northwind |
| `payslip` | employee pay for a period: earnings, deductions, net pay | 290 | 231 | 30 | 29 | adventureworks |
| `purchase_order` | order the issuer places with a vendor | 50,313 | 36,908 | 6,598 | 6,807 | adventureworks, northwind |
| `quote` | price quotation with validity and lead time | 47,746 | 35,004 | 6,313 | 6,429 | adventureworks, northwind |
| `receipt` | proof of a paid retail transaction (A5) | 16,456 | 12,105 | 2,218 | 2,133 | chinook, sakila |
| `shipping_order` | instruction to ship an order: items, weights, consignee, carrier | 47,747 | 35,182 | 6,274 | 6,291 | adventureworks, northwind |
| `work_order` | production order: routing operations, planned vs actual cost | 42,625 | 31,152 | 5,782 | 5,691 | adventureworks |
| `scans` | degraded page images of a sample of the documents | 120,523 pages | 88,799 | 15,829 | 15,895 | |

## Quick start

```python
import json
from datasets import load_dataset

documents = load_dataset("AyoubChLin/Company-document-dataset-v2", "invoice", split="train")
row = documents[0]
row["pdf"]                            # pdfplumber.PDF
json.loads(row["extracted_data"])     # the gold fields
```

Use `"all"` to load every document type. For a large subset, pass `streaming=True` to
`load_dataset` and read examples with `next(iter(documents))` to avoid downloading the entire subset.

## Scans

120,523 degraded page images (scan and photo profiles) of a sample of the documents, with the gold-field
boxes moved into image pixels:

```python
scans = load_dataset("AyoubChLin/Company-document-dataset-v2", "scans", split="test")
scans[0]["image"], json.loads(scans[0]["boxes"])
```

## Files

```
data/<type>/<split>-NNNNN.parquet    one row per PDF, the PDF embedded (the columns below)
scans/<type>/<split>-NNNNN.parquet   one row per degraded page image
stats.json                           counts per split, type, source, locale, layout; companies per split
licenses/                            source database licenses
```

## Splits

Splits are **by issuing company** (per sector): validation and test documents come from companies whose
issuing company is absent from training. Source databases, products, counterparties, layout families
and themes can occur across splits; this is an issuer-held-out split, not a source-held-out split.

| split | documents | companies | scan pages |
|---|---|---|---|
| train | 259,497 | 44 | 88,799 |
| validation | 47,114 | 8 | 15,829 |
| test | 46,969 | 8 | 15,895 |

## Columns

One row per PDF (`all` and every document-type subset):

| column | content |
|---|---|
| `pdf` | the PDF itself (the viewer shows its first page; `datasets` opens it with pdfplumber; raw bytes with `.cast_column("pdf", Pdf(decode=False))`) |
| `file_name` | `<type>/<doc_id>.pdf` |
| `doc_id`, `split`, `document_type` | identifiers |
| `source`, `variant` | source database and document variant (`<type>.<source>`) |
| `company`, `company_name`, `company_sector`, `company_country`, `company_city`, `company_tax_id`, `company_locale`, `company_currency` | the issuing company |
| `number`, `issue_date`, `currency`, `total`, `items_count`, `counterparty_role`, `counterparty_name` | key gold values as plain columns |
| `layout`, `theme`, `locale`, `pages` | letterhead layout, color theme, language, page count |
| `extracted_data` | all gold fields as JSON |
| `file_content` | text extracted from the PDF, in reading order |
| `options` | content variation drawn for the document (JSON) |
| `rendered` | each gold field as printed in the PDF (JSON) |
| `boxes` | where each gold field is printed (JSON: field path -> list of page + bbox in PDF points) |
| `words` | every word of the PDF with its page and bbox (JSON) |

`scans` subset, one row per degraded page image (profiles `scan` and `photo`: skew, blur, noise, paper tint,
lighting, JPEG):

| column | content |
|---|---|
| `image` | the page image |
| `doc_id`, `split`, `document_type`, `page`, `profile` | identifiers; join to the documents on `doc_id` |
| `width`, `height` | image size in pixels |
| `params` | degradation parameters (JSON) |
| `words`, `boxes` | words and gold-field boxes moved into image pixels (JSON) |

## Sources

| source | documents |
|---|---|
| adventureworks | 208,870 |
| northwind | 127,842 |
| sakila | 16,044 |
| chinook | 824 |

Northwind (food wholesale), AdventureWorks (bicycle manufacturer: sales, purchasing, production, HR),
Chinook (online music store), Sakila (video rental, dates shifted +19 years). Issuers are synthetic;
counterparties, products, quantities and prices come from the databases.

| language | documents |
|---|---|
| English | 203,657 |
| French | 149,923 |

## Guarantees

Every document passed a self-check: the checked gold values are present in the PDF text and the arithmetic
holds (line totals, tax, totals, running balances, aging, payroll, received vs accepted). Money is computed
with Decimal and half-up rounding; currencies are converted once from the source (USD).

## Limitations

- These are synthetic documents derived from sample databases. Their layouts, wording and simulated
  degradation do not cover the full variety of real business documents or camera captures.
- Document types are imbalanced; use the per-type counts when selecting training data and reporting
  evaluation results. Some types contain only a small number of examples.
- Scan rows represent pages of sampled PDFs, not additional independent business transactions.
  Keep scans with their parent document's split when constructing an evaluation dataset.
- Gold fields and word boxes come from the generation and PDF extraction pipeline. Arithmetic and
  text checks do not establish that every annotation or reading-order decision is error-free.
- The same underlying source records can support multiple document types. Holding out issuing
  companies does not guarantee that all business entities or transaction content are unseen.

## Licenses

Code and generated documents: Apache-2.0. Source data: Northwind (MIT), AdventureWorks (MIT),
Chinook (MIT), Sakila (BSD-2); see `licenses/`.

## Citation

Created by **Cherguelaine Ayoub**. If you use this dataset, please cite:

```bibtex
@misc{cherguelaine2026companydocumentsv2,
  author = {Cherguelaine, Ayoub},
  title = {Company Documents v2: Synthetic Business Documents},
  year = {2026},
  url = {https://github.com/AyoubCherguelaine/Company-document-dataset-v2}
}
```

## Reproduce

Generator source code: [Company-document-dataset-v2](https://github.com/AyoubCherguelaine/Company-document-dataset-v2).
To generate the content locally from a Git checkout:

```bash
git clone https://github.com/AyoubCherguelaine/Company-document-dataset-v2.git
cd Company-document-dataset-v2
# Generate all source records and their scans locally.
python3 scripts/run_pipeline.py --all-records --stages venv download index companies texts generate augment --seed 42 --workers 8 --augment-fraction 0.3
# Export with the published dataset's company split seed.
./venv/bin/python -m docgen export output/v2 dataset/full-local --format parquet --seed 0
```

See the [repository README](https://github.com/AyoubCherguelaine/Company-document-dataset-v2#readme) for setup, configuration and full-dataset generation options.

Generated with the CompanyDocuments v2 generator (`docgen`) and this run config:

```yaml
{
  "run_name": "full",
  "seed": 42,
  "out_dir": "output/parts/<type>",
  "workers": 8,
  "fx": {
    "USD": "1",
    "EUR": "0.92",
    "GBP": "0.79"
  },
  "self_check": true,
  "boxes": true,
  "resume": true,
  "documents": [
    {
      "type": "account_statement",
      "count": "all"
    },
    {
      "type": "credit_note",
      "count": "all"
    },
    {
      "type": "employment_certificate",
      "count": "all"
    },
    {
      "type": "goods_received_note",
      "count": "all"
    },
    {
      "type": "inventory_report",
      "count": "all"
    },
    {
      "type": "invoice",
      "count": "all"
    },
    {
      "type": "packing_slip",
      "count": "all"
    },
    {
      "type": "payslip",
      "count": "all"
    },
    {
      "type": "purchase_order",
      "count": "all"
    },
    {
      "type": "quote",
      "count": "all"
    },
    {
      "type": "receipt",
      "count": "all"
    },
    {
      "type": "shipping_order",
      "count": "all"
    },
    {
      "type": "work_order",
      "count": "all"
    }
  ]
}
```
