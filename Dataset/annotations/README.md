# Image-linked text references

Prepared 2026-10-19 for the 140 included images in the frozen classifier split manifest.

These are **OCR-assisted, assistant-visually-reviewed reference transcriptions**, not independently human-verified gold annotations. Every included image was visually inspected; OCR errors were corrected against the image. Difficult handwriting, blur, masking, cropping and obscured regions are recorded with markers or uncertainty notes. Exact character accuracy has not been measured.

## Start here

- Open [review.html](review.html) for each prepared image alongside its transcription; filter by class.
- [index.csv](index.csv) maps source image, sample ID, class, split and JSON filename.
- [transcriptions/](transcriptions/) contains one UTF-8 JSON record per image.
- [transcriptions.jsonl](transcriptions.jsonl) contains the same 140 records, one per line.
- [review_queue.csv](review_queue.csv) lists explicit uncertainty notes and non-signature markers for focused checking. All records still benefit from an independent human audit.
- [validation_report.json](validation_report.json) records coverage and integrity checks.

## What each JSON contains

| Field | Meaning |
|---|---|
| sample_id | Existing stable classifier sample ID |
| source_image | Original relative path and SHA-256 recorded in the manifest |
| prepared_image | Decoded classifier image path and checked SHA-256 |
| classification | Existing class label and fixed train/val/test assignment |
| transcription.full_text | Reference text in approximate reading order |
| transcription.lines | Same text split on newlines |
| review | Assistant review status, notes, uncertainty descriptions; human_verified is false |
| provenance | OCR draft path, transcription method and date |
| usage | Restrictions for scoring and model input |

All paths inside records are relative to the project root. JSON filenames use the existing sample IDs, so source filenames can change without becoming model features.

## Transcription conventions

Record visible text, including document headings, stamps, handwriting, item descriptions, quantities, rates and totals. Preserve source spelling and printed numerical values; do not repair arithmetic or invent missing fields. Ignore photographic background objects. Whitespace is normalized and tables are linearized with header and row text; this is not a field-extraction or table-geometry annotation set.

Square-bracket markers describe non-literal or unreadable content: [signature], [illegible], [redacted], [masked], [cut off], [occluded], and [crossed out: visible text]. Consult review.uncertainties for best readings and source-specific limitations. Signatures are indicated rather than treated as reliable name transcriptions. Explicit separately printed names remain text. Masking counts are not guaranteed exact where marked uncertain.

For OCR scoring, define a normalization policy first. Exclude unresolved spans and annotation markers with their corresponding image/OCR spans; blindly deleting markers from reference text alone can still penalize OCR incorrectly. Reading order and table linearization also affect raw character/word error rates. Human audit is required before describing this as benchmark gold truth. Word coordinates/confidences in the OCR drafts have not been manually corrected.

## Safe classifier use

Use transcription.full_text as the reference text input, with class label supplied separately as the target. Exclude annotation markers/descriptions from model features. Never supply source path, filename, class label, split, review notes or metadata as input features. Fit vocabulary/features using the training split only; retain current family grouping and held-out splits. The test references are for held-out evaluation, not feature selection or tuning.

Reference-text classification would measure the classifier with corrected text. Deployment performance must later be measured with actual OCR output. Neither experiment was run during this annotation task.

## Maintenance

- ocr_drafts/ preserves the unreviewed Tesseract output, including word boxes/confidence; these files are not reference truth.
- review_actions.json records visual corrections by one-based row number in the current frozen splits.csv. Do not reorder/change that manifest and replay these actions.
- review_pages/ contains paired images used for visual inspection.
- services/document_classifier/reference_annotations.py export rebuilds JSONs and index from drafts plus review actions.
- services/document_classifier/finalize_annotations.py checks coverage, text, labels, splits and prepared image hashes, then rebuilds JSONL, review queue, report and review page.

Edit review_actions.json when correcting a transcription, then export and finalize. Editing an exported JSON alone will be overwritten on the next export. Record any future independent verification accurately; the current exporter sets human_verified=false.

Raw images, class labels, frozen splits and trained models were preserved. The five classifier improvement tasks remain paused; see Context/PENDING.md.

## Current corrected edition

Use [versions/utf8-v2/README.md](versions/utf8-v2/README.md) and its [review page](versions/utf8-v2/review.html) for new annotation work. This edition fixes a Windows UTF-8 decoding bug affecting 34 text records. Files at the original paths above remain preserved for reproducibility of earlier experiments. No new human verification or classifier evaluation occurred. Export new editions with reference_annotations.py export --output <new-directory>; package with finalize_annotations.py --annotations-dir <new-directory>. Historical pause statements above have been superseded by the completed OCR experiments in Context/OCR_TEXT.md.

## Current content scope

The user clarified PRINTED TEXT ONLY on 2026-10-20. Historical references are preserved, including handwriting that is now outside scope. Use scope/printed-only-v1/eligible_manifest.csv for current candidates and scope/printed-only-v1/review_queue.csv for the eligible flagged queue. The portal defaults to this scope; ignore handwritten notes/signatures and do not reuse old handwriting references as current training text.
