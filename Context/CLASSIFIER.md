# Classifier handoff

Updated 2026-10-19.

Implementation: ../services/document_classifier/README.md
Results: ../services/document_classifier/RESULTS.md
Review: ../services/document_classifier/REVIEW.md

User scope: image -> purchase_order / receipt / delivery_note / customer_copy only. No classifier table detection or number extraction. User confirmed Dataset-2 contains photographs of printed synthetic originals.

Initial corpus: 145 images decoded (91 curated, 54 HEIC phone photographs). Corrected five packing slips and one delivery challan from the purchase-order folder in the manifest only. Five ambiguous samples excluded pending team review. Final usable 140: PO35, receipt28, delivery50, customer27. Office Copy is included under customer_copy per existing proposal taxonomy.

Split: 86 train / 26 validation / 28 test, immutable data/splits.csv. Reviewed document/template families group related originals and photographs. No claims of complete vendor separation; unknown relationships may remain.

Selected: ImageNet MobileNetV3 Small frozen features + trained head. Best validation macro-F1 0.456. Fine-tuning last visual blocks did not improve; preserve both runs, selected baseline. Test accuracy 46.4% (13/28), macro-F1 0.483. Largest confusion: delivery notes -> purchase orders. Experimental and not reliable for operational use.

Use PowerShell services/document_classifier/run.ps1 -Action predict -Image <absolute image path>. Local isolated Python runtime is recorded in runtime.local.json (ignored by Git); dependencies live on the local C: drive, not inside the Google Drive dataset folder. Portable setup instructions are in classifier README.md.

Five workflow tests pass; one-image prediction verified. Originals are preserved. Data audit initially reflects original folder labels; authoritative corrected labels are labels.csv and data/manifest.csv.

Next: compare better resolution/document features or OCR-text features on validation, keeping the public output strictly four-class. Since initial test errors are now known, use a fresh independent final holdout for strong claims. This work did not build OCR extraction, LLM integration, mobile app, or API.

## Dataset research handoff — 2026-10-19

The latest user request specifies OCR text as classification input after photograph/scan capture. The existing trained experiment above remains an image-only historical baseline; no model change/training occurred in this research session.

See ../research/datasets/DATASET_SEARCH.md and sources.csv for checked public options and gaps. Candidate images/annotations are quarantined in Dataset/external_candidates/, not training data. Five existing Customer_Copy images have confirmed ExpressExpense SRD SHA-256 matches; CORD train ID 8 has a confirmed visual derivative match to Receipt/cord-train-0008.jpg. Exact paired evidence is in overlap_matches.csv. Other source guesses are explicitly unconfirmed.

Initial acquisition can use small English synthetic PO/packing-slip subsets plus manually copy-labelled SRD photographs. Real delivery-note/challan and customer-copy family coverage remain insufficient. Office Copy/Guest Copy/Duplicate stay accepted under existing taxonomy; copy precedence on PO/delivery pages, goods received notes and invoice/delivery hybrids need a decision before intake. Preserve current labels/splits/results.

## Current OCR-text path — 2026-10-19

The user resumed the preliminary experiment. Read OCR_TEXT.md and services/document_classifier/TEXT_EXPERIMENT.md. A runnable OCR→TF-IDF/logistic-regression four-class pipeline now exists, with validation-selected original_ocr scoring 17/28 on the exposed historical test. The image baseline is preserved. The augmented training run scores 20/28 but loses validation and is not promoted after test. All results are preliminary; delivery-note recall remains 1/10.

Latest follow-up: sparse/combined OCR did not beat existing validation performance. Default remains text_preliminary/original_ocr; no new test evaluation. See services/document_classifier/DELIVERY_OCR_EXPERIMENT.md and docs/data-collection/FRESH_HOLDOUT.md. Thirteen workflow checks pass; fresh holdout collection is still pending.

## Printed-only scope applied — 2026-10-20

User explicitly excluded handwriting. Visually screened all 236 catalog candidates for content style, retaining contact-sheet evidence and selected enlargements. Activated Dataset/annotations/scope/printed-only-v1/: 202 candidates (52 PO, 64 receipt, 63 delivery note, 23 customer copy), comprising 116 original included and 86 intake images. Excluded 24 handwriting-dependent catalog images (two already historically excluded); held seven printed images with handwritten notes/values pending reviewed printed-only derivatives; retained three other prior exclusions. Photographed synthetic handwriting-style bodies remain outside scope even when physically printed. Incidental signatures are ignored as transcription targets.

