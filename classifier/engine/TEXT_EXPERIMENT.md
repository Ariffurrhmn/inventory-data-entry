# Preliminary OCR-text experiment — 2026-10-19

Completed the authorized comparison. Selected candidate: **original_ocr**, using validation macro-F1 before generating test predictions. This is exploratory evidence on a small previously examined test set, not independent final deployment validation.

## Results

| Model and input | Training images | Validation accuracy | Validation macro-F1 | Test correct / accuracy | Test macro-F1 |
|---|---:|---:|---:|---:|---:|
| Historical MobileNetV3 image baseline | 86 | — | — | 13/28 (46.4%) | 0.483 |
| Reference trained → reference text | 86 | 84.6% | 0.838 | 15/28 (53.6%) | 0.545 |
| Reference trained → OCR text | 86 | 61.5% | 0.569 | 15/28 (53.6%) | 0.505 |
| OCR trained, original only | 86 | 80.8% | 0.782 | 17/28 (60.7%) | 0.597 |
| OCR trained, plus 91 additions | 177 | 76.9% | 0.726 | 20/28 (71.4%) | 0.695 |

The original-only OCR candidate won validation. The augmented model scored higher on test, but was not promoted after seeing that result. Both OCR models and the reference diagnostic are retained. These numbers are a fixed, prespecified comparison; no hyperparameters were tuned after test evaluation. The old test was already inspected in the earlier image experiment, so it is not a fresh final holdout.

Reference-text performance is also limited. The reference-trained model gets 15/28 on both reference and OCR inputs, although its individual mistakes differ. OCR quality is therefore not the only problem demonstrated here; limited training diversity, model features, grouping and label definitions also need investigation. Do not interpret the diagnostic as a measured accuracy ceiling.

## Selected model per-class test performance

| Class | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| purchase_order | 7 | 0.500 | 0.857 | 0.632 |
| receipt | 5 | 0.571 | 0.800 | 0.667 |
| delivery_note | 10 | 0.500 | 0.100 | 0.167 |
| customer_copy | 6 | 0.857 | 1.000 | 0.923 |

Detailed predictions, confusion matrices and the selected model's test-error list live in runs/text_preliminary/. Probabilities are uncalibrated, and the classifier always chooses one of the four labels. The prediction command flags empty OCR; it has no unknown class.

## Data and leakage controls

The original corpus and data/splits.csv remain 140 images: 86 training, 26 validation and 28 test, with 52 existing groups. The experiment-specific manifest references 91 accepted additions as training-only: 49 receipts, 2 customer copies, 20 synthetic purchase orders and 20 synthetic packing slips mapped to delivery_note. Augmented training therefore has 177 images; evaluation remains the original 54 held-out images. No source images or existing reference JSONs were rewritten.

The additions passed the prior exact/perceptual/visual duplicate review. A normalized merchant-name check against original reference text found no matching existing merchant family. This is a guard, not proof of complete independence. Original group membership is checked for crossing splits; all new synthetic pages retain one generator-family group. Unknown supplier, layout, POS-system or source relationships can remain.

Word 1–2 gram TF-IDF and character-within-word 3–5 gram TF-IDF are combined with balanced logistic regression (C=1, lbfgs, max_iter=1000, seed 42). Vocabulary and IDF are fitted only on the respective training records. Class labels, filenames, source paths, splits and review notes are never supplied as features. NFKC and whitespace normalization are applied consistently. Bracketed spans are removed from classification input; this intentionally removes annotation descriptions, but also removes literal bracketed text such as [D], a limitation to revisit in a separately versioned experiment.

The reference model uses only corrected training text for the original 86; its evaluation reference text comes only from held-out records. There are no independent human-verified reference transcriptions for this experiment. New SRD OCR screening and publisher embedded text were not treated as reference truth.

## OCR quality: preliminary, restricted subset

Tesseract 5.5.3, tessdata_best English, PSM 3. Small images are enlarged toward width 1400, capped at 3×. Existing OCR drafts for all 140 originals were reused after image/source-hash checks. All 91 additions were OCR-processed with that same policy rather than mixing in the differently preprocessed intake screening text. Runs store the policy and traineddata hash.

Of 140 original reference records, **72 whole documents were scored and 68 excluded**. Any explicit uncertainty note or any bracket marker excludes the entire record, including signature-marked pages. No attempt was made to align an unresolved span with OCR and delete it independently.

On those 72 documents, after NFKC, casefold and whitespace collapse:

- Corpus character error rate: **36.4%** (34,092 reference characters).
- Corpus word error rate: **45.6%** (5,489 reference words).

These are edit-distance errors, not character-confidence estimates. The subset excludes difficult/uncertain pages and is not representative of the whole corpus. Reference reading order and linearized tables can create errors unrelated to character recognition. References are assistant-reviewed with human_verified=false, so these are preliminary measurements, not benchmark gold scores.

Empty OCR outputs: 7 originals and 1 additions. IDs are recorded in evaluation.json; per-document and per-class OCR scores are in ocr_quality_documents.csv and ocr_quality.json.

## Artifacts and reproduction

- runs/text_preliminary/experiment_spec.json: fixed settings, source hashes, OCR policy and limitations, saved before training/evaluation.
- experiment_manifest.csv and group_audit.json: experimental inclusion and grouping decisions.
- reference.joblib, original_ocr.joblib, augmented_ocr.joblib: fitted text pipelines.
- selection.json: validation-only candidate choice, written before test predictions.
- evaluation.json, predictions.csv, *_confusion.csv and selected_test_errors.csv: measured classifier results.
- ocr/ and ocr_quality*: cached OCR and preliminary scoring evidence.
- top_features.csv: selected-model feature coefficients, for inspection rather than causal explanation.

From services/document_classifier/ using the existing environment:

    python -m unittest test_workflow.py test_text_workflow.py
    python predict_text.py --image "C:/path/to/document.jpg"
    python predict_text.py --text-file "C:/path/to/ocr.txt"

The prediction command loads the candidate in selection.json. Image input runs local Tesseract first; text-file input accepts OCR text directly. HEIC input uses the installed pillow-heif plugin. Tesseract must be on PATH and .cache/tessdata/eng.traineddata present. No document text is uploaded by these scripts.

To reproduce training, use a NEW run name:

    python run_text_experiment.py --run text_reproduction

A completed run cannot be overwritten. Persisted joblib models should be loaded only from trusted local runs and with compatible package versions. The recorded sklearn version is 1.9.1.

## Validation and next work

All 144 protected original label/manifest/split/result/reference files matched their before-run SHA-256 values. Saved pipelines were reloaded and predictions checked for consistency. Workflow tests cover duplicate exclusion, held-out merchant exclusion, training-only vocabulary fitting, normalization and metric arithmetic; inference smoke results are recorded separately.

Next: human-check the reference/label uncertainties and build a fresh, supplier/layout-separated real-document holdout, especially delivery notes and copy-marked documents. Use validation for any subsequent OCR preprocessing/model changes. Do not promote the augmented model merely because of this test result. Image/text fusion, LLM extraction and application integration were not implemented.

Technical references: [scikit-learn text features](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction), [LogisticRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html).
