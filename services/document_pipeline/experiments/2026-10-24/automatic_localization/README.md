# Automatic ruled-table localization — 2026-10-24

Working reusable development improvement, implemented in `services/document_pipeline/localization.py`. Local Pillow/NumPy/SciPy morphology plus Tesseract; no model download, paid API, image-specific coordinates, merchant strings, reference answers, classifier change, historical test image or annotation access. Seven manifest-guarded eligible development documents, including two beyond the five original demonstrations. These are exposed, adaptively reused development observations, **not field accuracy or localization accuracy**. Every candidate remains `human_verified=false`.

## What the detector does

EXIF orientation → uniform resize (long side at most 1400) → local illumination normalization → foreground threshold → directional dilation/closing to bridge slanted/dashed rules → horizontal/vertical morphological opening → connected rule components → projection bands → multirow/multicolumn grid → inset cell interiors → cell montage → actual local OCR. It retains headers and does not infer field roles. A second candidate searches deskew angles -4 to +4 degrees in half-degree steps. A separate full-image PSM11 candidate retains TSV word boxes and Tesseract line grouping; those groups do not establish a table.

Connected components are the contour-like region alternative available without OpenCV (not installed in this runtime). Deskew was actually executed, with scores preserved; it adds no recovered grid in final run6. Perspective rectification was not implemented or claimed: page/edge quadrilateral fitting is unreliable on dashed borders and curved phone pages, and this bounded improvement does not establish perspective-invariant localization. The source document remains the full EXIF-oriented page; no unsupported paper contour is substituted. Gross rotations outside the bounded search, borderless tables and complicated merged grids remain limitations.

`analyze(image_path, new_output_directory, tessdata_directory)` writes `result.json`, candidate masks/overlays, actual OCR PNG/TXT/TSV, exact subprocess commands/stderr/timing and an exact module source snapshot. It refuses an existing output directory. The layout contains working pixel boxes and an inverse affine using the actual rounded X/Y resize dimensions. Every montage cell carries an original EXIF-oriented source polygon. OCR TSV positions refer to doubled montage pixels: divide by `mapping_scale_to_ocr=2`, locate the montage cell, translate into its working cell and apply the saved affine. Resampling means this is a geometric mapping, not exact glyph segmentation. No coordinates from the old manual diagnostic enter this code.

## Measured final run6

| Development image | Automatic grid | Rows including header | Columns | Observed OCR outcome |
|---|---:|---:|---:|---|
| 76cc99d39da4 | 1 | 3 | 4 | Two complete numeric PO rows |
| f9918570b903 | 1 | 6 | 3 | Five descriptions and five quantities |
| 5dffabcb47cb | 0 | 0 | 0 | Explicit no-grid; primary OCR retained |
| e396ade11def | 0 | 0 | 0 | Explicit no-grid; primary OCR retained |
| cdd7aaa9004d | 1 | 4 | 4 | Three complete numeric rows; original classifier route retained |
| cc6e515ae67f (additional layout) | 0 | 0 | 0 | Explicit no-grid; OCR word-box fallback preserved |
| 398c6ef688e4 (additional layout) | 1 | 6 | 3 | Five description/quantity rows |

This is **4/7 documents producing a grid**, not a 57% detector accuracy measurement. No human reviewed table truth exists. Exact source hashes and development/historical split flags are in `run6/summary.json`. The runner checks eligible scope, train/val development membership and historical split != test **before opening each image**. It reads no held-out input. `run6/audit.json` verifies all seven image hashes, module/snapshot hashes, OCR image/text hashes, successful exit codes and TSV presence. Run6 took **79.2904 seconds** end to end for seven images, including deskew search and word-box OCR; eight grid OCR subprocesses used **6.445 seconds**. These are observations, not latency percentiles. It made 15 OCR subprocess calls (eight grid + seven word-box fallback).

Exact automatic PO region OCR:

```text
Item Qty Rate (Tk) Amount (Tk)
Miniket Rice 25kg 24 Tk 1,850 Tk 44,400
Onion 1kg 20 Tk 65 Tk 1,300
```

Exact automatic delivery-note region OCR:

```text
Si Item Description Qty.
1 Mustard Oil 1L 6
2 Milk Powder 500g 20
3 Detergent 500g 12
4 Onion 1kg 12
5 Salt 1kg 2
```

