# Shared context — start here

This folder is shared by the project team, Codex, and Claude. It replaces the old use of Context/ as a mixed document-working folder; that material is preserved in docs/design/.

Read in this order:
1. PROJECT.md — purpose, boundaries, proposed architecture, evidence.
2. STATUS.md — current state, next work, uncertainties.
3. DECISIONS.md — established scope and unresolved choices.
4. ORGANIZATION.md — where files belong and what moved.

After a meaningful session, update STATUS.md with the date, actual work, validation, and next step. Record decisions with their source and rationale in DECISIONS.md. Keep these notes concise; link to primary project files rather than copying entire drafts.

Audit records:
- inventory-before-2026-10-19.csv: original relative paths and byte sizes.
- moves-2026-10-19.csv: old-to-new folder/file mappings.
- inventory-current-2026-10-19.csv: inventory after organization (excluding this inventory itself).

Inspection date: 2026-10-19. This was a filesystem/text-source review, not a full reading of every PDF, Office document, image, or recording.

For classifier work, read CLASSIFIER.md and services/document_classifier/RESULTS.md. Earlier inspection statements and pending-photo notes are historical; the user confirmed photography and the classifier has now been implemented.


For the current text-reference work, read TRANSCRIPTIONS.md and Dataset/annotations/README.md. The five classifier improvement tasks remain paused in PENDING.md.

For the independent review of the other AI's dataset findings and confirmed already-used source flags, read research/datasets/INDEPENDENT_REVIEW.md and source_assessment_flags.csv.

For the completed, separately staged external-data intake, read INTAKE.md and Dataset/intake/2026-10-19/README.md. The old training corpus still has 140 images; 91 accepted additions have not been merged.

For the completed preliminary OCR-text experiment and current runnable text classifier, read OCR_TEXT.md and services/document_classifier/TEXT_EXPERIMENT.md. These supersede earlier statements that OCR/text experiments were still paused or unimplemented.

Latest OCR follow-up: services/document_classifier/DELIVERY_OCR_EXPERIMENT.md records the completed validation-only sparse/combined comparison. No model promotion or new test evaluation. docs/data-collection/FRESH_HOLDOUT.md and Dataset/holdout_real_pending/ contain the collection guide and blank manifest; no new holdout documents collected.

Latest annotation edition: Dataset/annotations/versions/utf8-v2/ fixes UTF-8 decoding damage in 34 text records while preserving all historical annotations/results. Read its README.md before further annotation work. Human review and real holdout collection remain pending.

For the local image/transcription review app, read services/annotation_portal/README.md. Launch Open Portal.cmd there; reviewer records live in Dataset/annotations/human_review/reviews.sqlite3. It displays saved references and OCR-only records, and preserves original annotations.

Latest annotation work: 10 assistant visual reviews saved in the portal, with 3 text corrections and 2 payment-status flags. These are AI, needs_review, human_verified=false. Evidence: Dataset/annotations/audits/assistant-review-batch-01-2026-10-19/applied.json.

Current scope is PRINTED TEXT ONLY (user clarification 2026-10-20). Read Dataset/annotations/scope/printed-only-v1/README.md before further data/model work. Active candidate set: 202; handwriting/handwritten fields excluded and seven mixed pages held. The inherited printed validation split has no delivery notes, so four-class selection needs a new development validation plan. Older mixed-scope statements are historical.

RUNNABLE CLASSIFIER (2026-10-20): services/document_classifier/PRINTED_CLASSIFIER.md is the current handoff. Active printed_v1_edges model and local upload UI at http://127.0.0.1:8767; Open Classifier.cmd restarts it. New grouped development training/validation is150/25; old test27 excluded. Development validation19/25, CC recall4/9; preliminary. Earlier statements that training was blocked or only legacy inference existed are historical.

Latest classifier (2026-10-20): active printed_v1_minilm replaces printed_v1_edges after transformer experiments. Same adaptive150/25 development split;20/25, macro-F1 .8036; no historical test inputs opened. MiniLM frozen encoder + trained LR + unchanged heading/edge rules. BERT fine-tuning and feature fusion rejected. Details: services/document_classifier/TRANSFORMER_EXPERIMENT.md; current usage: PRINTED_CLASSIFIER.md. Public weights are in the configured local C: hf-cache and required for inference.

CURRENT SELECTED CLASSIFIER (2026-10-20): printed_v3_explainable supersedes MiniLM. Corrected OCR + printed rules + training-group-CV selected ComplementNB;23/25 adaptive validation (92%),146/150 training OOF with adaptive rules (97.3%), no historical test inputs. Explainable rule traces/exact n-gram effects;30 tests. Read services/document_classifier/EXPLAINABLE_CLASSIFIER.md and PRINTED_CLASSIFIER.md. Existing server not restarted per user direction; next user launch loads this run. Independent final90% remains unproven. All earlier active-model and in-progress statements are historical.

CURRENT APP / PATHS (2026-10-20): classifier/ is now the canonical top-level classifier folder. Launch classifier/Open Demo.cmd; Document Lab is at http://127.0.0.1:8770. Source/models/history moved to classifier/engine/. Read classifier/README.md and classifier/docs/SUPERVISOR_DEMO.md. Five explicitly recorded development examples plus live image/OCR analysis, explanations and report export/save;43 automated checks and browser walkthrough passed. Historical prepared-image compatibility assets remain at services/document_classifier/data/. Earlier service paths in these notes are historical aliases.


Downstream prototype (2026-10-24): read services/document_pipeline/README.md and its experiments/2026-10-24/ reports. Local port8772 supports OCR/classification, sub-agent JSON handoff, verification, persisted submissions and a demonstration consumer. Automatic extraction backend, generic table localization and reviewed field truth remain boundaries.

Downstream follow-up (2026-10-24): automatic ruled-grid localization and opt-in gateway region evidence are implemented; four of seven eligible development layouts yield grids. Read services/document_pipeline/experiments/2026-10-24/downstream_followup/README.md, automatic_localization/README.md and services/document_pipeline/FIELD_REVIEW.md. Current downstream software suite49 checks; no independent extraction accuracy or installed unattended generative backend. Shared STATUS/DECISIONS record actual measurements and boundaries.

SUPERVISOR SHOWCASE (2026-10-29): supervisor_showcase/ is the folder for supervisor meetings. Launch Open Showcase.cmd (port 8780); read supervisor_showcase/README.md. Saved supervisor decisions are in supervisor_showcase/meeting-notes/. The classifier runtime venv in classifier/engine/runtime.local.json is currently empty; see STATUS.md.
