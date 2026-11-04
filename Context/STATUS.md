# Current status

Updated 2026-10-19 after directory inspection and organization.

## Confirmed from files and notes

- Prepared report/proposal files, signed copies, presentation, research-log PDF, and deprecated drafts exist under deliverables/. Preserve their version distinctions.
- Editable design/report/presentation material is now in docs/design/.
- Literature is grouped by topic under research/literature/.
- Synthetic README describes 120 fabricated examples, 30 per class, with 22 arithmetic-flagged cases; treat these as dataset documentation until independently validated.
- Bridge STATUS.md dated 2026-10-10 says all 29 images are approved (10 PO, 10 delivery challans, 9 customer copies). Its later instruction saying customer copies are next is stale.
- Bridge notes mark printing/phone photography as pending. Prepared print PDFs already exist; their existence does not prove printing or photography happened.
- Dataset exclusions and answer keys are preserved. Do not merge excluded examples back into class folders.

## Next useful work

1. Confirm whether printing/phone photography happened since the bridge checkpoint and whether application code lives elsewhere.
2. Audit real/curated, generated, and photographed data separately; establish usable per-class counts and provenance.
3. Resolve OCR, LLM, schema enforcement, confidence signal, classification taxonomy, and API/storage choices before implementation.
4. Verify research citations and reconcile older presentation plans with existing deliverables.
5. Validate and repair the synthetic regeneration workflow before running it.

## Existing tooling limitations

- synthetic_dataset/tools/generate.js writes to tools/out/, while shoot.sh and crop_and_degrade.py expect synthetic_dataset/html, images, and manifest.json. The README's regeneration sequence is not currently a verified end-to-end workflow.
- shoot.sh and crop_and_degrade.py contain machine-specific absolute paths.
- ChatGPT_Bridge/tools/make_prompts.py overwrites prompts and answers.csv. Running it may undo manual review refinements.
- make_print_pdf.py expects the retained root-level ChatGPT_Bridge/ and Dataset/ paths and requires Pillow/reportlab.
- No application execution or model accuracy evaluation was performed.

## Organization handoff

Original files were moved as recorded in moves-2026-10-19.csv. Dataset/, synthetic_dataset/, ChatGPT_Bridge/, and figures/ were retained to preserve tooling paths and existing references. Shared entry points are README.md, AGENTS.md, and CLAUDE.md. No generated corpus or deliverable was regenerated.

## Verification notes — 2026-10-19

The initial snapshot contained 774 files (including hidden desktop.ini files). After the folder moves, 773 matched their mapped paths and byte sizes. The original docs/research-logs/Research Log.docx (26,572 bytes) was absent; docs/research-logs/Research Log Capstone.docx (30,914 bytes) was present instead. No command in this organization renamed or edited that document. A concurrent or synchronized change is possible but unconfirmed. The observed file and Copy of Research Log.docx were preserved; do not silently treat this as a verified identical replacement. See inventory-before-2026-10-19.csv for the original snapshot.

After that check, textual root-path references in existing Markdown/text/script sources were updated where applicable. Byte-size equality is therefore only a verification of the move phase, not a claim that all text files remain unchanged. Binary embedded links were not checked. Existing script output-path inconsistencies were documented, not repaired or executed.

## User clarification and classifier scope — 2026-10-19

The user confirmed printing the synthetic/generated documents and photographing the printed copies. Dataset/Dataset-2 contains those phone photographs (54 HEIC files: 21 purchase orders, 24 delivery notes/challans, 9 customer copies). Printing/photography is complete for this material; earlier pending notes are historical. These are photographed synthetic documents, not real business transactions.

The classifier scope is ONLY four-class image classification: purchase_order, receipt, delivery_note, customer_copy. Table/region detection and number extraction are not classifier responsibilities. LLM extraction is a separate downstream stage. The user authorized preparing data and implementing/training this classifier. Work is under services/document_classifier/. Generated originals are excluded from the initial experiment to avoid original/photo leakage; curated provenance is not assumed real.


## Classifier implementation completed — 2026-10-19

See CLASSIFIER.md and services/document_classifier/RESULTS.md for the authoritative handoff. Prepared 145 images; 140 included after label review. Trained the four-class image baseline, attempted fine-tuning using validation only, and evaluated the selected baseline once: 13/28 correct (46.4% accuracy), macro-F1 0.483. Five workflow tests pass. This is an experimental baseline, not operationally reliable. Known originals/photographs/templates are grouped across fixed splits. No originals were changed by classifier preparation.


## Public dataset research and OCR-text input clarification — 2026-10-19

User clarified the intended classifier input pipeline: photograph/scan -> OCR text -> exactly one of purchase_order, receipt, delivery_note, customer_copy. This is a requested next direction, not a claim that the existing image-only baseline was changed. Table/field/number extraction stays downstream.

Completed research/datasets/DATASET_SEARCH.md and sources.csv (11 source records), with sample_provenance.csv, sample_review.csv, overlap_matches.csv and candidate quarantine folders under Dataset/external_candidates/. Inspected 28 image/PDF samples or thumbnails; larger retained annotation files were also examined. Company Documents v2 provides checked English synthetic PO/packing-slip/receipt samples and explicit generated-document/source-data licenses. ExpressExpense SRD provides usable photo candidates with explicit MIT permission, but five checked copy-marked images already exist locally as exact SHA-256 matches. CORD v2 train ID 8 is a confirmed visual derivative of cord-train-0008.jpg (not byte-identical); other filename clues remain unconfirmed.

