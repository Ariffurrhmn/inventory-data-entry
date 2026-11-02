# Downstream roadblock follow-up — 2026-10-24

This session achieved an opt-in automatic ruled-table OCR improvement and a separate human field-review/evaluation tool. It did not establish independent extraction accuracy or install an unattended generative backend. The selected classifier is unchanged; its model and all five demo image hashes match saved pointers (`audit-manifest.json`). No historical test images were opened. Raw corpus, annotations/review history, manual diagnostics and older deliverables were preserved.

## Actual measurements

The current suite passes **49 tests** in 8.484 seconds (`software-checks.txt`), compared with the freshly rerun baseline's 35. Synthetic fixtures test software behavior only.

Automatic localization on seven eligible development images produced four grids and three explicit no-grid outcomes. This is a yield, not detector accuracy. The PO's two numeric rows and DN's five quantities are recovered without document-specific coordinates or merchant rules. DN OCR now reads `Detergent 500g`; manual diagnostic OCR read `5008`. Four source families/layout appearances are not established as an independent representative sample. Detailed methods, failed candidates, exact source snapshots, masks, overlays, PNG/TXT/TSV, coordinates and comparisons: [automatic localization](../automatic_localization/README.md). Final authoritative evidence is `../automatic_localization/run6/`; all seven inputs were checked against the eligible development manifest before image access. The two added documents include one detected DN grid and one no-grid PO.

Two fresh `fork_turns=none` agents independently read only their specified OCR JSON and contract. Neither was given images, previous outputs, references, expected labels or answer keys. The primary branch uses existing primary OCR; the region branch adds deterministic automatically selected cell OCR to those same immutable primary strings. Both retain the classifier prediction, including the known faint-copy route. Exact prompts, responses, source hashes and proposed correction lists are preserved, not regenerated or repaired. All returned correction arrays were empty. Agent provider model identity, inference latency and API cost were not independently instrumented. Codex agents are experiment transport, not a callable application backend.

| Diagnostic over five development documents | Primary OCR | Primary + automatic region OCR |
|---|---:|---:|
| Parse/schema-valid records | 5/5 | 5/5 |
| Returned rows (including uncertain fragments) | 6 | 14 |
| Populated quantities | 4 | 13 |
| Complete quantity/price/line-total rows | 2 | 6 |
| Passed line arithmetic checks | 2 | 6 |
| Failed arithmetic checks | 0 | 0 |
| Unavailable arithmetic checks | 14 | 18 |
| All populated fields literal-evidence supported | 2/5 | 2/5 |
| Mechanical review_required | 5/5 | 4/5 |

These are candidate completeness, schema, substring and arithmetic measurements, **not accurate-field counts**. More rows also create more unavailable monetary checks. PO improves from one to two complete numeric rows; DN from zero to five quantity rows; faint-copy from zero to three numeric rows. Comma-normalized values remain flagged under the unchanged literal policy. The separate grouped-comma diagnostic still has incomplete total support because punctuation/token boundaries remain strict. It was not promoted. Receipt monetary separators and row associations remain unresolved. One agent incorrectly describes OFFICE COPY as contradicting customer_copy; this is a preserved AI uncertainty, not a new taxonomy decision.

The DN now passes mechanical checks but remains `human_verified=false`; the demonstration consumer never updates inventory. Neither mechanical acceptance nor local OCR observations establish source truth. Agents also used whole row strings as `raw_text` in several outputs. Those original responses remain intact. Future prompt/schema wording now explicitly requests the item-description cell alone; the review workflow scores that declared meaning, so whole-row strings may fail description agreement even when numeric fields agree. No retrospective rewriting or description-accuracy claim.

`comparison-validation.json` preserves per-field evidence, every arithmetic check and both policy results. `primary-validation.json` preserves the earlier primary-only replay. `audit-manifest.json` records prompts/response/source hashes. `review-preparation/` contains five actual AI candidate records, their provenance and blank forms with no copied reference values or source row count. **No human truth or measured extraction accuracy exists.**

## Integrated behavior and fresh smoke