Compared with the saved manual `ocr_regions/results-run2` diagnostic, the automatic PO retains the same two numeric rows and automatic DN retains all five quantities. Automatic DN now reads `Detergent 500g` where the manual montage read `Detergent 5008`. These are actual unchanged Tesseract strings agreeing with earlier **unverified AI observations**, not measured correct fields or human truth. No OCR correction was applied. The extra DN OCR includes Soybean Oil 5L/12, Tea 400g/4, Salt 1kg/12, Hand Wash 200ml/1 and Exercise Book/3; these are candidate readings only.

## Failed alternatives preserved

All six runs are retained, with candidate masks, overlays, exact OCR and subprocess stderr. Initial runs changed a small set of generic morphology parameters using development inspection; this is adaptive method development.

- `run1`: thin-rule threshold190, directional opening without dashed closing. PO grid absent; DN misses the right boundary; faint copy extracts only quantity column; additional DN only three rows. `localization_run1.py` is a **reconstructed approximation**, not a byte-identical snapshot; initial recorded on-disk module hashes cannot fully reproduce that source revision. Do not treat it as a frozen exact-source experiment.
- `run2`: threshold215 and directional tolerance recover more boundaries and complete faint-copy rows. PO dashed grid absent; DN misreads outer quantities. `localization_run2.py` preserves the candidate source.
- `run3`: dashed closing and increased border inset recover the missing PO row, and all five DN quantities, but weak rule-support thresholds produce false row cuts through PO text and a spurious receipt grid. Failed OCR is preserved, not cleaned.
- `run4`: stronger rule coverage recovers both complete PO rows and removes the receipt grid; DN has a spurious one-row signature component.
- `run5`: require at least two rows and two columns; removes that signature component. This is the final OCR policy. `localization_run2.py` through `localization_run5.py` preserve successive source snapshots; earlier per-document hashes can reflect concurrent editing of the module on disk, so final run6 is the authoritative frozen reproduction.
- `run6`: same OCR as run5, corrected rounded-coordinate inverse affine, explicit source polygons and per-document exact source snapshots/traineddata hash/version. Every final snapshot matches the current integrated module. No candidate chosen by observed expected values.

Selection is fixed: first successful OCR candidate containing a geometric grid, in `[axis_grid, deskew_grid]` order. No grid retains primary OCR only. This preserves actual failure cases and avoids selecting whichever OCR happens to match known answers. Word-box results are saved but not silently appended to extraction evidence.

## Blinded extraction handoff

`blinded-region-inputs.json` supplies only the five original IDs, unchanged **predicted** document types and exact primary OCR plus automatically selected region OCR. It uses the shared `region_evidence.combine` delimiters; the fixed geometry-only selection is identical to the opt-in gateway adapter. The faint-copy classifier route remains purchase_order. `blinded-region-provenance.json` records exact primary/region/combined UTF-8 hashes, source image/result hashes and boundaries. It contains no expected field values. The extraction agent must not inspect other artifacts or use this report as an answer reference. Fresh agent prompts/responses/validation are handled separately by the parent experiment.

## Reproduce

Use Python from `classifier/engine/runtime.local.json` with Tesseract on PATH:

```text
python -m unittest discover -s services/document_pipeline -p test_localization.py
python services/document_pipeline/run_localization.py <new-image> --output <new-audit-directory>
python services/document_pipeline/experiments/2026-10-24/automatic_localization/run_experiment.py <new-run-directory-name>
python services/document_pipeline/experiments/2026-10-24/automatic_localization/audit_results.py run6
```

Four synthetic geometry tests pass: blank rejection, coordinate-free grid dimensions/montage mapping, affine identity/scaling and rounded-dimension mapping. These establish software behavior, not OCR accuracy. `prepare_blinded_inputs.py run6 <new-destination-directory>` recreates the isolated extraction inputs while refusing existing output files. The audit command prints by default; an optional second argument saves to a new report path with exclusive creation. Neither command overwrites saved evidence or edits datasets/annotations. Historical experiment runs and raw/manual artifacts are preserved.

Remaining localization roadblock: three of these seven layouts have no accepted ruled grid; borderless layouts, generic perspective correction, merged-cell topology and independently reviewed coordinate/field truth are not established. The useful integration is opt-in and never auto-accepts extraction or relabels a document.
