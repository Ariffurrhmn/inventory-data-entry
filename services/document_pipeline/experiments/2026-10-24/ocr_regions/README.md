# Bounded region OCR diagnostic — 2026-10-24

Two exposed development images, six configurations each. Comparison uses AI visual observations (`human_verified=false`), not independent truth, accuracy or a new benchmark. No source images, canonical OCR, classifier code, annotations or models changed.

## Findings

Explicit cell-interior crops let local Tesseract recover both purchase-order numeric rows and all five delivery-note quantities. Exact best-candidate OCR:

Purchase order:

```text
Miniket Rice 25kg 24 Tk 1,850 Tk 44,400
Onion 1kg 20 Tk 65 Tk 1,300
```

Delivery note:

```text
1 Mustard Oil 1L | 6

2 Milk Powder 500g 20
3 Detergent 5008 . 12
4 Onion 1kg = 12
5 Salt 1kg a 2
```

The quantities agree with unverified visual observations (6, 20, 12, 12, 2), but `Detergent 5008` remains an OCR error relative to observed `500g`. No visual correction entered the saved OCR. Printed PO commas remain; the strict extraction contract must not silently normalize evidence.

## All candidates

| Image | Configuration | OCR seconds | Diagnostic observation |
|---|---|---:|---|
| 76cc99d39da4 | table_gray_psm6 | 0.8132 | Only EE; rows lost. |
| 76cc99d39da4 | table_normalized_psm6 | 1.6396 | Both numeric rows, with grid noise. |
| 76cc99d39da4 | table_normalized_psm11 | 1.3881 | Fragments; 1,850 split as 1, 850. |
| 76cc99d39da4 | table_binary190_psm6 | 1.0727 | Both numeric rows; grid/currency noise. |
| 76cc99d39da4 | row_interiors_psm6 | 0.5775 | Both rows; vertical-border artifacts. |
| 76cc99d39da4 | cell_interiors_psm6 | 0.5633 | Clean two rows with all six row numbers. |
| f9918570b903 | table_gray_psm6 | 0.5990 | Empty OCR. |
| f9918570b903 | table_normalized_psm6 | 1.8783 | Corrupted fragments; quantities lost. |
| f9918570b903 | table_normalized_psm11 | 1.7385 | Fragments; assignments unreliable. |
| f9918570b903 | table_binary190_psm6 | 1.0572 | Corrupted fragments; rows unusable. |
| f9918570b903 | row_interiors_psm6 | 1.0402 | First quantity 6 lost; later quantities visible. |
| f9918570b903 | cell_interiors_psm6 | 0.9736 | All five row quantities; Detergent 500g misread 5008. |

Total successful-run OCR subprocess time: 13.3412 seconds. Excludes setup, preprocessing, disk work and extraction.

## Reproduce and evidence

Use the Python interpreter from `classifier/engine/runtime.local.json`, Tesseract on PATH and the existing `classifier/engine/.cache/tessdata/eng.traineddata`. Run `run_region_ocr.py --output <a-new-directory>`; existing output directories are refused. Pillow and NumPy are required.

`results-run2/manifest.json` records source hashes, traineddata hash, script hash, Tesseract version, exact commands, manually chosen crop coordinates, exact OCR, stderr and timings. All twelve PNG/TXT/TSV triplets and source/script hashes were checked. TSV boxes refer to transformed crop/montage pixels, not original-page coordinates. Numeric-token presence is only a comparison against unverified AI observations; it cannot establish assignment.

`results-run1/` preserves twelve initial invocations with absent txt/tsv configuration files: fallback TXT existed, TSV did not, and warning stderr is retained. `results-run2/` repeats the identical twelve configurations with explicit create_txt/create_tsv flags; OCR strings match exactly. There were twelve distinct candidate configurations, each executed twice. PSM11 estimating-resolution/diacritic messages in successful-run stderr are retained. An earlier setup-only root-path mistake created an empty `results/` directory before OCR began.

## Limits and next roadblock

Successful crops use image-specific manually selected table, row and cell rectangles. The pixels are readable once structure is supplied; automatic table/cell detection and original-coordinate mapping are unimplemented. Whole-table preprocessing remained inadequate for the delivery note. This is no generic recovery/accuracy claim or classifier promotion. Next work needs image-independent region detection and independent validation. Agent extraction remains an explicit development handoff; no callable LLM was added to the gateway.
