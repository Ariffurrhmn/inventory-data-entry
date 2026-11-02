# Document Lab — supervisor demo

**Double-click [Open Demo.cmd](Open%20Demo.cmd).** It starts the local app and opens http://127.0.0.1:8770. The model and dependencies are already configured on this PC.

This folder contains the classifier application, selected model, original classifier source, experiment history and presentation examples. Shared project memory remains in ../Context/.

## Present it in three minutes

1. Open the app and choose **Purchase request**. Point to the printed slip on the left and the three matched purchase-request fields on the right.
2. Choose **Retail receipt**, **Delivery challan**, then **Office copy** to show the four classes. The badge says **Recorded example**: these are saved analyses of existing development documents, using actual cached OCR.
3. Choose **Faint copy stamp**. Show the known mismatch and the text features that supported the wrong prediction. An explanation describes model behavior; it does not guarantee a correct label.
4. Open **Model & evidence**. State the measured development result:23/25 (92%). The grouped training check is146/150 (97.3%) with an adaptive rule overlay. Neither is independent final accuracy.
5. If time permits, choose a normal example and click **Run live classification**, or upload your own printed slip. Live mode actually runs local OCR and classification; detailed images can take a while.
6. **Export JSON** downloads the report. **Save in project** writes it into exports/. Uploaded images are temporary and are not saved.

A longer presentation script and likely supervisor questions are in [docs/SUPERVISOR_DEMO.md](docs/SUPERVISOR_DEMO.md).

## Folder map

| Location | Purpose |
|---|---|
| Open Demo.cmd | One-click launch on this Windows PC |
| Stop Demo.cmd | Stops only this demo's local server |
| app/ | Demo server, HTML, CSS and JavaScript |
| demo/ | Five copied development images and their recorded model explanations |
| engine/ | Consolidated classifier code, selected model, derived training images, OCR weights and all previous experiment runs |
| engine/runs/printed_v3_explainable/ | Selected model, integrity checks and validation/explanation evidence |
| docs/ | Presentation guide, migration records and demo validation |
| tests/ | Demo API tests |
| exports/ | Explicitly saved reports; not automatically training data |
| setup.ps1 / Setup Demo.cmd | Optional dependency setup on another PC |

Raw datasets, annotation truth/review history and signed deliverables remain in their original project locations. The old services/document_classifier/data/ is an immutable compatibility copy for historical annotation image links; two historical OCR cache folders are also retained read-only so an already-running annotation portal remains usable. New classifier work belongs here. Old command launchers forward to this folder.

## Modes and explanations

**Recorded examples** make the walkthrough immediate and reproducible. Their image hashes and model hashes are checked. They are not fresh inference or a new benchmark. Four examples are photographs of printed synthetic documents; the app states this provenance. The receipt is an existing development document with incompletely recorded original provenance.

**Live analysis** accepts JPEG, PNG, WebP, HEIC, TIFF or BMP up to20 MB/25 megapixels. It uses the selected saved classifier and local Tesseract OCR. A text tab also accepts pasted OCR. For the closest match to model training, use corrected full-page printed OCR.

The hybrid predicts exactly purchase_order, receipt, delivery_note or customer_copy. It shows either the printed rule and actual matched text, or supporting/opposing n-grams with exact contributions to the learned log-score difference. Scores are uncalibrated model preferences. No LLM rationale, table extraction or inventory update is involved.

Handwriting is outside scope. Signatures are not transcription targets. The two missed red copy stamps, limited customer-copy data and non-independent validation are shown rather than hidden. Full research details: [engine/EXPLAINABLE_CLASSIFIER.md](engine/EXPLAINABLE_CLASSIFIER.md).

## Running and setup

PowerShell alternative:
```powershell
.\classifier\start_demo.ps1 -Open
.\classifier\start_demo.ps1 -Port 8771 -Open
.\classifier\stop_demo.ps1
```

The launcher checks the runtime config, Tesseract, selected model and port ownership. Logs: .runtime/demo.log and demo-error.log. If the port belongs to another app, select another port; the launcher does not stop unrelated services. Keep this folder available locally before the presentation if Google Drive is streaming its files.

On another Windows PC:
- Install Python 3.12, 3.13 or 3.14 and Tesseract; ensure tesseract is on PATH.
- Copy this entire classifier folder, including engine/.cache/tessdata/eng.traineddata.
- Run Setup Demo.cmd, then Open Demo.cmd. Setup installs only the minimal demo dependencies into LocalAppData/DocumentLab/python-env and writes engine/runtime.local.json (shared with services/document_pipeline and supervisor_showcase).
- No Hugging Face cache, GPU, API key or network inference is required for the selected ComplementNB model. Network is only needed for initial dependency installation.
- Research retraining additionally requires the parent project's Dataset/ and related provenance files; copying this demo folder does not copy the raw datasets.

To run checks:
```powershell
$pythonPath=(Get-Content classifier/engine/runtime.local.json -Raw | ConvertFrom-Json).python
& $pythonPath -m unittest discover -s classifier/tests -p 'test_*.py'
& $pythonPath -m unittest discover -s classifier/engine -p 'test_*.py'
```

JSON reports contain OCR text and evidence. Saving/exporting does not change source images, annotations, ground truth, training splits or the model.


