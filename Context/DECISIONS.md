# Decisions and open questions

## Established scope (from existing report and presentation sources)

- Build a cloud document-digitization gateway consumed by an external ERP.
- Keep mobile capture thin; no on-device model execution.
- Recognize four document classes and extract schema-constrained records.
- Use arithmetic validation plus confidence flags; no internal human confirmation workflow.
- Leave inventory state and item matching to the consumer.
- Keep this version English-only.

These summarize existing project choices, not new implementation decisions.

## Open implementation choices

The written materials describe OCR/LLM provider selection, schema enforcement, confidence signal, taxonomy/classifier refinement, and API/data-model details as decisions requiring implementation/evaluation. Defaults in a presentation are proposals, not proof of a selected working stack. Validate against report Table 3.3 before locking choices.

## 2026-10-19 — shared memory and organization

User requested understandable organization and common context for Codex and Claude. Keep shared project facts in Context/ with small root AGENTS.md and CLAUDE.md entry points. Move editable writing into docs/, prepared submissions into deliverables/, and papers into research/literature/. Retain data/bridge/figure paths because tooling depends on them. Preserve all original versions and provenance.

## User clarification and classifier scope — 2026-10-19

The user confirmed printing the synthetic/generated documents and photographing the printed copies. Dataset/Dataset-2 contains those phone photographs (54 HEIC files: 21 purchase orders, 24 delivery notes/challans, 9 customer copies). Printing/photography is complete for this material; earlier pending notes are historical. These are photographed synthetic documents, not real business transactions.

The classifier scope is ONLY four-class image classification: purchase_order, receipt, delivery_note, customer_copy. Table/region detection and number extraction are not classifier responsibilities. LLM extraction is a separate downstream stage. The user authorized preparing data and implementing/training this classifier. Work is under services/document_classifier/. Generated originals are excluded from the initial experiment to avoid original/photo leakage; curated provenance is not assumed real.

## 2026-10-19 — public candidate research boundaries and next input direction

Source: user's dataset-research request. Classifier input will use OCR text obtained from a document photograph/scan; output stays exactly the four established classes. This clarification does not retroactively change the completed image baseline or claim an OCR classifier exists.

Keep downloaded public samples in Dataset/external_candidates/ and research evidence in research/datasets/. Do not merge, train, or replace existing splits during dataset assessment. Treat synthetic generated/degraded pages as synthetic, extraction-region labels as distinct from document labels, and source-provided clean text as distinct from project OCR. Known template/original/photo and cross-source duplicate relationships must remain grouped in future splits. The report's balanced intake targets are recommendations, not adopted measured results.

Pending taxonomy decisions (not resolved here): precedence when PO/delivery documents also have accepted copy markings; eligibility of goods received notes and invoice/delivery hybrids. Established Office Copy/Guest Copy/Duplicate treatment remains unchanged.

## 2026-10-19 — reference annotation scope and pause

Source: user requested text transcriptions against the existing 140 included images, and asked to put the five classifier improvement tasks on hold. Use per-image JSON with source identity, visible text, provenance and transparent review/uncertainty metadata. OCR may assist drafting; visually reviewed references must remain distinct from raw OCR. Do not claim independent human verification. Preserve originals, labels, fixed splits and models; no classifier experiment or external import during annotation. Paused tasks are recorded in PENDING.md.

## 2026-10-19 — bounded staged intake authorized

User accepted the proposed ExpressExpense review and small English synthetic PO/packing-slip intake. Keep additions under Dataset/intake/2026-10-19 with source bytes, notices, review reasons and duplicate links. Do not merge with the original 140, change their splits or train in this task. Conservative labels require visible payment evidence for new receipts and accepted explicit copy cues for customer_copy; unresolved restaurant bills remain held, not negative labels. Synthetic examples share one generator family and are training supplements only. Assistant visual labels are not independent human verification. Other implementation experiments remain paused.

## 2026-10-19 — preliminary text experiment and selection discipline

User approved the preliminary OCR-text experiment after intake. Keep the existing 140-image benchmark and protected references immutable, with new accepted data training-only in a separate experiment manifest. Use fixed TF-IDF/logistic-regression settings and select an OCR-input candidate using validation macro-F1 before test prediction. Original-only OCR won validation and stays selected despite the augmented run winning this small exposed test. Do not promote it retrospectively based on test. OCR scoring excludes whole records with any uncertainty/marker rather than deleting unresolved spans without alignment; all reported reference metrics remain preliminary and AI-reviewed.

## Retain original OCR candidate after validation follow-up — 2026-10-19

User authorized continuation. Tested PSM11 sparse OCR and unique-line PSM3+PSM11 combinations with original-only and augmented training, keeping the classifier configuration fixed. Best new validation macro-F1 .726 did not exceed .782; retain text_preliminary/original_ocr as default. More OCR text alone did not improve classification. No new test evaluation or promotion. Fresh holdout collection is planned separately; an empty manifest is not acquired data. See services/document_classifier/DELIVERY_OCR_EXPERIMENT.md.

