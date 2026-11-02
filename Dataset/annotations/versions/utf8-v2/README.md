# UTF-8 corrected annotation version

Generated 2026-10-19 from the unchanged original UTF-8 review_actions.json and unreviewed OCR drafts. Start with [review.html](review.html) to compare all 140 images and texts. Machine-readable references are in transcriptions/ and transcriptions.jsonl; index.csv maps stable sample IDs. The 45-record review_queue.csv still requires audit; human_verified remains false everywhere.

This corrects an exporter bug: Python on this Windows installation defaults to cp1252, while review actions are UTF-8. The old exporter decoded review actions without an explicit encoding, corrupting currency and punctuation. The fixed exporter reads UTF-8 directly; no heuristic decoding or content guessing is used. Text changed in 34 records: 32 train, 1 validation, 1 test. Class labels, split assignments and image metadata did not change. This is an encoding repair, not a fresh visual review of all images.

The original annotation files one directory tree above and all historical model/results remain preserved. Use this version for future annotation review. Prior experiment reports describe the older annotations and are not silently recalculated. Existing OCR-model inference still uses its saved model and policy. No classifier training or new test evaluation occurred.

Encoding audit: ../../audits/utf8-2026-10-19/report.json and changes.jsonl. The audit verified 863 historical files unchanged; the original annotation README was intentionally updated after verification. All 140 image links and prepared hashes were checked. Two training images received visual spot checks; uncertain handwriting was left unresolved.

To create another version, run from services/document_classifier with the configured Python environment:

```
python reference_annotations.py export --output <new-absolute-directory>
python finalize_annotations.py --annotations-dir <new-absolute-directory>
```

The exporter refuses an existing version output directory. Review instructions are still sourced from Dataset/annotations/review_actions.json; preserve a UTF-8 copy with each version. Exporting without --output uses the legacy location and can overwrite historical references, so use a new directory. Packaging rebuilds derived review files in the selected directory.