`gateway.py --region-ocr` runs `localization.analyze` for image submissions. The fixed choice is the first geometric-grid candidate with successful OCR in `[axis_grid, deskew_grid]` order, never whichever text matches expected values. No grid leaves primary OCR alone; word-box OCR is saved but not silently merged. The classifier result remains unchanged. A separate `extraction_source` retains combined exact text, image/primary/combined hashes, method, audit location and `human_verified=false`. Prompt export and verification use that same persisted text; old submissions continue using their original evidence. Imported JSON gains `extraction_human_verified=false`. New mode does not reprocess existing idempotency keys; use a new key.

Derived crops/OCR/audits from opt-in image submissions persist under the selected database's sibling `regions/` directory. Original upload bytes remain temporary. Localization failures record submission failure; no missing source evidence is invented. Default launcher behavior remains primary OCR unless `-RegionOcr` is supplied.

`live-region-smoke/` records a fresh selected-classifier image run, actual automatic region OCR, import of the actual region-agent response, persistence and demonstration consumer checks for PO and DN. Processing observations: PO 29.386 seconds; DN 18.623 seconds, excluding classifier initialization and agent extraction. Both completed. PO requires review; DN passes mechanical checks; both are unverified and `inventory_updated=false`. These are two observations, not latency percentiles or a production load benchmark.

## No-paid-API backend feasibility

`hardware.json` and `backend-probe.json` are actual local inspection, with reproduction in `services/document_pipeline/probe_local_backend.py`. i7-1265U (10 cores/12 logical processors), approximately16 GiB physical RAM, integrated Iris Xe graphics, CPU-only PyTorch2.14.1, no CUDA. Only about1.2–1.4 GiB physical memory was free in these snapshots. Ollama/llama.cpp executables were absent from PATH; llama_cpp was not installed. The inspected Gemma cache has only a627-byte config and40-byte ref, no tokenizer/generative weights. The other inspected caches hold classifier encoders, not extraction generators.

An actual offline/local-only Gemma load failed with missing weight files after58.120 seconds (includes import/loading overhead). **No model generation was executed**, so model peak RAM, generation latency, schema compliance and extraction accuracy are unmeasured. No weights were downloaded. This is a concrete provisioning/resource-headroom blocker for an unattended backend on the current installation, not proof that CPU extraction is impossible. A future bounded trial requires a chosen licensed small quantized model/runtime and sufficient freed RAM, then measured peak resource use, context limits, generation latency and schema/field tests. No particular model's suitability is established here.

## Run

From project root in PowerShell, use the configured interpreter:

```powershell
$py = (Get-Content classifier/engine/runtime.local.json | ConvertFrom-Json).python
& $py -m unittest discover -s services/document_pipeline -p 'test_*.py'
.\services\document_pipeline\start.ps1 -RegionOcr
# Browse http://127.0.0.1:8772; use a NEW submission key.
& $py services/document_pipeline/run_localization.py <image> --output <new-audit-directory>
& $py services/document_pipeline/experiments/2026-10-24/downstream_followup/validate_followup.py <new-validation.json>
& $py services/document_pipeline/run_region_smoke.py --output <new-smoke-directory> --responses services/document_pipeline/experiments/2026-10-24/downstream_followup/region-response.json
& $py services/document_pipeline/probe_local_backend.py --output <new-backend-report.json>
```

The validation runner replays actual saved responses; it does not invoke agents or regenerate data. New audit/report directories refuse replacement. The smoke uses an isolated temporary database; it preserves derived audits/results in its new output directory. `prepare_reviews.py` has already produced the blanks; do not rerun it into the existing folder. See [FIELD_REVIEW.md](../../../FIELD_REVIEW.md) for human `prepare`/`append`/`evaluate` commands, statuses, source binding, append-only history and exact metric definitions.

Remaining roadblocks: no ruled grid on three of seven tested layouts; borderless/complex/merged/perspective layouts unproven; no installed callable generative backend or safe measured model memory budget; and no independent human field truth. Reliable final accuracy still needs separately collected, source-grouped real printed documents and image-first human references. Do not use historical test inputs to tune these gaps.