Ready for a bounded future acquisition: English synthetic Company Documents v2 PO/packing-slip subsets and copy-aware SRD review; neither supplies a verified balanced real four-class corpus. DocILE needs authorized research access and dataset-term review. SROIE original image rights/version need confirmation; WildReceipt dataset license remains unclear despite useful OCR/copy-cue candidates. Roboflow PO full-resolution samples/exports and source provenance need verification. Senga's indexed PO/delivery-note lead currently returns 401. Real delivery-note/challan and independent copy-marked photo coverage remain gaps. Proposed class targets are plans, not acquired/measured yields.

No training, OCR execution, corpus merge, existing label/split change, or generator run. Protected labels/manifest/splits/results hashes were verified across report finalization; no whole-corpus before/after checksum claim. Next: rights/access clarification, taxonomy decisions for copy-marked POs/delivery notes and goods received notes, then source/family-grouped intake with a fresh real holdout. See the report for evidence and limitations.

## Reference transcriptions completed — 2026-10-19

Created one JSON transcription for each of the 140 included classifier images, plus an index, combined JSONL, side-by-side image/text review page, review queue and validation report in Dataset/annotations/. Each image received assistant visual review; all records explicitly retain human_verified=false. Unreadable/uncertain spans are marked and documented. These are reference candidates pending independent audit, not measured perfect OCR truth. Tables are linearized, without reviewed bounding boxes.

Class counts remain 35 purchase_order, 28 receipt, 50 delivery_note and 27 customer_copy; fixed splits remain 86/26/28. Labels/splits/source metadata matched the manifest and prepared image hashes were checked. No classifier experiment or external corpus import was run. Tesseract was used solely for annotation drafts. See TRANSCRIPTIONS.md for handoff and PENDING.md for the five paused tasks.

## Independent dataset-source assessment — 2026-10-19

Reviewed the other AI's 11-source research and current publisher pages. Independently screened 74 retained candidate image files plus all 200 cached ExpressExpense SRD images (266 unique byte streams) against the 145-image manifest and 140 included prepared images. Confirmed five ExpressExpense original byte identities by rehashing both sides; CORD train row 8 is a visually confirmed compression derivative. A second perceptual candidate was visually rejected. Two source families are confirmed already represented; absence of another match is bounded sample evidence, not full-release disjointness.

Saved research/datasets/INDEPENDENT_REVIEW.md, source_assessment_flags.csv and overlap_recheck_* evidence. Best additions are English synthetic Company Documents v2 PO/packing slips and unique SRD photos after copy/payment review; SRD 1078 shows a balance due and is not automatically a paid receipt. Conditional sources need access/terms/provenance work. Real English delivery/challan photographs and independent copy layouts remain gaps. No corpus merge, annotation/label/split change or model/OCR experiment; five implementation tasks remain paused.

## Reviewed intake staged — 2026-10-19

User approved the proposed bounded intake. Reviewed all 200 SRD images plus 20 English Company Documents v2 POs and 20 packing slips. Accepted separately: 49 receipt, 2 customer_copy, 20 synthetic purchase_order, 20 synthetic delivery_note (91). Held 140; excluded 5 existing duplicates and 4 internal derivatives. See INTAKE.md and Dataset/intake/2026-10-19/README.md for sources, labels, groups, license notices and limitations.

Validation passed for 240 source hashes, all image decoding and 91 unique accepted image hashes. The 144 protected classifier/reference files matched their before-intake hashes. Existing corpus remains 140; no merge, new split assignment, training or OCR quality experiment. OCR was used only for intake screening and is not reference truth. Human verification remains zero for staged labels. Other improvement work remains paused.

## Preliminary OCR-text classifier completed — 2026-10-19

User authorized continuing with the grouped OCR/text experiment. Preserved the frozen original 86/26/28 split and added 91 reviewed training-only candidates in a separate run manifest (177 augmented training). Trained fixed word/character TF-IDF + balanced logistic-regression pipelines; vocabulary/IDF fitted on training only. Original-only OCR won validation (macro-F1 .782 versus .726), so it remains selected: test 17/28 (60.7%), macro-F1 .597. Augmented OCR test 20/28 (71.4%), macro-F1 .695, retained as comparison without switching selection after test. Historical image baseline was 13/28 (46.4%). Delivery notes remain weak (selected recall 1/10); the reference-text diagnostic is also limited.

Scored OCR preliminarily on 72 whole references without markers/uncertainties, excluding 68; CER36.4%, WER45.6%. AI-only references, table reading order and selective coverage limit this estimate. Seven original and one additional OCR outputs are empty. Ten checks plus persisted-model/image/text inference smoke checks passed; 144 protected existing files match prior hashes. Current original corpus/splits and reference transcriptions were not overwritten. See OCR_TEXT.md, TEXT_EXPERIMENT.md and runs/text_preliminary/. Future changes need validation and a fresh independent holdout; fusion/LLM/app integration not implemented.

