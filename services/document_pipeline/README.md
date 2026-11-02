# Document Pipeline — local downstream prototype

Open **Open Pipeline.cmd**, then visit http://127.0.0.1:8772. It uses the existing classifier Python runtime and Tesseract. Close the launcher terminal to stop a manually started instance. This is a local development service, not a deployed cloud gateway.

The prototype processes English printed documents through OCR and the unchanged four-class classifier, exports an extraction prompt, accepts externally returned JSON, checks source evidence and arithmetic, and exposes a demonstration consumer response. LLM extraction is a **Codex sub-agent handoff**. There is no automatic model endpoint, paid API, stock ledger, or real ERP integration.


## Current follow-up — automatic region OCR and field review

The current suite passes **49 checks** (fresh baseline35). Opt-in automatic localization recovers both PO numeric rows and all five DN quantities; four of seven eligible development images produce grids, with explicit failures preserved. Two fresh isolated extraction agents produced5/5 schema-valid records each; populated quantities rise4→13 and complete numeric rows2→6 with region OCR. These counts are not field accuracy. One DN passes mechanical checks but remains human_verified=false. No independent truth or automatic LLM backend has been created.

Run `./services/document_pipeline/start.ps1 -RegionOcr` from project root to enable automatic cell OCR. Default launcher remains primary-only. Classification OCR is preserved; separate exact extraction evidence and audit artifacts persist under `.runtime/regions/` (or beside the chosen database). Prompt and verifier use that same stored source. Use new submission keys for the new mode. Imported candidates are explicitly unverified.

Read [the measured follow-up](experiments/2026-10-24/downstream_followup/README.md) for actual prompts/responses, source hashes, failed alternatives, offline hardware/backend probe, live integration evidence and reproduction. [Automatic localization](experiments/2026-10-24/automatic_localization/README.md) documents methods/coordinates/limits. [Field review](FIELD_REVIEW.md) provides separate blank, source-bound human review and evaluation commands. Five actual candidate records and blank review forms are prepared in the follow-up's `review-preparation/`; they contain no manufactured ground truth.

The inspected installation has CPU-only PyTorch and no cached generative weights/callable model server; an offline load failed. About1.2–1.4 GiB RAM was free. No model downloaded or generation benchmark claimed. Runtime provisioning/headroom and independent human truth remain concrete blockers.

## Using the prototype

1. Upload an image or paste OCR, enter a unique submission key, and click **Read document**.
2. Copy/download the prompt and run it with a Codex sub-agent. The document content is untrusted data. Return JSON only.
3. Paste the returned JSON and click **Verify JSON**.
4. Inspect checks/reasons, download the result, and check the demonstration consumer.

The same key and request replays its existing submission. Reusing a key with changed content returns a conflict. Completed extractions are immutable; identical replay succeeds, and revisions need a new submission. Failed OCR remains a recorded failure; a new key is required to retry. A restart marks interrupted OCR as failed. Rejected structured attempts are appended to the audit database, and valid JSON can then be retried.

OCR/results and extraction attempts are stored in .runtime/submissions.sqlite3. Uploaded image bytes are temporary. The input_sha256 field is a canonical request fingerprint, including the image filename/base64 or supplied text; it is not the raw image hash. The server binds only 127.0.0.1, checks Host/Origin, and requires an ephemeral session token for submission/result APIs. This is single-process local prototype access control, not production tenant authentication or retention management. Do not run two instances against the same database.

## Contract and verification

schema.json and contract.py define a provisional downstream contract, separate from the classifier's classification-report JSON. Dates and headers preserve OCR strings. Monetary fields and quantities use nullable decimal strings so verification does not depend on binary floating point. All populated headers, descriptions, and numeric fields require exact source quotes addressed by JSON pointer. Partial numeric tokens do not count as evidence.

The default policy requires literal numeric evidence. Corrections are proposals only: original OCR and extracted values are never silently rewritten. An experimental grouped_commas policy records an explicit source-token mapping and an unverified English grouping assumption. It is available for diagnostics; the gateway default remains literal.

Decimal checks compare quantity times unit price, item sums versus subtotal, and subtotal plus tax minus discount versus grand total with absolute tolerance 0.01. Missing operands yield not_applicable. Missing subtotal/tax/discount are never assumed to be zero. Quantity-only delivery notes do not require absent prices or totals; they still need nonempty supported rows and quantities. Other incomplete monetary checks, missing evidence, ambiguities, and correction proposals cause review.

A passed check establishes arithmetic or text presence, not correct field/row assignment or agreement with the image. The tests include a consistently wrong, OCR-supported record that passes arithmetic. Classifier scores remain uncalibrated. The extraction document_type preserves the classifier route, so a classifier mistake can propagate; contradictory cues belong in uncertainties.

## Earlier tested progress — 2026-10-24 (preserved)

- 35 automated checks passed using the configured classifier runtime: contract, arithmetic, evidence, class-specific absence, invalid JSON/overflow/depth, HTTP access checks, concurrent idempotency, conflict, persistence, failures and immutable extraction.
- Five saved development OCR inputs went through live classification and HTTP submission; two original demo images also underwent fresh local OCR through HTTP. Live image stages took 21.234 and 7.096 seconds in that measured run, excluding initial model startup. These are two observations, not latency percentiles.
- Ten actual saved sub-agent responses (direct and strict variants for five documents) completed classifier -> persisted submission -> extraction import -> verification -> demonstration consumer. All required review.
- Browser walkthrough completed using actual delivery-note OCR and an actual sub-agent record. It reached completed and blocked_for_review with inventory_updated=false.
- Actual sub-agent experiments tried direct extraction, evidence-first revision, strict evidence withholding, multiple OCR views, and a separate image-assisted observation branch. All five direct outputs were parseable/schema-valid; this does not measure extraction accuracy.
- A separate opt-in grouping diagnostic supports all populated fields on 5/5 direct records with six audited mappings, versus 2/5 literal-evidence support. All remain review-required. No locale or accuracy claim is made.
- Region/cell OCR experiments and image-assisted findings are separately documented in experiments/2026-10-24/. Manual crops and AI observations are development diagnostics, not a deployed table detector or reviewed truth.

Measured artifacts: validation/2026-10-24/live-smoke.json, handoff-replay.json, numeric-policy.json, checks.json, browser-qa.json and the experiment reports. Earlier failed SQL/connection tests were fixed before the successful run. Original datasets, annotation/review history, historical test inputs, classifier weights and old deliverables were not changed.

## Remaining boundaries

Sub-agents establish feasibility inside Codex; a standalone app still needs a callable extraction backend to automate this boundary. Opt-in automatic ruled-grid localization now recovers cells on four of seven development images; borderless/complex layouts and perspective rectification remain unresolved. Independent human-reviewed field truth is still absent, so extraction accuracy, correction improvement, and calibrated acceptance thresholds remain unmeasured. Cloud deployment, production authorization, a real ERP consumer, and phone-to-server capture are not established by this prototype.

## Reproduce

From the project root, use the Python path in classifier/engine/runtime.local.json:

- python -m unittest discover -s services/document_pipeline -p "test_*.py"
- python services/document_pipeline/run_live_smoke.py
- python services/document_pipeline/run_handoff_replay.py
- python services/document_pipeline/compare_numeric_policy.py
- python services/document_pipeline/experiments/2026-10-24/validate_experiment.py

Use the configured classifier Python rather than an unrelated system Python for live OCR/model checks. The live smoke needs Tesseract on PATH. New runtime and experiment data belongs within this service; none of it automatically becomes training data or annotation truth.