## Preserve historical annotations during encoding repair — 2026-10-19

Use explicit UTF-8 when loading annotation review actions. Re-export into a new version instead of overwriting references used by measured runs. Dataset/annotations/versions/utf8-v2/ is the corrected reference edition for future work; older experiment metrics remain attached to the preserved original annotations. Encoding repair does not set human_verified=true or resolve uncertain handwriting.

## Annotation portal saves separate reviewer revisions — 2026-10-19

User authorized a local HTML review app and persistent records. Use services/annotation_portal/ with a loopback-only standard-library Python server and SQLite revisions under Dataset/annotations/human_review/. Save new human reviews separately from immutable reference editions and original model labels/splits. Class edits are proposals for later adoption. OCR caches without references remain visible as OCR-only samples. Explicit reviewer identity and checkbox confirmation are required for verified status; automated UI tests use an isolated database and never assert human verification.

## AI review provenance — 2026-10-19

User-authorized assistant reviews must be recorded as reviewer_type=ai and human_verified=false. They may append a needs_review revision after an unchanged unnamed draft, preserving history; edited/named human reviews and concurrent saves require explicit merge rather than replacement. AI review cannot assert human verification. First completed batch: Dataset/annotations/audits/assistant-review-batch-01-2026-10-19/applied.json.

## Printed-only classifier inputs — user clarification 2026-10-20

User stated that handwritten notes are not part of the task. Exclude handwritten/handwriting-style bodies and handwritten transaction fields on printed templates from new working inputs; physically printing synthetic handwriting does not change this decision. Hold mixed printed pages with handwritten notes/values until reviewed printed-only derivatives exist. Printed pages with incidental signatures may remain, with signature content ignored. Preserve original data/history; use versioned scope manifests instead of rewriting frozen experiments. Portal archives are read-only and printed exports respect scope. Active edition: Dataset/annotations/scope/printed-only-v1/. No retraining or revised performance claim until all four classes have development validation coverage.

## Train and activate printed prototype — user authorization 2026-10-20

User prioritized a running classifier ASAP. Preserve original splits and exclude historical test inputs; create a new versioned development split merging known Bridge template groups across classes into validation, keeping Company Documents generator together in training. Train fixed TF-IDF/logistic models and record adaptive heading/edge-OCR follow-ups separately. Activate printed_v1_edges after development validation and persisted-model checks. Explicit headings may select a class; ambiguous copy/order hybrids use trained fallback. Statistical scores stay uncalibrated and are not invented for rule-selected labels. No real-holdout accuracy claim. Use the local upload UI and classify.ps1 as current entry points.

## Transformer selection and local weights — 2026-10-20

User explicitly authorized trying new classifier architectures. Keep the frozen printed150/25 development split and exclude historical test inputs. Compare MiniLM frozen semantic features, small BERT fine-tuning and lexical/semantic fusion in versioned runs; retain all unsuccessful candidates. Promote MiniLM C1 plus the unchanged heading/edge rules because development macro-F1 .8036 exceeds .7657; C10 ties, so earlier C1 wins. State the small one-record gain and adaptive validation limits. BERT/fusion were not promoted.

Keep document OCR and inference local. Cache publisher weights outside Google Drive in the configured C: runtime, record pinned public repository revisions/license/file hashes, and require local-files-only loading with integrity checks. Active joblib references the cache; moving installations requires restoring the exact snapshot and repackaging. Do not describe the selected system as fully fine-tuned BERT: it is a frozen MiniLM encoder with a trained LR head plus printed-heading rules.


## Explainable classification and sustained experiments — 2026-10-20

User requires explainable AI and continuing experiments toward90% or close; avoid repeatedly demonstrating/restarting the classifier UI. Every decision should identify whether a normalized printed heading or the trained model selected it. Explain the model through measured fixed-model text-block omission effects and score contrasts; never generate persuasive rationales from labels or call scores calibrated confidence. Omission shows local model sensitivity, not causation or proof of a correct label. Continue preserving failed candidates, historical test exclusion and adaptive-validation disclosure.

## Select explainable hybrid after sustained iteration — 2026-10-20

User requested continuing toward90% or close and explainable AI while avoiding repeated UI demonstrations. Select printed_v3_explainable: corrected full-page OCR for learned features, multiple independent OCR views for printed evidence, unique/ambiguous rule handling and training-group-CV selected ComplementNB. Do not present this as a transformer achieving92% alone. Additional contrastive MiniLM did not improve and is preserved.