## Validation-only delivery-note OCR follow-up completed — 2026-10-19

Compared four fixed sparse/combined OCR alternatives on 177 training and 26 validation records; no test images opened or new test evaluation. All eight empty training/validation OCR outputs became nonempty, but the best new candidate (sparse_augmented) lost to the existing original_ocr model: validation macro-F1 .726 versus .782. No promotion; default inference remains text_preliminary/original_ocr. Delivery-note recall remains weak (best new candidate 2/6 on validation). Preserved the negative result in services/document_classifier/DELIVERY_OCR_EXPERIMENT.md and runs/text_delivery_v2/. Thirteen workflow checks and a training-image/text persisted-model smoke comparison passed; 69 protected files matched pre-run hashes.

Prepared docs/data-collection/FRESH_HOLDOUT.md plus Dataset/holdout_real_pending/manifest.csv and images/. Target: 80 real distinct documents, 20/class, from new businesses/layouts. Actual new holdout documents: zero. Next work requires collecting these documents and independently reviewing labels/transcriptions. Repeated tuning against the exposed historical test is not final evaluation.

## UTF-8 reference repair — 2026-10-19

Found and fixed a Windows encoding bug: reference_annotations.py read UTF-8 review actions using the cp1252 system default. Created Dataset/annotations/versions/utf8-v2/ from the unchanged correction instructions; 34 text records corrected (32 train, 1 val, 1 test). All 140 new JSONs, their image hashes and review-page image links passed checks; 863 protected historical annotation/run/data files remained unchanged; the annotation README was intentionally updated after verification. Fifteen workflow checks passed, including a regression test simulating cp1252. Two training images were visually spot-checked; this is not an independent human audit. Human verification is still zero and the 45-record review queue remains unresolved.

Use the versioned UTF-8 references for future review. Preserve original references and prior reported metrics; no model training, OCR metric recalculation, or new test evaluation occurred. Current default classifier remains text_preliminary/original_ocr. Details: Dataset/annotations/versions/utf8-v2/README.md and Dataset/annotations/audits/utf8-2026-10-19/report.json. Next: independent review of uncertain spans and collection of real holdout documents.

## Local annotation portal completed — 2026-10-19

User requested an HTML app with the slip on the left, editable annotations on the right, persistent saves and visibility into existing/unrecorded OCR. Implemented services/annotation_portal/ (HTML/CSS/JS plus a Python standard-library local server). Launch with Open Portal.cmd or run.ps1; default URL http://127.0.0.1:8765. It is running at handoff, though process availability is not guaranteed in future sessions.

Catalog contains 236 samples: 140 corrected references, 91 OCR-only intake records, and five excluded samples without recorded reference/OCR. Default queue shows 45 flagged records. Existing text tab exposes original drafts, experiment OCR and sparse OCR independently. Image viewer supports zoom/rotation; editor supports class, text, uncertainties, notes, reviewer and explicit verification. Saved reviews have immutable revision history and stale-write conflict detection; browser drafts are restored separately from disk saves. JSON exports are available for latest reviews and the full catalog.

Real review storage: Dataset/annotations/human_review/reviews.sqlite3. At creation it has zero reviewer records; automated browser saves were isolated in services/annotation_portal/.runtime/qa/reviews.sqlite3 as two non-verified draft revisions. Six backend tests passed, plus browser save/reload/history, draft recovery, OCR-only filtering, source visibility and image/layout checks. All 236 linked image paths exist. See services/annotation_portal/validation.json and README.md. Original annotations, source images, models, labels and splits were not overwritten; no training/evaluation occurred. Human reviews are not automatically adopted into canonical references or training. Next: user/team reviews the flagged queue, then OCR-only additions, using the portal.

## Assistant visual review batch saved — 2026-10-19

User asked Codex to perform the proposed 10-record review batch. Individually visually inspected 10 flagged receipt images and saved 10 AI review revisions in the portal: 3 text corrections, 2 unresolved payment-status/taxonomy flags, and mixed-language scope notes. All are reviewer_type=ai, status=needs_review, human_verified=false. Redacted text was not reconstructed. Existing unnamed/unedited drafts arrived during inspection; preserved them as revision 1 and appended the AI findings as revision 2 after checking they contained no manual edits. All 20 pre-existing review records remain in history, and 14 protected reference/metadata files matched hashes. Human edits/named reviews would have been skipped.

Evidence: Dataset/annotations/audits/assistant-review-batch-01-2026-10-19/README.md, applied.json, reviews.json and pre-review database backup. Initial report.json records a skipped first attempt and is not the completion summary. Five reviewed images belong to the historical test split; no training, tuning or evaluation occurred. The AI review does not create independently human-verified ground truth or change canonical references/frozen labels. The portal now distinguishes AI reviewer provenance from human verification; six backend tests pass, including rejection of AI human-verification requests. Next: human adjudication of payment/language questions, further annotation review, and explicit versioned adoption of accepted corrections before training.

## Printed-only scope applied — 2026-10-20

