# Transformer experiments — 2026-10-20

Measured locally on CPU using the same printed-only development split: 150 training, 25 validation. No historical test images or OCR were opened. These are adaptive comparisons on reused validation, not final accuracy estimates.

The active classifier is now **printed_v1_minilm**, selected at 20/25 (80%), macro-F1 .8036, versus the previous 19/25 (76%), .7657. This is one additional correct document on a small validation set. Existing printed-heading rules and edge OCR remain part of the selected pipeline.

## Actual comparisons

| Approach | Standalone correct /25 | With unchanged heading/edge rules /25 | Hybrid macro-F1 |
|---|---:|---:|---:|
| Previous TF-IDF + logistic regression | — | 19 | .7657 |
| Frozen MiniLM, balanced logistic regression C=1 | 13 | **20** | **.8036** |
| Frozen MiniLM, balanced logistic regression C=10 | 13 | 20 | .8036 |
| Fine-tuned small BERT, epoch4 | 2 | 17 | .6737 |
| Fine-tuned small BERT, epoch8 | 3 | 17 | .6737 |
| Fine-tuned small BERT, epoch12 | 3 | 17 | .6526 |
| MiniLM + word/character feature fusion, C=1 | 13 | 19 | .7652 |
| MiniLM + word/character feature fusion, C=10 | 12 | 19 | .7652 |

C=1 wins the MiniLM tie by candidate order. No result uses reference transcriptions, review notes, filenames or sample IDs as learned features. OCR text is unreviewed cached Tesseract PSM11. Train/validation split and cache checksums are retained. All existing raw datasets, references, frozen splits and older models remain intact.

Active validation recall: purchase_order9/10, receipt3/3, delivery_note3/3, customer_copy5/9 (previously4/9). Four customer copies and one purchase order remain wrong. One customer copy that was previously classified as receipt is now classified as purchase_order, so individual error types can change.

## Methods

**MiniLM:** frozen sentence-transformers/all-MiniLM-L6-v2. Following its model card, use attention-masked mean pooling and L2 normalization. Encode the first254 and last254 wordpieces independently (plus special tokens) and concatenate their384-dimensional vectors. This preserves both title and footer information; for short pages the two views repeat. Fit balanced logistic regression only on150 training vectors. Evaluate C=1 and10. Encoder weights are not fine-tuned.

**Small BERT:** google/bert_uncased_L-2_H-128_A-2, 4,386,436 parameters with the new four-class head. End-to-end training uses first127 plus last127 wordpieces when necessary, AdamW lr5e-5, weight_decay .01, inverse-frequency weighted cross entropy, batch8, gradient clipping1, seed42, 12epochs. Compare saved epochs4/8/12. Training correct counts were123/150,136/150,143/150, while validation was2/25,3/25,3/25. This run fits training much better than the held-out document families; it provides no reason to promote BERT or claim larger models will solve the data gap.

**Fusion:** training-fitted word1–2 and character_wb3–5 TF-IDF, normalized jointly, concatenated with jointly normalized frozen MiniLM vectors. Balanced logistic regression C=1/10. Vocabulary and IDF fit on training only. No improvement.

The hybrid comparison applies exactly the previous unambiguous heading rules to full-page OCR plus the previous cached top/bottom region OCR. Region text never enters the learned classifiers. Ambiguous copy/order headings use the learned fallback. Receipt/customer-copy taxonomy and missing/faint copy text remain limitations.

## Saved evidence and operation

- runs/printed_v1_transformers/: specification saved before fitting, split, input hashes, features, LR artifacts, three BERT checkpoints, every validation prediction, metrics, training diagnostic and public-model sources.
- runs/printed_v1_fusion/: separate adaptive follow-up specification, training-fitted features, two models and results.
- runs/printed_v1_minilm/: activated offline inference adapter, LR, selection, previous pointer, public-weight manifest, hashes, copied edge OCR/rules, validation and smoke evidence.
- train_transformers.py, train_transformer_fusion.py, package_transformer.py reproduce the versioned sequence; completed output directories refuse overwrite.
- transformer_models.py implements local-only inference; inference.py checks its hash against the saved selection.
- requirements-transformers.txt adds the optional transformer dependencies to the existing environment (Transformers4.57.6, PyTorch2.14.1 CPU).

Public weights are downloaded from the publishers, **not remote inference**. Document text stays local. Both model cards declare Apache-2.0:
[MiniLM model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2),
[Google small BERT model card](https://huggingface.co/google/bert_uncased_L-2_H-128_A-2).
Implementation reference: [Hugging Face text classification](https://huggingface.co/docs/transformers/tasks/sequence_classification).

Pinned public revisions are recorded in *_source.json: MiniLM1110a243fdf4706b3f48f1d95db1a4f5529b4d41, small BERT30b0a37ccaaa32f332884b96992754e246e48c5f. Downloaded files and tokenizer hashes are recorded. The large public weights remain in the local C: visualization runtime's hf-cache, outside the Drive project. The active joblib references that absolute cache path; moving machines requires restoring the exact pinned snapshot and updating/repackaging the adapter, not only copying joblib. Inference uses local_files_only=True and verifies cached-file hashes. Source model cards/notices remain in that cache.

Saved encoder features and all25 selected predictions were independently reproduced after packaging. Twenty-one workflow tests pass; the restarted app uses the new run. Four actual validation image uploads reproduced cached predictions exactly; three were correct, one customer copy remained wrong. Empty OCR and invalid-image requests were rejected. Browser text classification also completed; a fabricated DEMO used only for interface checking was classified customer_copy and is not benchmark data. See the active run's smoke_validation.json.

## Limits and next experiments

There are only eight customer-copy training examples, while nine are in validation. Validation has just three delivery notes, all printed synthetic Bridge photographs. Known development families are separated, but exhaustive source independence is unproven. Validation has now been reused repeatedly. No fresh real holdout was collected and no independent generalization improvement has been established.

The next useful work is broader printed customer-copy data from different merchants/templates, followed by a fresh real holdout. Further CPU-feasible model work could compare contrastive adaptation of the frozen encoder and multiple grouped training-only folds; keep the current25 as development evidence and do not tune on the historical test.

