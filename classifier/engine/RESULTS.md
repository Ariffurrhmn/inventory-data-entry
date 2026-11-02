# Initial classifier results — 2026-10-19

**Status: working experimental baseline; accuracy is insufficient for operational use.**

140 reviewed/included images: 35 purchase orders, 28 receipts, 50 delivery notes, 27 customer copies. Six obvious folder-label corrections and five deferred ambiguous cases are documented in REVIEW.md and labels.csv. Original inputs were preserved.

86 training, 26 validation, and 28 held-out test images. Known original/photo variants and template families stay within one split. This is a small mixed-origin corpus containing photographed synthetic documents; the score is not a measurement of real-shop performance.

## Selected model

ImageNet-pretrained MobileNetV3 Small, full-page 224-pixel letterboxing, frozen visual features, trained classification head. Best validation macro-F1: 0.456. A 20-epoch experiment fine-tuning the last two visual blocks did not beat that validation result, so the frozen-feature baseline was selected before test evaluation.

- Test accuracy: **46.4% (13/28)**.
- Test macro-F1: **0.483**.
- Batch test inference: about 2.5 seconds for 28 images on this CPU, excluding model startup. This is not a production latency benchmark.
- Always predicts one of four classes. Softmax scores are uncalibrated.

| Actual class | Test images | Correct | Recall | F1 |
|---|---:|---:|---:|---:|
| Purchase order | 7 | 2 | 28.6% | 0.250 |
| Receipt | 5 | 3 | 60.0% | 0.667 |
| Delivery note | 10 | 3 | 30.0% | 0.462 |
| Customer copy | 6 | 5 | 83.3% | 0.556 |

## Confusion matrix

Rows are actual classes; columns are predictions.

| Actual / predicted | Purchase order | Receipt | Delivery note | Customer copy |
|---|---:|---:|---:|---:|
| Purchase order | 2 | 0 | 0 | 5 |
| Receipt | 0 | 3 | 0 | 2 |
| Delivery note | 7 | 0 | 3 | 0 |
| Customer copy | 0 | 1 | 0 | 5 |

Interpretation: the model confuses visually similar forms. Small text/copy markings may be lost at 224 pixels; that is a plausible explanation, not a demonstrated causal finding.

## Verified

- All 145 source images decoded; 54 HEIC phone photographs converted to derived JPEGs.
- 140 included after visual label review and grouping.
- Five workflow tests passed: deterministic/group-isolated splitting, duplicate-group conflict rejection, review enforcement, full-page preprocessing, actual split-integrity checks.
- Training completed, checkpoint saved, evaluation completed, and single-image prediction smoke-tested.
- Raw results: runs/baseline/evaluation.json, predictions.csv, confusion_matrix.csv; validation history in training.json.
- Exact runtime dependencies: requirements-lock.txt. Setup/use: README.md and run.ps1.

## Next experiment

Keep this baseline and its split. Use validation data to compare a higher-resolution document model or an OCR-text classifier, since discriminating PO/challan/copy often depends on words. Either approach can still expose exactly the same four-class output, without adding table/number extraction to the classifier. Collect additional independent layouts and real documents for stronger validation. Do not repeatedly select models using these 28 test cases; obtain a fresh independent test set for final claims.