User explicitly excluded handwriting. Visually screened all 236 catalog candidates for content style, retaining contact-sheet evidence and selected enlargements. Activated Dataset/annotations/scope/printed-only-v1/: 202 candidates (52 PO, 64 receipt, 63 delivery note, 23 customer copy), comprising 116 original included and 86 intake images. Excluded 24 handwriting-dependent catalog images (two already historically excluded); held seven printed images with handwritten notes/values pending reviewed printed-only derivatives; retained three other prior exclusions. Photographed synthetic handwriting-style bodies remain outside scope even when physically printed. Incidental signatures are ignored as transcription targets.

Portal defaults to printed candidates and has separate handwriting/region-hold/history views. Out-of-scope records are read-only, and the printed-review export withholds their saved reviews; full catalog export preserves history with scope flags. Eight backend tests pass. Original labels, 86/26/28 assignments, 140 corrected references and selected model/results remain preserved (147 protected hashes checked). No training/evaluation and no new human verification.

Critical readiness gap: inherited printed subset is train162/val13/test27, but validation has zero delivery notes (the six previous validation delivery notes were handwriting-dependent). Need new printed delivery-note development data or an explicitly versioned grouped development split from non-test families before four-class model selection. Do not use the old exposed test to fill the gap. Legacy predictor and metrics still describe the previous broader scope. See scope README, validation.json and evaluation_readiness.json. Current scope eligibility does not resolve existing label/payment/language uncertainties or imply perfectly cleaned OCR.

## Printed classifier trained and running — 2026-10-20

User explicitly requested training and a running classifier ASAP. Active pipeline is runs/printed_v1_edges/ via active_text_model.json, using trained word/character TF-IDF + balanced logistic regression, explicit printed-heading decisions and sparse/full-page plus top/bottom region OCR. Web upload/pasted-text app runs on http://127.0.0.1:8767; launch with services/document_classifier/Open Classifier.cmd or start_classifier.ps1 -Open. CLI classify.ps1 and default run.ps1 predict use the active pipeline; predict-image retains the legacy image model.

Created a new grouped development manifest without changing frozen original splits. Training150: PO36/R56/DN50/CC8. Validation25: PO10/R3/DN3/CC9. Known Bridge printed template groups across classes are held together in validation. All 27 historical test records are excluded; five share the broader Bridge validation family, so this is not an independent new test. Company Documents v2 stays one training generator group.

Initial three OCR/statistical candidates selected baseline at 13/25. Adaptive bounded heading and edge-OCR follow-ups reached 19/25 (76%), macro-F1 .7657. Validation recall PO9/10, R3/3, DN3/3, CC4/9: customer copies remain weak, and all three validation delivery notes are synthetic. Do not present development validation as final generalization accuracy. Twenty-one workflow checks pass; final saved inference reproduces all25 predictions, image-upload/cached-pipeline checks pass (one CC misclassification explicitly recorded), and empty/bad input rejection plus CLI/browser operation were verified. No old test inputs opened, no reference/label/source rewrites. See services/document_classifier/PRINTED_CLASSIFIER.md and final smoke_validation.json. The earlier missing-validation-DN blocker is resolved by the new development split, not by changing the historical test.

## Transformer iteration completed — 2026-10-20

User requested new classification approaches including transformers/BERT. Actually ran frozen MiniLM with balanced LR (C1/10), small BERT end-to-end fine-tuning (12epochs; checkpoints4/8/12), and semantic/lexical feature fusion (C1/10), all locally on CPU. Reused the saved150/25 printed development split and unreviewed sparse OCR; no historical test inputs opened. Specifications, cache/source hashes, predictions, public model revisions, weights/checkpoints and failed candidates are preserved under services/document_classifier/runs/printed_v1_transformers/ and printed_v1_fusion/.

Activated printed_v1_minilm after persisted encoder/features/predictions reproduced. Frozen MiniLM/LR plus unchanged heading/edge OCR scores20/25 (80%), macro-F1 .8036, versus previous19/25, .7657. Recall PO9/10, R3/3, DN3/3, CC5/9. MiniLM alone13/25; small BERT hybrids17/25; fusion hybrids19/25. Small BERT epoch12 fits143/150 training but only3/25 validation without rules, so it was rejected. This is one net additional correct validation record, not independent generalization evidence.

Local UI http://127.0.0.1:8767 now serves the new run. Twenty-one workflow tests pass; all25 saved validation predictions and encoder features reproduced. Four real image uploads match cached output (one known CC error); empty/invalid inputs rejected; browser and CLI remain available. Public Apache-2.0 model weights stay in the configured C: runtime hf-cache, with pinned revisions/file hashes in active public_weights.json; do not delete the cache. Inference stays offline/local. Previous models, sources, references and history preserved.

Read services/document_classifier/TRANSFORMER_EXPERIMENT.md and PRINTED_CLASSIFIER.md. Current data weaknesses remain eight training customer copies, reused validation, synthetic-only validation delivery notes and no fresh real holdout. Next: additional independent printed CC data and training-only grouped comparisons/contrastive adaptation; do not optimize against the historical test.


## Explainability and sustained iteration — user direction 2026-10-20