Use exact n-gram log-score contributions for linear/ComplementNB models; show deterministic rule evidence/canonical OCR correction when a rule decides; use measured fixed-model text omission for older transformers. Explanations describe actual associations/sensitivity and may expose spurious features. They do not prove a correct label or calibrate scores.

Preserve OCR view boundaries and apply the title window per view. Require all three printed field groups for supply-request intent; fuzzy recovery permits one edit only for the long distinctive duplicate marker. Keep contradictory class cues unresolved for the learned fallback. No merchant/sample-specific rules.

The90% development target was crossed at23/25 validation and146/150 training OOF with adaptive rule overlay. Independent final90% is not demonstrated; rules were adapted outside the classifier folds and validation reused. Preserve old test exclusion. Leave the server/UI alone after saving the selected pointer; the next user launch should load it. Further trustworthy performance evidence needs independent real printed data.


## Canonical classifier folder and supervisor demo — 2026-10-20

User explicitly requested classifier/ at project root. Consolidate existing services/document_classifier source/models/history under classifier/engine/ rather than flattening or deleting research evidence. Keeping engine two levels under the project root preserves established ROOT calculations. New presentation app belongs in classifier/app; curated development examples in classifier/demo; deliberate JSON saves in classifier/exports; presentation/migration/QA evidence in classifier/docs. Shared assistant memory remains Context/.

Retain old prepared images under services/document_classifier/data as immutable compatibility assets because frozen annotation HTML/JSON link there; a canonical derived copy lives in engine/data. Keep old launchers as forwarding stubs and map historical paths in audit hashing, rather than rewriting ground-truth/history. Raw datasets and annotation store remain where they were.

Recorded examples must be identified as replayed development analyses, with verified model/image hashes; never pretend instant replay is live OCR or fresh accuracy. Include the known failure and adaptive-metric caveats. Uploads are temporary; reports save only on explicit user action and never automatically enter training or ground truth. The supervisor UI displays actual rule matches or measured learned feature contributions.



## Downstream prototype and evidence contract — 2026-10-24

Source: user explicitly requested continuing downstream testing, OCR correction experiments through sub-agents, and no paid APIs. New implementation lives in services/document_pipeline/; preserve classifier/ and canonical corpus/history. Use Codex sub-agents as an experimental extraction transport, with explicit manual handoff in the standalone local service. Do not describe this as a deployed automatic LLM backend.

Provisional extraction schema uses nullable decimal strings, exact OCR evidence pointers, explicit uncertainty and proposed correction lists. Dates preserve source strings. Checks use Decimal with0.01 absolute tolerance; missing tax/discount/subtotal never become zero. Keep corrections separate and never overwrite original OCR/values. Default evidence is literal with numeric token boundaries. Optional English grouped-comma interpretation requires an auditable token mapping and review for unverified locale; no automatic policy promotion. Quantity-only delivery notes need supported rows/quantities, not nonexistent monetary values. No invented calibrated confidence. Preserve classifier route and report contradictions instead of silently relabelling.

Persist local submission/result/audit records and idempotency in SQLite. Same key/payload replays; changed payload conflicts. Completed extraction immutable. Consumer is explicitly a demonstration stub with inventory_updated=false. Local session-token/Host/Origin checks are prototype access control, not production authorization. Region OCR coordinates and image-assisted observations are diagnostic development artifacts, not generic detectors or human truth.

## Opt-in automatic region evidence and independent evaluation — 2026-10-24

Source: user requested sustained downstream localization, isolated no-paid-API extraction, local backend feasibility and separate field-level evaluation. Integrate successful ruled-table OCR as an opt-in downstream stage, never a classifier change. Preserve primary OCR; store exact region-derived evidence separately with source/image/module hashes and source-coordinate mapping. Use fixed geometry-only first-success [axis_grid,deskew_grid] selection; no reference-value-based choice, merchant rules or document-specific coordinates. No grid keeps primary only; saved word groups are not presumed tables. Final run6 is the frozen reproducible detector evidence; earlier failures/source-snapshot limitations remain explicit.

Keep AI candidates human_verified=false even when mechanical review_required=false. Passing schema, evidence substring or arithmetic cannot establish field truth. Separate field review is an offline evaluation workflow, not an ERP approval loop. Independent accuracy requires actual human image-first transcription, explicit reviewer/attestation, source/candidate hashes, row completeness and missing/spurious-row accounting. Preserve assisted reviews separately from independent references; never generate truth from agent outputs. Clarify future raw_text as the item-description cell alone; keep earlier whole-row agent responses unchanged and disclose the semantic mismatch in comparisons.

No unattended model promotion: current inspected installation lacks generative weights/runtime endpoint and has limited free memory. Offline load failure is not inference latency or proof CPU extraction is impossible. Do not download large weights or claim model resource/schema/accuracy results without a bounded provisioned trial and actual measurement. Codex agents remain isolated experimental extraction transport only.
