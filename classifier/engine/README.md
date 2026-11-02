# Research engine — retained implementation and experiment history

The current supervisor app starts from ../Open Demo.cmd. Read ../README.md for the demo and EXPLAINABLE_CLASSIFIER.md for the selected printed_v3_explainable model. Historical paths beginning services/document_classifier map to classifier/engine, except retained legacy image/OCR compatibility copies. Do not regenerate datasets to inspect them.

The original historical image-baseline README is preserved below and in ../docs/historical-engine-README.md.

---

# Four-class document image classifier

Predicts purchase_order, receipt, delivery_note, or customer_copy. The historical image baseline is documented below; the preliminary OCR-text classifier is documented in TEXT_EXPERIMENT.md. Table detection and numerical extraction remain outside classifier scope.

## Initial experiment

- Curated JPEG/PNG inputs from the four Dataset/ class folders.
- Dataset/Dataset-2 HEIC phone photographs of printed synthetic documents.
- The separate ChatGPT_Bridge PNG originals, 120-example synthetic corpus, and excluded samples are NOT included. Digital originals already present in Dataset class folders are retained and grouped with related photographs.
- Original inputs are never changed. Derived, EXIF-oriented JPEGs and review sheets are under data/.
- Folder labels require review via labels.csv. Review notes record ambiguities and exclusions.
- Digital originals and their phone photographs share groups; visually related templates also share groups. The split targets 60/20/20 by image count while keeping each reviewed group intact. Unknown relationships can remain; this is an exploratory baseline, not deployment validation.

The model uses ImageNet-pretrained MobileNetV3 Small, freezes image features, and trains the classification head. Full pages are letterboxed at 224 pixels to retain copy markings near page edges. Small text may still be unreadable at this resolution. Model selection uses validation macro-F1 only. An optional second experiment fine-tunes the last two visual blocks with finetune.py; in the initial run it did not beat the baseline, so baseline remains selected.

## Setup (Python 3.12 recommended)

Create a virtual environment on a local disk, rather than inside a cloud-synced dataset directory:

```powershell
py -3.12 -m venv C:\path\to\classifier-env
$py = 'C:\path\to\classifier-env\Scripts\python.exe'
& $py -m pip install Pillow pillow-heif numpy scikit-learn
& $py -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

Run the following from this directory:

```powershell
& $py prepare.py
& $py audit_duplicates.py
# Review data/review_*.jpg and fill labels.csv (project-root source_path,
# label, group_id, label_status=reviewed, include=yes/no, notes).
& $py prepare.py --labels-only
& $py split.py
& $py -m unittest test_workflow.py
& $py train.py --run baseline --epochs 100
& $py evaluate.py --run baseline
& $py predict.py 'C:\path\to\document.jpg' --run baseline
```

The first training run downloads pretrained weights from PyTorch. This downloads model weights only; it does not upload the document images.

## Outputs

- data/manifest.csv: path, provenance, label, dimensions, hash, group, review status.
- data/audit.json: conversion failures, counts, and exact duplicates.
- data/splits.csv and split_summary.json: frozen split assignment and fingerprint.
- runs/baseline/best.pt: model checkpoint and class order.
- training.json: validation history.
- evaluation.json, confusion_matrix.csv, predictions.csv: held-out results.

Prediction returns a label and uncalibrated softmax scores. This model always chooses one of the four classes; it has no out-of-distribution detector or unknown class.

Do not tune against test errors repeatedly. Future experiments should use validation data, preserve this split, and use a new run name. An independent real-document/photo collection is needed for stronger claims. Family grouping by inspection is conservative but not proof of independence.

## References

- [Torchvision MobileNetV3 Small](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.mobilenet_v3_small.html)
- [Pillow HEIF plugin](https://pillow-heif.readthedocs.io/en/stable/pillow-plugin.html)
- [Grouped evaluation](https://scikit-learn.org/stable/modules/cross_validation.html)

## Use the installed classifier on this computer

From this folder:

```powershell
.\run.ps1 -Action predict -Image 'C:\path\to\document.jpg'
.\run.ps1 -Action test
```

run.ps1 uses runtime.local.json to locate the isolated Python environment. It is installed on the local C: drive to avoid synchronizing ML dependencies through Google Drive. On another computer, pass -Python with your environment path. Do not rerun training with the existing run name; preserved results intentionally cause that command to stop.

Read REVIEW.md for six corrected folder labels, five deferred examples, and grouping decisions. data/audit.json describes the initial conversion and original folder counts; data/manifest.csv and data/splits.csv contain the authoritative reviewed labels and included examples. Initial review sheets retain original folder labels.

For a second experiment before its test evaluation:

```powershell
& $py finetune.py --from-run baseline --run my_new_run --epochs 20
```

The first project's selected model and measured results are described in RESULTS.md.
## Preliminary OCR-text classifier

Read [TEXT_EXPERIMENT.md](TEXT_EXPERIMENT.md). Run predict_text.py --image <path> or predict_text.py --text-file <path> with the existing environment. Selection is original_ocr by validation macro-F1; test accuracy is 17/28 (60.7%), versus the historical image baseline 13/28. The augmented model is retained for comparison, not promoted based on its higher test score. This is exploratory and particularly weak on delivery notes.

## Validation-only OCR follow-up

[DELIVERY_OCR_EXPERIMENT.md](DELIVERY_OCR_EXPERIMENT.md) records four sparse/combined OCR comparisons. None beat the existing validation-selected model, so default prediction is unchanged. No new test evaluation was performed. A fresh real holdout collection guide is in ../../docs/data-collection/FRESH_HOLDOUT.md; its manifest is currently empty.

## Current running printed classifier — 2026-10-20

Open [http://127.0.0.1:8767](http://127.0.0.1:8767), or double-click Open Classifier.cmd to launch it. Read [PRINTED_CLASSIFIER.md](PRINTED_CLASSIFIER.md) for the active training result and instructions. classify.ps1 -Image <path> or -TextFile <path> uses the same active model. run.ps1 -Action predict now defaults to active OCR classification; predict-image selects the historical image-only predictor. Active run: printed_v1_edges, 150 training /25 development validation, 19/25 correct (76%), macro-F1 .7657; customer-copy recall4/9 remains a limitation. No new independent test score.
