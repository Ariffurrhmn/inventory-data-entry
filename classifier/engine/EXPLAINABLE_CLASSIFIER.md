# Explainable printed classifier — 2026-10-20

Selected saved pipeline: **runs/printed_v3_explainable/**, through active_text_model.json.

**Development validation:23/25 (92%), macro-F1 .9211.** A training-only grouped out-of-fold check reaches146/150 (97.3%), macro-F1 .9480. The old27 test inputs remain excluded. Both figures are development evidence: model folds exclude held-out groups, but preprocessing/rule design and validation selection are adaptive, not a fully nested or independent final evaluation.

The user requested continuing experiments toward90% or close, avoiding repeated UI demonstrations, and requiring explainable AI. This iteration crossed90% in the above development checks and added measured explanations. The existing server was deliberately not restarted or demonstrated again; it may still have the old MiniLM model in memory. The launcher will load the selected new pipeline on the next user launch. Do not describe the old running process as already serving this candidate.

## What actually improved

The final system is a **hybrid**, not a BERT classifier with92% standalone accuracy:

1. Tesseract full-page OCR after local illumination correction supplies the learned classifier.
2. Independent sparse, edge, corrected-full and rotated-title views recover printed type/copy evidence.
3. Each OCR view gets its own title window, preventing headings in later views being ignored.
4. Conservative printed-text rules may select a unique class; conflicts use the learned fallback.
5. A training-group-CV selected word/bigram TF-IDF + ComplementNB classifier supplies the fallback.
6. The decision records either the matched rule/evidence or exact learned feature contributions.

No model sees reviewed reference transcription, annotation notes, image filenames or sample IDs as features. No handwriting model, downstream extraction, new raw dataset, human verification or fresh holdout was created.

### Measured comparisons

| Experiment | Development validation |
|---|---:|
| Previous MiniLM + heading/edge pipeline | 20/25,80% |
| Class-balanced contrastive MiniLM adaptation,40 steps | 16/25 standalone;20/25 with old rules |
| Corrected/rotated OCR with old MiniLM, sparse fallback input | 21/25 |
| Corrected/rotated OCR with old MiniLM, corrected-full input | 22/25 |
| Corrected/rotated OCR with old MiniLM, combined input | 22/25 |
| Retrained word/character LR + old rules | 20/25 |
| Retrained character LR + old rules | 20/25 |
| Retrained ComplementNB + old rules | 22/25 |
| Retrained MiniLM/LR + old rules | 22/25 |
| ComplementNB + copy/intent recovery | **23/25,92%** |
| Same model + independent per-view title windows (selected) | **23/25,92%** |

The four recovered-OCR classifiers were ranked by aggregated three-fold training-group macro-F1, not by the25 validation labels. Pure learned training OOF correct counts were64/150 word/character LR,59/150 character LR,77/150 ComplementNB,70/150 MiniLM/LR. ComplementNB won with macro-F1 .3583. Its standalone validation was15/25; rules/OCR recovery provide much of the final gain. None of these standalone results supports claiming that a neural model alone reached90%.

With copy/intent rules over the selected fold-specific fallback, training OOF was129/150. Fixing view-boundary handling raised this to146/150 without refitting or changing the model. The previous combined string allowed only the first30 total lines as title candidates, so recovered headings in later OCR views could never count as titles. Separate form-feed-delimited views each now get their own title window. Rules remain adaptive development logic, so97.3% is not an unbiased final estimate.

### Data isolation and preprocessing

Same saved printed split:150 train (PO36,R56,DN50,CC8),25 validation (PO10,R3,DN3,CC9),27 historical test excluded. Three shuffled StratifiedGroupKFold folds use seed42 and known development_group. Vocabulary, IDF and classifiers fit inside each training fold. Company Documents v2 remains one generator group; known Bridge development templates remain together in validation. Exhaustive provenance independence is unproven.

Uniform preprocessing ran once for all175 non-test images. Preserve raw images. EXIF-normalize, upscale to minimum width1600 capped3x, estimate local grayscale background with Gaussian radius24, divide image by background, then full-page PSM6. Threshold at190 on the normalized image, crop the top40%, and run PSM11 at rotations-12,0,+12. This is versioned in illumination_ocr.py and each cache's policy. Separate original PSM11 and top/bottom edge OCR remain available for rule evidence. The learned input is corrected full-page text only.

Contrastive adaptation trained only the final two MiniLM layers, with two distinct training groups per class in each batch,40 steps, lr2e-5, temperature .1 and seed42. Checkpoints20/40 and losses are retained. It did not improve the hybrid and was not selected.

### Rules and ambiguity

Existing title/copy patterns are preserved. Two additional conservative rules:

- The long copy marker “duplicate” may differ by one OCR insertion/deletion/substitution. Return the raw fragment, canonical word and edit distance. For example, observed “uplicate” is explicitly recorded as an OCR-tolerant match, never presented as verbatim correct OCR.
- A purchase request needs all three printed field groups: order number/date, required-by/date, and “please supply” or request goods/items. Return all matched terms. Order number alone does not establish purchase_order.

Combine matches across views. Different class cues remain ambiguous and use the learned fallback; no arbitrary copy/order precedence or merchant-specific rules are introduced. Source view index-1 denotes merged-context evidence; nonnegative indices refer to individual OCR sections.

## Explainability

Every prediction includes a cheap decision_trace with selected component, rule matches, conflicts, learned top/alternative classes and uncalibrated score margin. classifier_app.py now includes a full explanation by default in its classification response (request explain=false to omit it). classifier.html renders “Why this prediction?” with readable evidence. These source changes were statically checked; the UI was not reopened.

Three explanation paths are implemented:

- **Printed rules:** actual normalized matched text, rule kind and matched field terms. OCR-tolerant copy recovery also identifies the canonical word/edit distance. It states that a rule selected the label and identifies the learned fallback's different label if any.
- **Linear/ComplementNB models:** exact target-versus-alternative log-score contributions from active n-grams. Feature value times learned weight difference, plus the intercept, reconstructs the model's score contrast. Supporting and opposing terms are shown. These are model associations, not proof of correct document type.
- **Transformer models:** fixed-model token-block omission. Record how the score and label change when a block is removed, without fitting an explainer or generating a rationale. These are local sensitivity measurements; interactions/truncation and unnatural deletion inputs limit causal interpretation.

All25 selected validation predictions and explanations are saved in the selected run:18 heading traces,2 purchase-intent traces,5 exact model explanations. Largest algebra reconstruction error was2.27e-14. Saved-model inference reproduced all25 predictions. Five learned fallbacks include the two remaining errors; their explanations are preserved rather than hidden.

For example, the missed customer-copy record cdd7aaa9004d is predicted purchase_order. Its copy stamp was not adequately read, and “dhaka”/“10 dhaka” are strong learned supporting features for the wrong label. That is evidence of a problematic learned association, not a defensible business reason to call it a purchase order. Explicitly exposing it supports collecting better copy data and recovering the actual stamp instead of inventing a persuasive explanation.

Explain an existing OCR file directly:
```powershell
$pythonPath=(Get-Content services/document_classifier/runtime.local.json -Raw | ConvertFrom-Json).python
& $pythonPath services/document_classifier/explain.py --text-file 'C:\path\ocr.txt' --output 'C:\path\explanation.json'
```
Use --heading-file when separate region OCR exists, and --run to explain an older saved model. Canonical input for the selected model is corrected-full OCR, not sparse OCR or a reviewed transcription. JSON evidence stays local. No third-party model inference is used.

## Artifacts and checks

- printed_v2_illumination/: specification, uniform175-image unreviewed OCR cache, code/policy and three comparisons.
- printed_v2_contrastive/: training specification/code, two encoder checkpoints, LR heads, loss trace and negative results.
- printed_v2_explainability/: earlier MiniLM error sensitivity audit; preserved as historical evidence.
- printed_v2_groupcv/: model specifications, training fold assignments, four models and their CV/validation results.
- printed_v2_rules/: copy/intent rule recovery and129/150 training OOF evidence.
- printed_v3_sections/: view-boundary fix and146/150 training OOF evidence, plus23/25 validation.
- printed_v3_explainable/: selected portable sklearn model, selection/dependency hashes, source snapshots, predictions,25 explanations and previous active pointer.
- explain.py, test_explanations.py and test_recovered_workflow.py: faithful explanation implementation and controls.
- EXPLAINABLE_CLASSIFIER.md: this handoff.

Thirty workflow tests pass. Controlled explanation tests independently reconstruct model log-score contrasts, compare omissions against actual score changes, retain ambiguity and exercise image-to-section routing without re-running OCR. UI JavaScript passes node --check. No new UI demonstration/server restart or repeated image-upload smoke series was performed. The175-image OCR generation was the necessary new experiment, not repeated demo inference.

Original source labels/manifests/splits, scope manifest, prior model and historical evaluation match six protected hashes. Original images/references/review history were not rewritten. Current ComplementNB inference uses the base sklearn environment and does not require the optional C: Hugging Face cache; all older transformer weights remain preserved for older runs.

## Remaining limits and next evidence

Validation recall:PO10/10,R3/3,DN3/3,CC7/9. Two red-stamped customer copies remain wrong. Four training OOF errors remain (two customer copies, two delivery notes). Only eight customer copies are in training; all three validation delivery notes are printed synthetic photos. Existing labels/reference reviews are not independently human-verified, and payment/language/taxonomy questions remain.

The90% development target has been crossed, but **independent real-world90% accuracy has not been demonstrated**. Reused validation and adaptive rules can overstate generalization. Keep the historical test excluded. Next useful work is an independent real printed holdout and additional customer-copy families; color/region OCR for faint stamps is a plausible unimplemented next experiment.

Implementation references:
[ComplementNB documentation](https://scikit-learn.org/stable/modules/generated/sklearn.naive_bayes.ComplementNB.html),
[Sentence Transformers loss overview](https://www.sbert.net/docs/sentence_transformer/loss_overview.html).
Reported numbers above come from local saved experiment artifacts, not these references.