User requested continuing experiments toward90% or close, focusing on improvements rather than repeatedly opening/running the app, and explicitly requires explainable AI. Active goal is ongoing. No new performance target has yet been achieved. Uniform illumination-normalized OCR and rotated title views are being generated for all175 development images in runs/printed_v2_illumination/ (not test). A cross-group, class-balanced contrastive MiniLM adaptation is running in runs/printed_v2_contrastive/. Keep incomplete runs distinguished from completed results.

Implemented explain.py: deterministic heading trace or fixed-model token-block omission effects, with supporting/opposing evidence and explicit sensitivity/calibration limits. Three controlled explanation tests pass. audit_explanations.py is preparing traces for five existing errors and one heading decision in runs/printed_v2_explainability/. inference.py now includes a cheap decision_trace in output; the existing server has not been restarted to pick up this change. No UI reruns requested. Heavy omission explanations are available through CLI and batch artifacts, not yet an app button.

## 90% development target crossed; explainable candidate selected — 2026-10-20

Completed the sustained experiments and explainability work requested by the user. Selected active_text_model.json run is **printed_v3_explainable**. It is a corrected-illumination OCR + versioned printed-text rules + training-group-CV selected TF-IDF/ComplementNB fallback. It is not a BERT classifier with92% standalone accuracy. Current selected validation23/25 (92%), macro-F1 .9211; PO10/10,R3/3,DN3/3,CC7/9. Training-only grouped OOF model predictions with adaptive rules146/150 (97.3%), macro-F1 .9480; four errors remain. These are reused/adaptive development measurements, not independent final accuracy. No historical test inputs opened.

Actually completed: uniform corrected/rotated OCR for all175 development images;40-step cross-group class-balanced contrastive MiniLM adaptation (no improvement); four training-group-CV recovered-OCR learners; conservative copy-marker/purchase-intent recovery; independent title windows per OCR view. The view-window correction fixed a real handling issue: concatenated OCR previously let the first30 total lines suppress corrected titles in later views. All experiments and unsuccessful models/checkpoints are retained in runs/printed_v2_*/ and printed_v3_sections/.

Explainability implemented in explain.py and prediction decision_trace. API includes full explanation by default and UI source has a readable “Why this prediction?” section. Deterministic rule evidence records exact normalized matches or explicit OCR correction; learned n-gram contributions exactly reconstruct score differences; older transformers use measured token-block omission. No generated rationales. Selected run saves all25 explanations (18 heading,2 purchase intent,5 exact model). Maximum algebra error2.27e-14. Explanations also expose wrong associations, including address words supporting a missed copy's wrong PO label.

Thirty workflow tests pass;25 saved predictions/explanations reproduced; UI JavaScript syntax checked. No repeated UI demo/server restart or image-upload smoke series: the existing8767 process may still hold the old MiniLM model. **Next user launch loads the new selected run.** Current model uses base sklearn environment and no Hugging Face encoder cache; preserve caches for older runs.

Primary handoffs: services/document_classifier/EXPLAINABLE_CLASSIFIER.md and PRINTED_CLASSIFIER.md. Earlier in-progress notes above are superseded. Remaining: two red-stamped validation customer copies, eight CC training examples, synthetic-only validation DN and unverified truth. Independent real-world90% remains unproven; next evidence is fresh real holdout and more printed CC families. Raw images, original labels/splits, annotations/review history and prior models/results preserved; six protected hashes verified.


## Supervisor demo and classifier consolidation — 2026-10-20

User requested a top-level classifier folder and an app to demonstrate to the supervisor. Completed classifier/: Open Demo.cmd launches local Document Lab at http://127.0.0.1:8770; Stop Demo.cmd stops its owned server. app/ contains the new supervisor UI/server. engine/ contains relocated classifier source, derived data, OCR weights, selected model and all prior runs. Selected model and metrics unchanged: printed_v3_explainable,23/25 adaptive development validation. No retraining or new benchmark claim in this task.

Demo has image upload/pasted OCR, document preview/zoom/rotation, explanation/OCR/details tabs, JSON export, explicit project report saving, and Model & evidence page. Five existing validation examples cover the four types and a known failure; replay mode is clearly labelled Recorded example. Four examples are photographs of printed synthetic documents. Run live performs real local OCR/inference. Browser live purchase-request check succeeded in10.51s. Browser verified recorded purchase intent, receipt learned contributions, office-copy heading, known copy-stamp mismatch, OCR inspection, evidence limitations, saved report and downloaded JSON.

43 automated checks passed:5 demo API tests,30 classifier tests,8 portal tests. Portal catalog still resolves all236 images. Selected model, six protected historical hashes and demo example hashes are preserved. Migration docs/classifier inventories explain that the prescan covered941 files (overlapped relocation);940 data/code hashes matched, with only OS-managed data/desktop.ini differing. Full post-relocation inventory is saved. No original datasets, annotations/review history or signed documents moved/rewritten. One pre-launch transient module lookup failure was resolved after relocated Drive files became accessible; final startup/live flow succeeded.

Historical services/document_classifier/data/ remains as immutable prepared-image compatibility assets for old annotation HTML/JSON links; canonical derived copy is in classifier/engine/data/. Old command launchers forward to the new folder. Portal code now reads canonical classifier/engine with fixture fallback; research helper references updated. text_common.sha translates missing old classifier paths for preserved historical hash audits; frozen records themselves retain historical strings. Other historical paths may need the documented prefix translation when reading old artifacts.

