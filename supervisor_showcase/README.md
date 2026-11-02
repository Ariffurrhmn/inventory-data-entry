# Supervisor Showcase

Everything we show the supervisor about the completed document classifier, in one place.

**Double-click `Open Showcase.cmd`.** It starts a local server and opens http://127.0.0.1:8780 in your browser. `Stop Showcase.cmd` stops it.

The showcase is a six-step walkthrough. Use the top navigation, or the ← → arrow keys, to move between steps:

| Step | What the supervisor sees |
|---|---|
| 1. Overview | What the classifier does, headline results, how it works, the four document types |
| 2. Live demo | Pick any of the 25 validation documents, upload a photo, or paste text. See the predicted type and the exact reason behind it. "Run live" really runs OCR and the model (about 15 s) |
| 3. Results | Confusion matrix, per-type recall/precision, the two mistakes, and a gallery of every validation document |
| 4. Journey | The five models we built, their scores and what we set aside |
| 5. Data & gaps | Where the data came from and the known weaknesses |
| 6. Decide next | Four decisions for the next phase, with our recommendation. The supervisor picks options and adds comments; **Save meeting notes** writes them to `meeting-notes/` |

## Suggested 10-minute meeting script

1. **Overview (1 min).** "The classifier is done: photo in, one of four document types out, with the reason." Point at 23/25 and read the "What the 92% means" box aloud.
2. **Live demo (4 min).** Show a printed-rule decision (any purchase order), then a learned-model decision (any receipt) and its word chart. Open the *Mistakes* filter and show one. If time allows, press **Run live** or upload a fresh photo.
3. **Results (1 min).** The confusion matrix shows the only errors are customer copies.
4. **Journey + Data (2 min).** 46% → 92%, why the transformer was not kept, and the main gap: no independent real-document test yet.
5. **Decide next (2 min).** Go through the four questions with the supervisor, then click **Save meeting notes**.

Bookmark a specific document with `#demo/<id>`, for example http://127.0.0.1:8780/#demo/76cc99d39da4.

## Before the meeting

- Open the showcase once on the presenting laptop. The status pill (top right) should say **Model ready · local**.
- If Google Drive is streaming this project, open it while online once, or mark the project folder *Available offline* in Drive.
- If the pill says **Recorded mode only** or **OCR missing**, steps 1 and 3–6 still work fully; only *Run live* and upload need the model and Tesseract.

## Requirements

- Windows, Python 3.12+ with `scikit-learn==1.9.1`, Pillow, numpy and joblib (`py -m pip install -r classifier/requirements-demo.txt`). The launcher finds a suitable Python automatically.
- Tesseract OCR on PATH, for live mode only.
- HEIC uploads also need `pillow-heif`; otherwise convert phone photos to JPEG.

## What is in this folder

| Path | Purpose |
|---|---|
| `Open Showcase.cmd` / `Stop Showcase.cmd` | One-click start and stop |
| `start.ps1` / `stop.ps1` | The same, from PowerShell (`.\start.ps1 -Port 8781 -Open` if 8780 is busy) |
| `server.py` | Local server (127.0.0.1 only). Reads the selected model and its saved evidence from `../classifier/engine/`; nothing is copied or retrained |
| `web/` | The page: `index.html`, `styles.css`, `app.js` |
| `data/showcase.json` | Every fact and figure shown, with the source file for each. **Edit text here**, for example to change a decision option before the next meeting |
| `meeting-notes/` | Saved supervisor decisions (`.md` to read, `.json` for the record). Earlier meetings also appear at the bottom of step 6 |
| `tests/` | Automated checks: `py -3.14 -m unittest discover -s supervisor_showcase/tests` |
| `.runtime/` | Server logs |

## Honesty rules this showcase follows

- "Recorded run" results are the selected model's saved outputs on the 25 validation documents. "Live" results are computed on the spot.
- 23/25 is adaptive development validation, not independent accuracy. The page says so wherever the number appears.
- Model scores are shown as relative preferences, never as probabilities.
- Uploaded photos are analysed in memory and not saved.
- A test checks that the headline numbers match `classifier/engine/runs/printed_v3_explainable/completion.json`, so the page cannot quietly drift from the recorded results.
