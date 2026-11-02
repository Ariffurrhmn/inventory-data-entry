# Paused classifier improvement plan

User requested 2026-10-19: put the five-point plan on hold while preparing image-linked text reference transcriptions for the 140 included images.

Paused:
1. OCR extraction/cache experiment (annotation drafting may use OCR solely as an aid).
2. OCR quality experiment against references.
3. Text-only classifier training.
4. Text/image/fused validation comparisons.
5. External dataset import workflow.

Current authorized work: JSON reference transcriptions for the existing 140 included images. Preserve class labels, train/validation/test membership, originals, and existing models. Do not train or run classifier experiments as part of annotation.
## Authorization update — 2026-10-19

The user approved the proposed ExpressExpense review and bounded synthetic-data intake. External intake is now authorized only for staging and reviewing these additions separately: the 200-image SRD release and a target of 20 English Company Documents v2 purchase orders plus 20 packing slips. Preserve the existing corpus and splits; do not merge or train. OCR screening is allowed as an intake labeling aid and does not resume the OCR quality/classifier experiments. Other improvement tasks remain paused.

## Bounded intake completed — 2026-10-19

The approved staging/review is complete: 91 accepted additions, 140 held, 9 excluded from 240 reviewed candidates. Files are in Dataset/intake/2026-10-19/. This did not resume or complete corpus merge, OCR evaluation, text training or fusion experiments. Existing 140-image splits are unchanged. See INTAKE.md.

## Preliminary OCR-text experiment authorized — 2026-10-19

The user approved continuing with grouped experimental training, OCR-quality measurement and a TF-IDF/logistic-regression comparison using the frozen original benchmark and eligible staged additions. This resumes those bounded experiments. Preserve existing data/splits.csv, source annotations and image baseline; additions enter a new experiment manifest as training-only after group/duplicate guards. Human verification of references is still pending; results must be labeled preliminary. Image/text fusion, LLM extraction and application integration are not resumed by this experiment.

## Preliminary experiment completed — 2026-10-19

The newly authorized preliminary OCR extraction/quality/text-classifier comparisons are completed, including a separate training-only augmentation manifest and preserved baseline. See OCR_TEXT.md for measured results. Human auditing and a fresh real-document holdout remain pending; no image/text fusion or LLM/application integration was performed. Do not treat earlier pause entries as evidence that the completed OCR-text prototype does not exist.

## Validation-only OCR recovery authorized — 2026-10-19

User requested continuing after the preliminary report. Investigate readable text missed on train/validation delivery pages; compare sparse-text OCR and combined OCR with original-only/augmented training using fixed classifier settings. Preserve and do not rerun the exposed historical test. Prepare a real-holdout collection guide/template; no claim that real holdout data has been collected.

Completion of authorized follow-up: sparse/combined OCR comparisons and the fresh-holdout collection kit are finished. None of the four candidates beat the previous validation-selected model; no promotion and no new test evaluation. See services/document_classifier/DELIVERY_OCR_EXPERIMENT.md. Real holdout collection and independent annotation review remain pending; the collection manifest has no image rows. This follow-up did not implement fusion, downstream extraction or app integration.

Annotation continuation completed: corrected the Windows UTF-8 exporter bug and created a preserved new edition at Dataset/annotations/versions/utf8-v2/. Thirty-four text records repaired; 45 queue records still need independent review. This is not human verification and did not train/evaluate another classifier.

The human-review interface is now implemented in services/annotation_portal/. User/team annotation review is pending, with zero real reviews at app creation. Saves are separate reviewer revisions; applying them to a new canonical reference edition remains a later explicit step.

Printed-only scope completed 2026-10-20: 202 candidates activated; handwritten body/forms excluded and seven mixed pages held. Before retraining, establish printed delivery-note validation coverage without moving historical test records into development. Human review and printed-only derivative creation remain pending; no handwriting transcription work is authorized under current scope.

Printed training/runnable inference completed 2026-10-20. Missing development delivery-note coverage was resolved by a new grouped non-test split. Remaining: clearer customer-copy OCR/training coverage, independent label/reference audits, fresh real holdout, and any explicitly requested downstream extraction/integration. Active prototype19/25 development validation; no new test evaluation.