Current entry points: classifier/README.md, classifier/docs/SUPERVISOR_DEMO.md, classifier/docs/demo-validation.json and classifier/docs/demo-preview.png. Shared context stays in Context/. Existing8767 classifier process was stopped for relocation; the new8770 demo serves the selected92% development model. Annotation portal remains separate on8765. Current demo runtime uses the configured external Python environment; Setup Demo.cmd supports another PC with Python3.12/Tesseract. Base demo does not need Hugging Face weights or GPU.


Demo handoff follow-up: old PSM3/sparse OCR caches are retained read-only alongside old prepared images to preserve the already-running portal session. Current portal source reads canonical engine paths; no forced portal restart. Migration records are in classifier/docs/migration/, QA records in classifier/docs/qa/. The supervisor demo launch remains classifier/Open Demo.cmd.

Final runtime audit: the new Document Lab on8770 is healthy and its selected model hash matches. The annotation portal on8765 was not running at the time of the audit (connection refused); this task did not force-start it. Its fresh catalog resolves all236 images and all8 portal tests pass. Use services/annotation_portal/Open Portal.cmd when needed. Read-only legacy OCR/image assets remain for compatibility with historical records and any restored old process.

## Capstone readiness assessment and proposed roadmap — 2026-10-20

User requested overall standing, a visual roadmap, priorities and presentation requirements after classifier stabilization. Created docs/design/capstone_readiness_roadmap_2026-10-20.md from shared context, current classifier handoffs, selected-run JSON, saved demo QA and the design report. Verified saved 23/25 adaptive validation and 43 historical workflow checks; the fresh holdout manifest still has no acquired-document rows. No models, datasets, references or application behavior changed; no tests/benchmarks rerun.

Assessment: explainable classifier demo ready; downstream schema-constrained extraction, arithmetic/flagging, submission gateway and capture integration remain implementation work. Proposed sequence: settle taxonomy/schema/evidence contract -> extraction vertical slice -> verification -> API/thin capture -> frozen independent evaluation -> final presentation, with real data collection and documentation alongside. Central proposed evidence is verification's effect on wrong unflagged extraction output. These are recommendations, not newly adopted scope/design decisions or measured outcomes. Report alignment needed for printed-only scope, current local hybrid, uncalibrated scores and separation of classifier from region/extraction tasks. Preserve signed/older deliverables.


## Downstream development pipeline and sustained testing — 2026-10-24

User authorized testing/iterating beyond classification, clarified OCR correction, and requested Codex sub-agents without paid APIs. Implemented services/document_pipeline/: loopback capture/upload or pasted OCR -> unchanged selected classifier -> exported sub-agent prompt -> externally supplied extraction JSON -> immutable evidence/Decimal verification -> persisted submission/result and demonstration consumer. Open Pipeline.cmd and http://127.0.0.1:8772 are the entry points. SQLite records idempotency, processing/failure/completion and extraction attempts. No callable model backend, real ERP, cloud deployment or phone-to-server capture is claimed.

35 automated downstream tests passed in the configured classifier runtime; five cached development OCR submissions and two actual image OCR uploads passed HTTP smoke. Ten actual saved direct/strict sub-agent responses completed the full handoff; all required review. Browser delivery-note walkthrough reached completed and blocked_for_review. Selected classifier model SHA-256 still matches bd1dba65eb03c3f2282697a502400794ce754543c5e16150625b73cea62ce0bd. No historical test inputs, canonical datasets/annotations or older deliverables changed.

Actual sub-agent approaches: direct and evidence-first extraction, strict literal withholding, multi-view OCR, separate image-assisted AI observations, then region OCR recovery. Direct outputs5/5 schema valid; literal evidence complete2/5; all review-required. Explicit diagnostic comma-grouping policy records6 mappings and supports populated fields5/5 but does not establish locale/accuracy. Strict withholding loses numeric operands. Multi-view rescues one description. Image assistance sees PO2 complete numeric rows and DN5 quantity rows; human_verified=false. Twelve local table/row/cell OCR configurations show manually chosen cell interiors recover both PO numeric rows and all DN quantities, with a remaining500g→5008 description error. All failures, PNG/TXT/TSV, timings and hashes retained.

Verification preserves original OCR/values; proposed corrections never silently apply. Default literal evidence; optional grouped_commas is diagnostic and flagged for locale assumption. Partial numeric tokens rejected. Missing operands are not_applicable, never implicit zero. Quantity-only delivery notes do not require monetary fields, but missing rows/quantities/uncertainties require review. Arithmetic/text presence cannot prove field correctness.

Primary handoff: services/document_pipeline/README.md; experiments/2026-10-24/README.md and ocr_regions/README.md; validation/2026-10-24/ contains measured smoke, handoff, policy, tests and browser evidence. Remaining boundaries: unattended extraction backend; automatic layout/table-cell localization (successful crops manually adapted to two exposed examples); independent human-reviewed field truth. No extraction accuracy or OCR improvement benchmark is claimed. Sub-agent usage/approval-review interruption recovered after user continued; work resumed normally.

