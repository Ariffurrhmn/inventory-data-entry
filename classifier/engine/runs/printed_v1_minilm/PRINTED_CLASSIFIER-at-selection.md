# Running printed document classifier — 2026-10-20

The active classifier is **printed_v1_minilm**, running locally at **http://127.0.0.1:8767**. Double-click **Open Classifier.cmd** to start/open it later. Input: a printed-document image (JPEG/PNG/WebP/HEIC/TIFF) or pasted OCR text. Output: exactly purchase_order, receipt, delivery_note or customer_copy. Table/number extraction remains outside this classifier.

## Run it

From the project root:
```powershell
.\services\document_classifier\start_classifier.ps1 -Open
.\services\document_classifier\classify.ps1 -Image 'C:\path\document.jpg'
.\services\document_classifier\classify.ps1 -TextFile 'C:\path\ocr.txt'
```

run.ps1 -Action predict uses the active OCR-text pipeline; predict-image retains the historical image baseline. Python comes from runtime.local.json. Hidden server logs are in .runtime/. The launcher restarts this project's owned classifier processes when the active run changes. The annotation portal stays separate on port8765.

## Current inference

Full-page sparse Tesseract OCR → frozen MiniLM encoder → trained balanced logistic regression. Separate top/bottom35% crops with autocontrast/PSM6 recover explicit printed heading/copy cues. Those region texts enter heading decisions only, never the learned model. MiniLM separately encodes the first254 and last254 wordpieces with mean pooling; concatenated features preserve titles and footers. Pasted text supplies both model input and heading context.

An unambiguous Purchase Order / Order Form / Order Slip, Delivery Note / Delivery Challan / Packing Slip, or Customer / Office / Guest / Duplicate Copy cue may select the class. Conflicting headings use the trained fallback. There are no merchant-name/sample-ID rules. Scores are uncalibrated classifier preferences and are not fabricated to agree with heading-selected labels. The UI shows matched text instead of score bars when a heading selects the label. Input must be printed: no handwriting detector is implemented.

The public encoder is local and frozen, not a remote LLM call. Its pinned weights/tokenizer and notices live under the configured C: runtime's hf-cache, outside Drive syncing. runs/printed_v1_minilm/public_weights.json records the exact absolute path, publisher revision and hashes. Inference verifies hashes and uses local_files_only=True. Keep that cache; copying the small joblib alone to another machine is insufficient. Optional dependencies are in requirements-transformers.txt. See TRANSFORMER_EXPERIMENT.md for restoration details.

## Development evidence

202 printed-scope candidates:150 train,25 validation,27 historical test excluded from this work. Saved split: runs/printed_v1_grouped/split_manifest.csv, copied into later runs. Original labels/splits remain unchanged.

| Split | Purchase order | Receipt | Delivery note | Customer copy | Total |
|---|---:|---:|---:|---:|---:|
| Training | 36 | 56 | 50 | 8 | 150 |
| Development validation | 10 | 3 | 3 | 9 | 25 |

Known Bridge printed templates across classes are one development family held in validation; Company Documents v2 stays one training generator family. Five excluded old test photos share the broader Bridge validation family. Old test remains excluded and is not independent of this development exercise. Exhaustive provenance independence is unproven.

| Stage | Validation correct | Macro-F1 |
|---|---:|---:|
| Statistical classifier, baseline OCR | 13/25 | .4806 |
| Heading cues + trained fallback, sparse OCR | 17/25 | .6849 |
| Heading cues + page-edge recovery + TF-IDF fallback | 19/25 | .7657 |
| **Same heading/edge rules + frozen MiniLM/LR fallback (active)** | **20/25 (80%)** | **.8036** |

Transformer comparison also tried fine-tuning small BERT for12epochs and fusing MiniLM with lexical features. Neither improved the winner. MiniLM alone scored13/25; heading/OCR recovery remains essential. Detailed raw/hybrid results and reproducible artifacts are in TRANSFORMER_EXPERIMENT.md.

Current recall: PO9/10, receipt3/3, delivery_note3/3, customer_copy5/9. One extra correct customer copy accounts for the net improvement. Four customer copies and one PO remain wrong. All three validation delivery notes are printed synthetic Bridge photos. Only eight training customer copies exist. Scores are not calibrated; label/payment/language questions and AI-reviewed truth remain limitations.

**All comparisons are adaptive development measurements on reused validation. No fresh final holdout has been collected or evaluated.** More validation searches increase the risk of overfitting selection. Historical test records were not opened for this work.

## Artifacts and checks

- active_text_model.json selects the current offline model.
- runs/printed_v1_grouped/, printed_v1_headings/, printed_v1_edges/: preserved previous statistical/OCR experiments.
- runs/printed_v1_transformers/: two frozen MiniLM classifiers, three fine-tuned BERT checkpoints, specifications, source revisions, input audit and per-record results.
- runs/printed_v1_fusion/: two semantic/lexical classifiers and results.
- runs/printed_v1_minilm/: selected inference adapter, LR, rules, copied edge caches, validation and smoke evidence.
- transformer_models.py, inference.py: saved-model inference; classifier_app.py/classifier.html: local UI.

Twenty-one workflow checks pass. Packaging independently reproduced all25 validation predictions and encoder features. Four real validation image uploads reproduced cached-pipeline outputs (three correct, one known customer-copy error); empty text and invalid images returned errors. Browser classification completed, including existing validation OCR e4c7eb83722c, now correctly classified as customer_copy. The saved transformer_preview.png shows that record, not a new independent evaluation. A separately labelled fabricated demo was used only for interface checking and is not measured data.

Raw datasets, reference editions, review history, original splits and previous models remain intact; protected hashes were checked before activation. Best next data work: more independent printed customer-copy examples and a fresh real holdout. Further model experiments should use training-only grouped folds where possible.

