# Synthetic Document Dataset

**Stand-in for the real vendor/customer documents the project plans to collect.** Every document here is entirely fabricated — fake supplier names, fake shops, fake items, fake numbers — generated to match the shape of what real collection (per the report's §3.2 protocol) is expected to produce. This is **not** a replacement for that real corpus; it exists so the pipeline, schema, and evaluation harness can be built and exercised (per Chapter 3's iterative methodology) before real documents arrive, and so the schedule risk named in the report and SWOT study (corpus collection depending on outside shop cooperation) doesn't block everything else.

Do not present these as real evaluation results — they're illustrative, exactly like `docs/design/demo_worked_example.md`, just generated at dataset scale instead of hand-built one at a time.

## Contents

```
synthetic_dataset/
├── images/     120 JPEGs — the "photographed document" input (what the mobile app would capture)
├── html/       120 HTML source files used to render each image (kept for regeneration/editing)
├── json/       120 ground-truth JSON records — what the pipeline SHOULD extract, matching Table 3.4's schema
├── manifest.json   index of all 120 records with type/production-method/degradation/flag metadata
└── README.md   this file
```

## Composition

120 documents total — **30 per document type**, matching the report's Table 3.1 minimum-per-class target:

| Document type | Count | Production method mix | Flagged (`review_required: true`) |
|---|---|---|---|
| `purchase_order` | 30 | printed (majority), handwritten (some) | 4 |
| `receipt` | 30 | thermal (majority), printed (some) | 5 |
| `delivery_note` | 30 | handwritten (majority), printed (some), thermal (some) | 8 |
| `customer_copy` | 30 | printed (majority), thermal (some), handwritten (some) | 5 |

The printed/thermal/handwritten split per type follows the *natural prevalence* pattern from Table 3.1 (e.g. receipts are mostly thermal, purchase orders are mostly printed) rather than a forced even split, since the report explicitly warns that an artificially uniform corpus would misstate expected deployment accuracy.

**~36% of images (43/120)** carry a mild visual degradation — slight blur, a few degrees of rotation, or reduced contrast/fading — to stand in for the printed/thermal/handwritten *capture-condition* variety a real phone photo would have. Most images are left clean. See `degrade_type` in `manifest.json` for which.

**~18% of records (22/120)** are "flagged" cases: one line item has a deliberately injected arithmetic mismatch (the OCR-plausible error the report's worked example describes — e.g. a misread quantity), so `arithmetic_check: "failed"` and `review_required: true` on that record. This mirrors the clean-vs-flagged pairing used in `docs/design/demo_worked_example.md`, generated at scale instead of by hand.

## JSON schema

Each `json/<file>.json` follows the target schema from the report's Table 3.4 (`document_type`, `line_items[].{raw_text,quantity,unit_price,line_total,arithmetic_check}`, `grand_total`, `review_required`, etc.), plus a few extra fields useful for dataset bookkeeping only (`production_method`, `_synthetic: true`, `_note`). Strip the underscore-prefixed fields if feeding this directly into something that validates strictly against Table 3.4.

## How the images were made

1. `html/*.html` — each document is a randomized HTML/CSS template (three visual styles: clean printed invoice, monospace thermal-receipt strip, handwritten-style script font on ruled paper), built from a fixed seed so the generation is reproducible.
2. Rendered to PNG via headless Chrome (`chrome --headless=new --screenshot`), then auto-cropped to the document bounds.
3. Degradation (blur / rotation / contrast-fade) applied as a post-process with Pillow, then saved as JPEG at quality 88 to mimic a phone-camera capture rather than a lossless scan.

The generator tooling lives in `tools/`:
- `generate.js` (Node, no dependencies) — builds the 120 HTML templates + ground-truth JSON from a fixed seed.
- `shoot.sh` (bash) — batch-renders each HTML file to PNG via headless Chrome (`chrome --headless=new --screenshot`). Edit the `CHROME` path at the top if Chrome is installed somewhere other than `C:\Program Files\Google\Chrome\Application\chrome.exe`.
- `crop_and_degrade.py` (Python + Pillow) — auto-crops each PNG to the document bounds, applies the blur/rotation/fade degradation per `manifest.json`, and saves as JPEG.

To regenerate or extend the set (e.g. rebalance the type mix, change the flagged-record rate, add more degradation variety, or increase `PER_TYPE` in `generate.js`), run the three scripts in that order from this folder.

## Suggested uses

- Populate the pipeline-walkthrough and JSON-reveal demo slides (`docs/design/ui_demo_plan.md`) with more than one worked example.
- Smoke-test an actual OCR/extraction pipeline once implementation starts (498B), before real shop documents are available.
- Dry-run the evaluation harness (confusion matrix, arithmetic self-validation catch rate) described in the report's Chapter 4 framework against known ground truth.
- Sanity-check the JSON schema (Table 3.4) against a larger and more varied set of examples than the single hand-built one currently in the report.
