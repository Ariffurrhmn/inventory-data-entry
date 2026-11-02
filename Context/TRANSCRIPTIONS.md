# Transcription handoff — 2026-10-19

User requested JSON or XML text references against the existing 140 included classifier images, and paused the five improvement tasks. JSON was chosen.

Completed 140 OCR-assisted transcriptions, each visually checked against its prepared image. Files live in Dataset/annotations/transcriptions/, with index.csv and a combined transcriptions.jsonl. Open Dataset/annotations/review.html to compare images and text. Dataset/annotations/README.md documents fields, markers, limitations and regeneration. Raw OCR remains separately labeled unreviewed in ocr_drafts/.

Counts: purchase_order 35, receipt 28, delivery_note 50, customer_copy 27. Frozen splits: train 86, val 26, test 28. All 140 exported records are assistant_visual_reviewed, human_verified=false. These are reference candidates, not independently verified benchmark gold truth. Tables are linearized; no reviewed bounding boxes or structured extraction labels were produced.

Validation checks exact sample coverage, nonempty text, UTF-8 replacement characters, labels/splits/source metadata against the frozen manifest, prepared image SHA-256 and required files. Full original source hashes were not recomputed. See Dataset/annotations/validation_report.json for actual counts and explicit limitations.

Some source regions are redacted, faint, cropped or handwritten. Dataset/annotations/review_queue.csv collects uncertainty notes/markers for audit. Do not infer missing content or score unresolved spans as exact truth. Do not feed filenames, labels or annotation metadata into classifier features.

Annotation maintenance uses review_actions.json keyed by one-based row in the current frozen manifest. Correct that source of review actions before re-exporting; direct JSON edits are overwritten. Export with services/document_classifier/reference_annotations.py export, then package/check with finalize_annotations.py.

No classifier training, OCR quality comparison, text experiment, fusion comparison or external import was performed. Tesseract was used only to assist annotation drafting. The five tasks in PENDING.md remain paused.

## UTF-8 reference repair — 2026-10-19

Found and fixed a Windows encoding bug: reference_annotations.py read UTF-8 review actions using the cp1252 system default. Created Dataset/annotations/versions/utf8-v2/ from the unchanged correction instructions; 34 text records corrected (32 train, 1 val, 1 test). All 140 new JSONs, their image hashes and review-page image links passed checks; 863 protected historical annotation/run/data files remained unchanged; the annotation README was intentionally updated after verification. Fifteen workflow checks passed, including a regression test simulating cp1252. Two training images were visually spot-checked; this is not an independent human audit. Human verification is still zero and the 45-record review queue remains unresolved.

Use the versioned UTF-8 references for future review. Preserve original references and prior reported metrics; no model training, OCR metric recalculation, or new test evaluation occurred. Current default classifier remains text_preliminary/original_ocr. Details: Dataset/annotations/versions/utf8-v2/README.md and Dataset/annotations/audits/utf8-2026-10-19/report.json. Next: independent review of uncertain spans and collection of real holdout documents.

## Interactive reviewer workflow

services/annotation_portal/ now provides a local left-image/right-editor portal. It loads the UTF-8 v2 references and all available original/experiment/sparse OCR drafts, including 91 intake samples without reviewed references. Human reviews save separately in Dataset/annotations/human_review/reviews.sqlite3 with full revisions and JSON export. Only explicit named reviewer confirmation marks the latest saved review human_verified=true. Source references/review actions stay unchanged; reference adoption is a later versioned step. See the portal README and validation.json. No human records were created by the agent in the real store.

## Assistant visual review batch saved — 2026-10-19

User asked Codex to perform the proposed 10-record review batch. Individually visually inspected 10 flagged receipt images and saved 10 AI review revisions in the portal: 3 text corrections, 2 unresolved payment-status/taxonomy flags, and mixed-language scope notes. All are reviewer_type=ai, status=needs_review, human_verified=false. Redacted text was not reconstructed. Existing unnamed/unedited drafts arrived during inspection; preserved them as revision 1 and appended the AI findings as revision 2 after checking they contained no manual edits. All 20 pre-existing review records remain in history, and 14 protected reference/metadata files matched hashes. Human edits/named reviews would have been skipped.

Evidence: Dataset/annotations/audits/assistant-review-batch-01-2026-10-19/README.md, applied.json, reviews.json and pre-review database backup. Initial report.json records a skipped first attempt and is not the completion summary. Five reviewed images belong to the historical test split; no training, tuning or evaluation occurred. The AI review does not create independently human-verified ground truth or change canonical references/frozen labels. The portal now distinguishes AI reviewer provenance from human verification; six backend tests pass, including rejection of AI human-verification requests. Next: human adjudication of payment/language questions, further annotation review, and explicit versioned adoption of accepted corrections before training.

## Printed-only transcription scope — 2026-10-20

Do not transcribe handwritten notes, signature names or added values for the current task. Original 140 references and saved review history remain historical, including unsupported handwriting. Active printed candidate manifest and 35-record eligible flagged queue live under Dataset/annotations/scope/printed-only-v1/. The portal defaults to that scope; handwritten/mixed held pages remain read-only history. Scope screening is not a new human transcription verification.
