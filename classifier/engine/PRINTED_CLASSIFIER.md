# Printed classifier — current handoff 2026-10-20

Selected saved run: **printed_v3_explainable**, a corrected-OCR + printed-text-rule + trained TF-IDF/ComplementNB hybrid with measured explanations.

**Development validation23/25 (92%), macro-F1 .9211.** Training-only grouped OOF model predictions with adaptive rule overlay:146/150 (97.3%), macro-F1 .9480. These are development checks, not independently established real-world accuracy. All27 historical test inputs remain excluded.

Read **EXPLAINABLE_CLASSIFIER.md** for architecture, all experiments, exact explanation methods, data isolation and limitations. The earlier transformer handoff below is preserved in runs/printed_v1_minilm/PRINTED_CLASSIFIER-at-selection.md; TRANSFORMER_EXPERIMENT.md remains the historical transformer report.

## Use

The selected classifier accepts printed-document images or OCR text and predicts purchase_order, receipt, delivery_note or customer_copy. It does not extract tables/numbers and does not support handwritten documents.

From the project root:
```powershell
.\services\document_classifier\start_classifier.ps1 -Open
.\services\document_classifier\classify.ps1 -Image 'C:\path\document.jpg'
.\services\document_classifier\classify.ps1 -TextFile 'C:\path\ocr.txt'
```

Open Classifier.cmd opens the local app at http://127.0.0.1:8767. The existing process was intentionally not restarted after these experiments, per the user's request to focus on improving rather than repeatedly demonstrating it. It may still hold the previous MiniLM pipeline. The next launch detects the changed active run and loads the new saved pipeline.

The new API response includes an explanation by default, and the UI source renders “Why this prediction?” with matched printed rules or weighted text evidence. The UI was statically checked, not reopened/demonstrated. Classifier scores remain uncalibrated preferences.

For pasted text, supply OCR from the corrected full-page policy for the closest match to training; sparse OCR or plain reference transcription is a different input distribution. For an image, the pipeline automatically performs uniform corrected full-page OCR for learned features plus separate sparse/edge/rotated views for printed rules. Each view gets its own title window. Ambiguous cross-class cues use the trained fallback.

## Why it predicts a class

- Rule selection: normalized matched text and rule kind; purchase-request intent lists all three field groups. OCR-tolerant “duplicate” matching records the raw fragment, canonical word and one-character edit.
- Learned fallback: supporting/opposing n-grams with exact contributions to the target-versus-alternative log-score difference. The sum reconstructs that difference, rather than generating a rationale.
- Older transformer runs: explain.py measures fixed-model token-block omission effects.

Full JSON explanations for all25 selected validation predictions are in runs/printed_v3_explainable/explanations/. Eighteen used heading traces, two purchase-intent traces, five exact learned explanations. Maximum score reconstruction error:2.27e-14. explain.py can also explain an existing OCR file with --text-file, optional --heading-file, --output and --run.

## Validation and remaining errors

Same printed scope202:150 training,25 development validation,27 historical test excluded. Known training/validation groups stay separated; original splits/labels/references/history remain intact. Current recall:PO10/10,R3/3,DN3/3,CC7/9. Two red-stamped customer copies remain wrong. Only eight CC training examples exist; all three validation delivery notes are printed synthetic Bridge photos. Dataset truth is not independently human-verified.

Thirty workflow tests pass. All25 persisted predictions and explanations reproduced; grouped-fold feature fitting, rule ambiguity, multi-view routing and algebraic explanation fidelity were checked. UI JavaScript passes node --check. No repeated image-upload demo or server restart was performed.

The current ComplementNB model needs the configured base sklearn/Pillow environment, not the optional Hugging Face weight cache. Keep that cache for preserved older transformer runs. Six protected source/model/evaluation hashes remain unchanged.

For additional improvement, prioritize independent printed customer-copy families and a fresh real holdout. Color/region OCR for faint copy stamps is a plausible next experiment, not implemented in this edition.

