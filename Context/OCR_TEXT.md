# OCR-text classifier handoff — 2026-10-19

User authorized the preliminary grouped OCR-text experiment. It is complete in services/document_classifier/runs/text_preliminary/. Read services/document_classifier/TEXT_EXPERIMENT.md for full results and limitations.

Frozen original assignments remain 86 train / 26 validation / 28 test. A separate experiment manifest adds all 91 accepted intake records to training only (177 augmented training records), without rewriting the original corpus/splits. Merchant-name screening found no existing-family matches; prior exact/perceptual/visual audits were retained. This is not proof of exhaustive supplier/layout independence.

Three fixed TF-IDF word/character plus balanced logistic-regression models were fitted: corrected reference text (86 originals), actual OCR text (86 originals), and OCR text plus additions (177). Features are fitted on training only. C=1, seed 42; no tuning after test evaluation. Validation-selected candidate is original_ocr: validation 21/26, macro-F1 .782; test 17/28 (60.7%), macro-F1 .597. Augmented OCR: validation 20/26, macro-F1 .726; test 20/28 (71.4%), macro-F1 .695. Preserve the validation-selected candidate despite the augmented test advantage. Historical image baseline: 13/28 (46.4%), macro-F1 .483.

Reference model: 15/28 on corrected test text, macro-F1 .545; 15/28 on OCR test text, macro-F1 .505. Do not assume OCR is the only problem or call corrected-text performance a ceiling. Selected model delivery-note recall is only 1/10; customer copies 6/6, POs 6/7, receipts 4/5. The small test was examined before this experiment and is not fresh final evaluation.

Original 140 OCR drafts were reused after image/source hash validation; all 91 additions were processed with matching Tesseract 5.5.3 best-English PSM3 and controlled upscaling. Seven originals and one addition produced empty text. Cache includes images/policy/traineddata hashes.

Preliminary OCR scoring: only 72 whole original documents, with no bracket markers or uncertainty notes; 68 excluded entirely. Micro CER36.4%, WER45.6% after NFKC/casefold/whitespace normalization. Signature-marked pages are excluded, and receipt subset is only 4 documents/55 words. Table reading order, linearization and unverified AI references limit interpretation. These are not independently human-verified gold metrics.

Ten original/new workflow checks passed. Saved-pipeline reload checks and image/text inference smoke validation are recorded. All 144 protected original label/manifest/split/result/reference files matched pre-run hashes. Image baseline and source annotations were not changed.

Run from services/document_classifier with the existing Python environment:
- python predict_text.py --image <image path>
- python predict_text.py --text-file <OCR text file>
- python -m unittest test_workflow.py test_text_workflow.py

predict_text.py loads selection.json and returns exactly one of the four labels, uncalibrated scores and an empty-OCR flag. No LLM/table/number extraction or application API was added. Existing run names cannot be overwritten; use a new name for reproduction.

Next priorities: independently audit uncertain labels/transcriptions, collect a fresh real supplier/layout-separated holdout, and investigate delivery-note OCR/representation failures using validation only. Do not repeatedly tune on the exposed 28 test images. Fusion and application/LLM integration remain outside this completed experiment.

## Completed validation-only follow-up

Read services/document_classifier/DELIVERY_OCR_EXPERIMENT.md and runs/text_delivery_v2/validation.json. Four sparse/combined variants failed to improve validation macro-F1; original_ocr remains default. Sparse OCR recovered eight empty training/validation outputs, but classification did not improve. No test images opened or new test score produced. Thirteen workflow tests and training-image/text inference checks passed. The existing preliminary test results above are unchanged. Holdout collection instructions: docs/data-collection/FRESH_HOLDOUT.md; actual fresh holdout count is zero.

Annotation encoding update: Dataset/annotations/versions/utf8-v2/ corrects 34 reference texts previously corrupted by cp1252 decoding. Historical OCR/reference-classifier metrics above use the preserved older references and have not been recomputed. Actual OCR-model selection/inference is unchanged; no new test evaluation.

Printed-only scope supersedes the previous handwriting-inclusive task. Active candidate manifest: Dataset/annotations/scope/printed-only-v1/eligible_manifest.csv (202). Old model/metrics remain legacy mixed-scope results, not printed-only measurements. Current validation subset lacks delivery notes; fix development coverage before new selection. Legacy scripts still consume historical manifests and require an explicit new scope-aware runner for future printed-only experiments.

## Printed classifier trained and running — 2026-10-20

User explicitly requested training and a running classifier ASAP. Active pipeline is runs/printed_v1_edges/ via active_text_model.json, using trained word/character TF-IDF + balanced logistic regression, explicit printed-heading decisions and sparse/full-page plus top/bottom region OCR. Web upload/pasted-text app runs on http://127.0.0.1:8767; launch with services/document_classifier/Open Classifier.cmd or start_classifier.ps1 -Open. CLI classify.ps1 and default run.ps1 predict use the active pipeline; predict-image retains the legacy image model.

Created a new grouped development manifest without changing frozen original splits. Training150: PO36/R56/DN50/CC8. Validation25: PO10/R3/DN3/CC9. Known Bridge printed template groups across classes are held together in validation. All 27 historical test records are excluded; five share the broader Bridge validation family, so this is not an independent new test. Company Documents v2 stays one training generator group.

Initial three OCR/statistical candidates selected baseline at 13/25. Adaptive bounded heading and edge-OCR follow-ups reached 19/25 (76%), macro-F1 .7657. Validation recall PO9/10, R3/3, DN3/3, CC4/9: customer copies remain weak, and all three validation delivery notes are synthetic. Do not present development validation as final generalization accuracy. Twenty-one workflow checks pass; final saved inference reproduces all25 predictions, image-upload/cached-pipeline checks pass (one CC misclassification explicitly recorded), and empty/bad input rejection plus CLI/browser operation were verified. No old test inputs opened, no reference/label/source rewrites. See services/document_classifier/PRINTED_CLASSIFIER.md and final smoke_validation.json. The earlier missing-validation-DN blocker is resolved by the new development split, not by changing the historical test.

Transformer follow-up (2026-10-20): printed_v1_minilm now selected at20/25 on reused printed development validation. Statistical fallback uses a frozen MiniLM encoder with trained balanced LR; heading/edge OCR is unchanged. No new test result. See services/document_classifier/TRANSFORMER_EXPERIMENT.md and PRINTED_CLASSIFIER.md; earlier active pointers above are historical.

Current OCR/model (2026-10-20): printed_v3_explainable uses illumination-normalized full-page PSM6 for learned features and independent sparse/edge/rotated views for explicit evidence. All175 development images processed uniformly; historical27 test inputs excluded. Per-view title windows fix suppressed later headings. Selected hybrid23/25 adaptive validation; exact model/rule explanations included. See services/document_classifier/EXPLAINABLE_CLASSIFIER.md; earlier active runs remain preserved history.

Current paths/demo (2026-10-20): classifier/engine/ holds the preserved OCR/model experiments; classifier/Open Demo.cmd launches the supervisor app at8770. Faithful explanations, explicitly recorded validation examples, live OCR and JSON report saving are implemented. Raw images/annotation history preserved; historical prepared-image compatibility remains under services/document_classifier/data/. See classifier/README.md.