## Automatic localization, blinded extraction and field evaluation preparation — 2026-10-24

Implemented opt-in reusable ruled-table/cell OCR in services/document_pipeline/localization.py with Pillow/NumPy/SciPy directional morphology, dashed-rule closing, connected components, bounded deskew, cell montages, OCR word boxes and original EXIF-oriented coordinate polygons. No image-specific coordinates or merchant rules. Preserved all six experimental runs, including failed approaches and the explicit early-source snapshot limitation; final run6 has exact source snapshots/hashes. Seven eligible development images were manifest-checked before opening (no historical test inputs): four produced grids; three explicit no-grid cases. PO both numeric rows, DN five quantities and Detergent500g recovered; extra DN five rows. These are unverified OCR observations/yield, not accuracy.

Gateway opt-in: services/document_pipeline/start.ps1 -RegionOcr (port8772); default stays primary-only. Classifier OCR/routing preserved. Separate extraction_source stores exact primary+selected-region evidence and hashes; exported prompt and verification use the same source, including after persistence/replay. No grid retains primary alone. Derived audits persist beside the chosen database under regions/. Imports explicitly extraction_human_verified=false. Two fresh selected-classifier image smoke runs plus actual saved response imports completed: PO29.386s, DN18.623s, excluding classifier initialization/agent extraction; inventory_updated=false. PO flagged; DN passes mechanical checks but remains unverified.

Fresh baseline35 tests; final49 software checks pass (8.484s). Two new fresh fork_turns=none agents saw only isolated OCR+contract: schema5/5 each; populated quantities4→13, complete numeric rows2→6, passed line arithmetic2→6, failed0, review-required5→4. All populated fields literal-evidence supported2/5 in each branch. No accuracy claim. Actual prompts/responses/correction lists/hashes and per-field audits saved; comma/locale, receipt association and full-row raw_text issues remain visible. Future schema/prompt now clarify item-description-only raw_text; historical responses untouched.

Offline backend probe: i7-1265U10c/12t, ~16GiB RAM, IrisXe, CPU-only torch2.14.1; ~1.2–1.4GiB free in snapshots. No Ollama/llama.cpp command on PATH; inspected Gemma cache config-only. Actual local-only load fails for absent weights (58.120s including import/load failure); no downloads or generation executed, so model RAM/latency/schema/accuracy unmeasured. Current unattended backend blocked on runtime/weights and memory headroom; CPU feasibility after provisioning remains unvalidated. Codex agents are experimental handoffs, not application backend.

Separate field_review.py + FIELD_REVIEW.md: blank image/candidate-hash-bound forms, explicit AI=false verification, append-only human revisions, independent image-first attestation, field statuses, row alignment/missing/spurious rows, exact string/Decimal accuracy and coverage. Eight fixture tests; fixtures are software checks, not measured extraction. Five actual candidate records and blank forms prepared, no independent human truth created. Field accuracy stays unavailable pending human references and new grouped real holdout.

Read services/document_pipeline/experiments/2026-10-24/downstream_followup/README.md and automatic_localization/README.md for measurements, full provenance and run commands. Selected classifier model and five demo image hashes match saved pointers. No raw corpus, historical splits/tests, annotations/review history, manual diagnostics or older deliverables rewritten. Remaining: borderless/complex/perspective localization (3/7 tested layouts no grid), unprovisioned unattended extraction, independent field truth. Do not treat grid yield/schema/arithmetic as accuracy.

## Saved HTML progress report — 2026-10-24

User requested a saved HTML report of built components, remaining work and overall standing. Created docs/design/capstone_progress_report_2026-10-24.html: offline responsive/printable status report, architecture/status matrix, saved classifier/downstream results, backend blockers, human evaluation procedure, proposed priorities, launch commands and links to primary evidence. Numbers checked against saved validation/test artifacts; no new benchmark or model/application changes. Local evidence links and section anchors validated.

## Supervisor Showcase — 2026-10-29