Portal defaults to printed candidates and has separate handwriting/region-hold/history views. Out-of-scope records are read-only, and the printed-review export withholds their saved reviews; full catalog export preserves history with scope flags. Eight backend tests pass. Original labels, 86/26/28 assignments, 140 corrected references and selected model/results remain preserved (147 protected hashes checked). No training/evaluation and no new human verification.

Critical readiness gap: inherited printed subset is train162/val13/test27, but validation has zero delivery notes (the six previous validation delivery notes were handwriting-dependent). Need new printed delivery-note development data or an explicitly versioned grouped development split from non-test families before four-class model selection. Do not use the old exposed test to fill the gap. Legacy predictor and metrics still describe the previous broader scope. See scope README, validation.json and evaluation_readiness.json. Current scope eligibility does not resolve existing label/payment/language uncertainties or imply perfectly cleaned OCR.

## Printed classifier trained and running — 2026-10-20

User explicitly requested training and a running classifier ASAP. Active pipeline is runs/printed_v1_edges/ via active_text_model.json, using trained word/character TF-IDF + balanced logistic regression, explicit printed-heading decisions and sparse/full-page plus top/bottom region OCR. Web upload/pasted-text app runs on http://127.0.0.1:8767; launch with services/document_classifier/Open Classifier.cmd or start_classifier.ps1 -Open. CLI classify.ps1 and default run.ps1 predict use the active pipeline; predict-image retains the legacy image model.

Created a new grouped development manifest without changing frozen original splits. Training150: PO36/R56/DN50/CC8. Validation25: PO10/R3/DN3/CC9. Known Bridge printed template groups across classes are held together in validation. All 27 historical test records are excluded; five share the broader Bridge validation family, so this is not an independent new test. Company Documents v2 stays one training generator group.

Initial three OCR/statistical candidates selected baseline at 13/25. Adaptive bounded heading and edge-OCR follow-ups reached 19/25 (76%), macro-F1 .7657. Validation recall PO9/10, R3/3, DN3/3, CC4/9: customer copies remain weak, and all three validation delivery notes are synthetic. Do not present development validation as final generalization accuracy. Twenty-one workflow checks pass; final saved inference reproduces all25 predictions, image-upload/cached-pipeline checks pass (one CC misclassification explicitly recorded), and empty/bad input rejection plus CLI/browser operation were verified. No old test inputs opened, no reference/label/source rewrites. See services/document_classifier/PRINTED_CLASSIFIER.md and final smoke_validation.json. The earlier missing-validation-DN blocker is resolved by the new development split, not by changing the historical test.

Transformer follow-up (2026-10-20): active printed_v1_minilm,20/25 adaptive printed development validation, macro-F1 .8036, CC5/9. Frozen MiniLM + trained logistic head plus prior heading/edge rules; small BERT and lexical fusion did worse. All27 historical test inputs excluded. Read services/document_classifier/TRANSFORMER_EXPERIMENT.md and PRINTED_CLASSIFIER.md; prior active-model statements above are historical. Weight cache on local C: is required.

Latest classifier (2026-10-20): selected printed_v3_explainable,23/25 adaptive validation, macro-F1 .9211; grouped training OOF with adaptive rule overlay146/150, macro-F1 .9480. Corrected OCR and per-view heading handling provide the gain; fallback is ComplementNB selected within grouped training CV. Not a92%-standalone BERT claim. Exact learned contributions or explicit rule traces explain decisions.30 tests, all25 saved predictions/explanations reproduced. Existing server not restarted; next user launch loads selected run. Read services/document_classifier/EXPLAINABLE_CLASSIFIER.md. Old test excluded; fresh final accuracy unproven.

Current location (2026-10-20): classifier/engine/ replaces services/document_classifier/ for source, models and all experiment history. User-facing demo is classifier/app, launched by classifier/Open Demo.cmd at port8770. See classifier/README.md and docs/SUPERVISOR_DEMO.md. Five labelled recorded examples and live upload/text inference; model remains printed_v3_explainable. Old prepared-image paths remain compatible.43 checks pass and one actual live image was browser-verified; no new training/evaluation.

