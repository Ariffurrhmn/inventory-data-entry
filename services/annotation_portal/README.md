# Slip review — local annotation portal

Open http://127.0.0.1:8765 while the local server is running. To start it again, double-click **Open Portal.cmd** in this folder. Python 3.10 or later must be on PATH; there are no packages to install. Opening index.html directly does not provide disk saving.

From the project root:

```powershell
.\services\annotation_portal\run.ps1 -Open
```

Use `-Port 8767` if the default port is occupied, or `-Foreground` to run in a terminal and stop with Ctrl+C. Background launch logs and the process ID are in `.runtime/`. The service listens only on this computer at 127.0.0.1.

## Review a document

1. The initial view contains the 45 records flagged in the existing annotation queue. Use Show, Class, Split or search to select another view.
2. Inspect the image on the left. Zoom, rotate, scroll, Fit or Open the full image as needed.
3. Edit the transcription on the right. Choose the document class, enter your name, and record uncertain regions or review notes.
4. Save as Draft or Needs another review while anything remains unfinished. To mark Verified by me, explicitly confirm that you checked the full text and class against the image and enter your name.
5. Click Save review or Save & next. Ctrl+S saves; Ctrl+Shift+S saves and advances.

Changes are backed up in this browser as unsaved drafts. **Only a successful Save writes the review to the project.** Navigating away and returning restores browser drafts. Server errors retain them. If another tab saves the same document, the older tab cannot overwrite it: download its browser draft, load the new disk record, and merge your edits.

## Find existing or missing text

The portal discovers records from the existing original manifest, frozen splits, preliminary experiment manifest and known OCR cache directories. Current inventory:

- 236 samples total: 145 original candidates plus 91 intake additions.
- 140 have saved reference transcriptions, preferring the UTF-8 corrected edition.
- 91 additional samples have OCR but no reviewed reference transcription.
- Five excluded original samples have no recorded reference/OCR text.
- Human reviews begin empty. Test browser saves used a separate database, never the real review store.

The **Existing text** tab shows the saved reference, initial OCR draft, experiment OCR and sparse OCR when available, with source paths and copy-to-editor controls. Empty OCR sources are displayed explicitly. An OCR file existing on disk does not make it verified truth. Show → OCR, no reference surfaces draft-only records. Show → No reference or OCR surfaces records needing a transcription from scratch. Show → Human reviews saved and the History tab show work already recorded in this portal.

## Storage and exports

Reviews are stored in `Dataset/annotations/human_review/reviews.sqlite3`. Every save creates a new revision in one SQLite transaction. It preserves UTF-8 text, proposed class, original class/split, status, reviewer, uncertainties, notes, timestamps and image/reference hashes. History retains prior versions. A later draft revision removes verified status from the latest review; it does not erase the verified historical revision.

**Export reviews** downloads the latest portal review for every saved sample as JSON. **Export all text** downloads the full discovered catalog including references, OCR, latest human review and review history. Full-catalog export reads the source files and can take longer than opening one document. Neither export includes browser-only unsaved drafts.

Original images, source annotations, OCR caches, trained models, frozen labels and splits are read-only inputs. A class correction is recorded as a proposed human label, not silently applied to training. Reviews are available for a later explicit, versioned annotation adoption step. No automatic training or reference replacement occurs. Human verification is an explicit reviewer declaration, not authentication or an automated correctness check. Review uncertain spans before treating a transcription as exact-character truth.

The inventory is scanned at server startup. Restart the server after adding source records or annotation files. This is a local file-backed review workflow, not a multi-computer collaboration server.

## Verification

```powershell
python -m unittest discover -s services/annotation_portal -p test_portal.py
```

Six tests cover UTF-8 persistence and reopen, retained history, stale-write conflicts, explicit verification, OCR-only discovery, API save/export, invalid writes and local request restrictions. Browser checks additionally covered a two-revision save/reload, browser draft recovery, OCR-only filtering, text-source visibility, image zoom/rotation and layout. QA saves are isolated in `.runtime/qa/reviews.sqlite3`, labelled as automated drafts with human_verified=false.

## AI-assisted reviews

Assistant review records carry reviewer_type=ai and human_verified=false, and remain Needs another review. They are identified by reviewer name and in revision history. A person editing an AI review must enter their own name and explicitly confirm image/text/class review to create a human-verified revision. The save API rejects reviewer_type=ai with verified status. Batch 01 added 10 AI review revisions; see Dataset/annotations/audits/assistant-review-batch-01-2026-10-19/applied.json. Initial inventory counts above describe app creation, not current live review progress.

## Current printed-only scope — 2026-10-20

Content scope defaults to Printed working set (202 candidates; 35 eligible flagged records). Handwriting excluded shows 24 archived samples; Needs printed crop/mask shows seven held images; All samples/history shows 236 historical candidates. Excluded/held records are read-only, preserving prior reviews. Export printed reviews includes only eligible sample IDs; full catalog/history export carries all records with scope flags. Unknown new records require scope screening before admission. Ignore handwriting and signatures in the editor. Eight backend tests pass, including out-of-scope write rejection, history retention, scoped export and unassessed-record exclusion. See Dataset/annotations/scope/printed-only-v1/README.md. Earlier counts describe historical app creation.