User requested a separate folder holding what to show the supervisor in coming weeks: the completed classifier with a polished UI that helps the supervisor decide next steps. Created supervisor_showcase/ (launch Open Showcase.cmd → http://127.0.0.1:8780). Six-step walkthrough: overview, live demo (all 25 validation documents with recorded outputs, Run live, upload, paste text), results (confusion matrix, per-type metrics, the two mistakes, full gallery), journey (five models on two clearly separated evaluation sets, rejected approaches), data & gaps, and a decision page whose supervisor choices save to supervisor_showcase/meeting-notes/. It imports the unchanged selected model printed_v3_explainable from classifier/engine; no model, data, split or annotation was changed or copied. Figures shown live in supervisor_showcase/data/showcase.json with source files; a test checks them against completion.json.

Validation: 7 automated checks pass (gallery = 23/25 recorded, headline/dataset counts match confusion matrices, image/record endpoints, token-protected POST, notes save/list, live text classification with the selected model hash). Browser checks: all six pages at desktop and 375 px (no horizontal overflow), light and dark themes, a live OCR run on a validation image (15 s, same label as the recorded output), deep links, decision save (test note deleted afterwards).

Runtime finding: the Python venv configured in classifier/engine/runtime.local.json (under .codex/visualizations/.../classifier-env) is now empty, apparently lost during a disk-full event on 2026-10-29 that also stopped Google Drive file reads for a while. classifier/Open Demo.cmd and services/document_pipeline therefore cannot start as configured. The showcase launcher falls back to system Python 3.14, which has scikit-learn 1.9.1 but not pillow-heif (HEIC uploads disabled there). runtime.local.json was not changed.

## Classifier runtime repaired — 2026-10-29

User approved repairing the wiped runtime. Created a new venv at D:\DocumentLab\python-env (Python 3.14.6; scikit-learn 1.9.1, numpy 2.5.4, Pillow 13.0.0, pillow-heif 1.8.1, joblib 1.6.0, scipy 1.18.1, matching requirements-lock.txt versions where available). Placed on D: because C: had only 2.8 GB free, and because venvs created from the Claude desktop app under AppData\Local are redirected into the app's private package storage (a first attempt landed there and was removed). classifier/engine/runtime.local.json now points to it; the old .codex classifier-env path is retired. setup.ps1 now accepts Python 3.12–3.14 and writes engine/runtime.local.json; requirements-demo.txt adds scipy for the pipeline.

Validation with the new runtime: classifier demo tests 5/5, document pipeline 49/49, engine 25/30 (the 5 in test_workflow.py need PyTorch for the historical MobileNet image baseline; torch not installed to save space). classifier/Open Demo launcher starts on 8770 with printed_v3_explainable; supervisor showcase now runs on this runtime with live mode ready, and a HEIC photo (Dataset/Dataset-2/Customer copy/IMG_1002.HEIC) classified customer_copy via printed heading in 29 s. Older transformer/MiniLM runs still need torch and the hf-cache to reproduce.

## CSE 498B plan created — 2026-10-30

User asked for a phased capstone plan (5–8 h/week, team where the user does most work). Saved docs/design/capstone_plan_498B_2026-10-30.md: phases, 40-task table with done-when checks, critical path, risks, cut order, this-week list and weekly hours. Deadlines (assumed submit Tue 15 Dec, defense Tue 22 Dec, mid-review ~19 Nov), rubric/template and supervisor scope expectations (local demo vs mobile/cloud) are unconfirmed ASSUMPTIONS. Proposed holdout target lowered from 80 to 40 real documents pending supervisor approval. No code, data or model changed. Next: tasks A1–A3 (confirm dates/scope, start teammate document collection); update the plan file in place as progress is reported.

## End-to-end demo with phone PWA — 2026-11-04

User asked for a complete demo of the full system (not only the classifier) to show the teacher and get a go-ahead; the mobile app is a PWA for now. Built full_demo/ (launch `Open Demo.cmd` / `Open Demo (phone).cmd` / `./full_demo/run.sh`, port 8790). Read full_demo/README.md and full_demo/DEMO_SCRIPT.md.

Contents: phone PWA (pairing code, camera/gallery capture, client-side downscale, IndexedDB offline queue re-sent with the same idempotency key, service worker, plain-language results); desktop dashboard (pipeline strip marked real/stand-in, 13-document curated shelf, evidence-annotated extraction, live policy toggles, "try to break it" simulator, ground-truth comparison, ERP inbox, phone tab with QR, Evidence page, Reset button); server reusing unchanged gateway.Store, contract.py and the selected printed_v3_explainable model; rules-based extraction stand-in with an --extractor-cmd hook for a real LLM; ERP stand-in inbox (inventory_updated always false).

Verification actually performed (Linux cloud container, Tesseract 5.3.4 with standard English data, not the project's earlier OCR data): 31 new tests pass (full_demo/tests); existing services/document_pipeline suite still 49/49; real-browser run (Chromium, emulated phone): pairing from QR URL, service worker registered, manifest served, offline capture held in IndexedDB, app shell reopened offline, queued photo uploaded and processed after reconnect, no console errors, no horizontal overflow at phone width; LAN-mode launch via run.sh, dashboard session refused from the LAN address, pair + capture + result over the LAN address. NOT done: test on a physical phone; Windows launcher (start.ps1/.cmd) not executed (no Windows here); https/installability not exercised; no real-document evaluation; no LLM extraction measured.

Measured on the 86 printed/thermal documents of synthetic_dataset (excluded from classifier training by prepare.py; clean synthetic renders; full_demo/evaluate_synthetic.py, data/evaluation.json): classifier 65/86 (heading rules 56/56; receipts decided by the learned model 9/30); rules extractor reads 27/86 documents with every field exact (rest mostly OCR slips); 17/17 documents with a printed arithmetic error flagged; strict contract flags 84/86 (2 wrong unflagged); demo_reconcile flags 47/86 (18 correct passed, 41 wrong caught, 21 wrong NOT flagged, mostly item-name OCR slips). The recorded 23/25 classifier figure is a tuned development set, not comparable. Observation, not a fix: the 'faint copy stamp' demo photo, a recorded misprediction, routes correctly under this machine's OCR data.

Open items for the supervisor: totals policy (strict vs reconcile with a stated no-tax assumption), real-document collection, extraction model choice. Next: run the demo on the Windows machine and a physical phone; collect real documents; provision and measure an LLM extractor.
