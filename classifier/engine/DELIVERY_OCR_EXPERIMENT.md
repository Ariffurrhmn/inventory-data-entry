# Delivery-note OCR follow-up — 2026-10-19

The existing original_ocr model remains selected. Sparse OCR recovered previously empty text, but none of four fixed alternatives beat the existing validation macro-F1 of 0.7818. No new test evaluation was performed.

## Experiment

Only training and validation images were opened: 177 training records (86 originals plus 91 reviewed additions) and 26 original validation records. Original splits, labels and references were preserved. Tesseract PSM11 used the same English model and resize policy as the PSM3 baseline. Combined mode appends unique nonempty lines from both passes. Each candidate uses the unchanged word/character TF-IDF and balanced logistic-regression configuration; references are used for OCR diagnostics, never as candidate classifier inputs. There are no class-specific keyword overrides.

| Candidate | Training records | Validation correct | Macro-F1 |
|---|---:|---:|---:|
| Existing original OCR (PSM3) | 86 | 21/26 | 0.7818 |
| sparse_original | 86 | 18/26 | 0.6622 |
| combined_original | 86 | 17/26 | 0.5967 |
| sparse_augmented | 177 | 20/26 | 0.7259 |
| combined_augmented | 177 | 19/26 | 0.6523 |

## Interpretation

Across the 203 training/validation records, eight baseline outputs were empty; none were empty with sparse OCR. Nonempty output is not a guarantee of usable text. The best new candidate still identifies only 2/6 validation delivery notes and 3/5 customer copies. Sparse OCR therefore does not resolve the delivery-note problem.

On the same 63 eligible original training/validation reference documents, character error rate changed from 36.7% to 31.5%, while word error rate changed from 44.6% to 50.7%. Sparse reading order and linearized table references affect both metrics. References are assistant-reviewed and remain human_verified=false. These figures cannot establish independently verified OCR accuracy.

Validation has now been reused adaptively and the historic test set was already exposed. Preserve both runs and collect a fresh real business/layout-separated holdout before stronger claims. The current four-candidate comparison is complete; it does not justify more tuning against the historic test set.

## Artifacts and use

- runs/text_delivery_v2/validation.json: metrics, OCR coverage, limitations and 69 protected-file hash checks.
- selection.json: best new candidate is sparse_augmented, promoted_validation_candidate=false.
- validation_predictions.csv and confusion CSVs: validation-only predictions.
- ocr_sparse/: cached raw OCR; diagnostic_text/: paired OCR for known validation failures.
- smoke_validation.json: workflow checks and persisted-model image/text inference check on a training image.

Default `python predict_text.py --image <path>` continues to load text_preliminary/original_ocr. To explicitly inspect the rejected follow-up candidate, use `--run text_delivery_v2`. That option is experimental and does not promote the candidate. Supplied text files must come from the matching OCR policy when comparing policies.

## Fresh holdout

See ../../docs/data-collection/FRESH_HOLDOUT.md and ../../Dataset/holdout_real_pending/. The target is 80 distinct real documents, 20 per class, with new business/layout families. The manifest is a blank collection template; no fresh holdout documents have been collected. Keep these images out of training and model selection, and freeze the chosen pipeline before opening them for final evaluation.
