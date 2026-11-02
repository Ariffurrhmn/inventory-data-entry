# Printed-only scope edition — 2026-10-20

The user explicitly excluded handwriting from the classifier task. This edition screens the existing 236 candidates for printed text content, while preserving all original files, references, review history, labels, splits and experiment artifacts.

## Working set

202 scope-eligible candidates: 52 purchase orders, 64 receipts, 63 delivery notes, 23 customer copies. These comprise 116 of the original 140 included images and 86 of the 91 accepted additions. Scope eligibility is not verified transcription/label truth, license clearance or a new real-document collection claim.

24 catalog images have handwritten or handwriting-style transaction bodies/fields and are outside scope; two were already excluded historically. Seven otherwise printed images with handwritten tips, totals, numbers or margin notes are held until reviewed printed-only crops/masks exist. Three printed catalog images retain their previous unrelated exclusions. Thus the previous 231 included candidates reduce by 29 to 202. No source image was deleted or altered.

Physical printing does not make handwriting-style body text eligible: photographs of printed synthetic handwritten forms are still outside the requested task. Ordinary typeset/thermal documents and photographs of them remain candidates. Incidental signatures may remain in an image but are not transcription targets. Pen circles without handwritten text are not themselves a handwritten-document class. Do not transcribe handwritten notes, signature names or added monetary values.

All 236 images received a visual content-style screen using the contact sheets retained here, with enlargements for selected mixed cases. This was not a new complete transcription audit. Decisions are AI-reviewed, human_verified=false. Some historical references/OCR contain signature markers or handwritten text and remain preserved as history; they are not automatically a clean printed-only text corpus. No algorithmic claim of removing every signature stroke from legacy OCR is made.

## Files

- policy.json: admission policy and boundaries.
- decisions.json: per-image style decisions, reasons and evidence.
- source_inventory.json: input inventory at screening time.
- manifest.csv: all 236 candidates with scope status, original inclusion/split/group, and checked image hashes.
- eligible_manifest.csv: the 202-record printed-only candidate subset for future work.
- excluded_or_held.csv: 24 handwriting, seven region holds and three prior exclusions.
- review_queue.csv: 35 previously flagged records still eligible for printed review.
- validation.json: scope counts and 147 protected-file hash checks.
- evaluation_readiness.json: per-class split counts and the validation gap.
- contact_sheets/: visual screening evidence; cell indices map to decisions.json.

Dataset/annotations/scope/active.json points the portal to this edition. New unassessed samples are not automatically admitted. The portal defaults to Printed working set, while excluded/held images and saved review history remain accessible read-only. Export printed reviews excludes out-of-scope saved reviews; Export catalog/history retains full provenance with scope flags.

## Evaluation gap

The inherited subset has 162 training, 13 validation and 27 historical test images. All six delivery notes in the previous validation set were handwritten, leaving zero delivery notes in the printed validation subset. Do not select a four-class model using that validation subset alone. Acquire printed delivery notes from new development families, or explicitly version a new grouped development split from non-test families. Do not pull exposed test documents into development or call the historical test fresh.

Existing mixed-scope experiment metrics and saved models remain unchanged. No retraining or model evaluation occurred. The old default predictor is a legacy experimental model, not a newly trained printed-only classifier. Historical run_text_experiment.py and image-training workflows still use historical manifests; do not run them as a new printed-only experiment without an explicit new manifest/split-aware runner.

To create a future edition, copy the policy/decision/inventory sources to a new directory, update decisions based on evidence, then run services/document_classifier/build_printed_scope.py --directory <new-directory> --activate. Completed editions refuse overwrite. Tests and current portal checks are documented in portal_validation.json.
