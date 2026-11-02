# OCR-to-JSON sub-agent pilot — 2026-10-24

Actual execution with one fresh Codex sub-agent for OCR-only trials, then follow-up turns; a second fresh sub-agent subsequently tested a separately labelled image-assisted branch. No paid API, external provider, historical test inputs, annotation references, answer files, or reviewed field truth were used. The OCR-only agent never inspected images. This is a development feasibility experiment on the five previously exposed classifier/demo examples, not an extraction accuracy benchmark. Four source examples are photographs of printed synthetic documents; the receipt has the existing development-document provenance. Document type is the classifier prediction, including its known purchase_order prediction on the faint-copy example; expected labels were not passed to the extraction agent.

The agent initially received only isolated raw OCR, predicted document type, and an extraction contract. It was created with fork_turns=none. Exact source-record hashes and UTF-8 OCR hashes are recorded in inputs/provenance.json. The inherited Codex session model identity was not independently exposed as a provider model identifier. API cost and extraction latency were not reliably instrumented and are not claimed. Inputs are preserved; output files contain the agent-returned JSON content, saved as UTF-8 with platform newlines.

## Executed approaches and measured validity

| Approach | Records | Parse/schema valid | All populated fields literal-evidence supported | Review required | Arithmetic passed / failed / unavailable |
|---|---:|---:|---:|---:|---:|
| Direct OCR extraction | 5 | 5 | 2 | 5 | 2 / 0 / 13 |
| Evidence-first agent revision | 5 | 5 | 2 | 5 | 2 / 0 / 13 |
| Strict literal evidence withholding | 5 | 5 | 5 | 5 | 0 / 0 / 15 |
| Multi-view OCR, strict policy | 2 | 2 | 2 | 2 | 0 / 0 / 6 |

Schema/evidence/arithmetic results come from executing validate_experiment.py against contract.validate_record; validation.json preserves the original contract source hash and per-field/check findings; validation-final.json records a later replay against the current contract. A passing schema or substring check is not an accurate-field measurement. None of these records is ready for automatic acceptance. Missing subtotal/tax/discount were not treated as zero.

The evidence-first agent removed two receipt quantity assignments because OCR ordering did not establish reliable row associations. It proposed five contextual textual repairs without applying them: Om: -> From:, grentea -> green tea, Tx 45 -> Tk 45, {louse -> House, and TOMER COPY -> CUSTOMER COPY. These are not verified OCR corrections. In particular, expanding a clipped copy marker could change classification and must remain a proposal.

The strict variant is a deterministic derivative written by the child, not another independent LLM sample. It withholds six numeric fields because decimal strings such as 1850 are not literal substrings of original quotes such as 1,850. Six explicit formatting proposals retain the original comma-formatted source. This improves literal evidence compliance by discarding usable information; it does not improve OCR. A production contract should separately specify locale-aware numeric normalization with an auditable original-token mapping. Decimal/thousands ambiguity in receipt values such as 36.000 remains unresolved regardless.

## Multi-view rescue

A separate two-record input preserves result.heading_ocr_text exactly, including six form-feed-separated OCR views per document. Source-field/record hashes and boundaries are recorded in inputs/multiview-provenance.json. The verifier checks evidence against that exact multi-view string. The child was told not to duplicate repeated rows across views.

The delivery note gains one literal item description, Onion 1Kg, absent from its full-page OCR. No supported quantity or amount is recovered. The 1Kg package description is not treated as a delivered quantity. The purchase order gains no extra supported rows or amounts; independent views corroborate its header and support a proposed Om: -> From: text repair. Multi-view OCR helps, but does not recover the table needed for this extraction slice.

## Concrete boundaries reached

- The LLM can return contract-shaped JSON from OCR through sub-agents. The experiment does not establish an unattended runtime model endpoint: Codex sub-agent invocation is an experiment transport, not a deployable application backend.
- Raw classifier OCR has already discarded or corrupted much of the table content. More prompting cannot establish missing numeric operands. Additional OCR views rescued one item name, with no additional numeric row.
- Text-only correction can propose plausible text, but cannot verify absent characters, missing rows, local separator conventions, or row assignments against a document image.
- Substring evidence cannot prove field-role accuracy; receipt quantities passed literal checks before the evidence-first association audit removed them.
- Arithmetic can verify two readable line products in the direct trial, but cannot validate full totals without missing operands. Consistently wrong or misassigned values can still pass arithmetic.
- No independently reviewed field truth exists in this experiment, so accuracy, OCR correction improvement, confidence calibration, or real-world success rates cannot be measured.

A next useful experiment would retain OCR word boxes/table regions and compare a clearly labelled image-assisted extraction branch against reviewed numeric fields. It must preserve original OCR and proposed corrections separately. The initial OCR-only trials did not inspect images. The later image-assisted branch below inspected two images, without generating reviewed truth.

## Reproduce and audit

From project root: python services/document_pipeline/experiments/2026-10-24/validate_experiment.py

- inputs/ocr-only.json: five isolated full-page OCR strings and predicted types.
- inputs/multiview-ocr-only.json: two exact multi-view strings.
- inputs/*provenance.json: source and OCR hashes, provenance and limitations.
- outputs/direct-agent-response.json: original direct response.
- outputs/evidence-agent-response.json: agent evidence/association revision.
- outputs/strict-agent-response.json: deterministic literal-policy derivative.
- outputs/multiview-agent-response.json: actual multi-view extraction response.
- ../../prompts/ocr-extraction-pilot-v1.md: substantive prompts and follow-ups.
- validation.json: executed validity findings; no accuracy claims.

No raw corpus, models, annotations, reviewed history, existing recorded analyses, or shared Context files were modified by this pilot.


## Separate image-assisted branch

A second fresh fork_turns=none sub-agent was given only the two original demo image paths, predicted document types, a visual-observation schema, and instructions to inspect actual pixels. It was not given earlier extracted records, reviewed annotations, expected values, or ground truth. The resulting outputs/image-assisted-observations.json uses method=image_assisted_ai_observation and human_verified=false. Source image hashes and the provenance category source_kind=image_assisted_ai_transcription are preserved in inputs/image-assisted-provenance.json. This file is deliberately excluded from OCR-backed contract validation; observations were not substituted for immutable OCR evidence or canonical annotations.

| Source | PO rows / complete numeric rows | DN descriptions / supported quantity observations |
|---|---:|---:|
| Original full-page OCR direct trial | 1 / 1 | 0 / 0 |
| Multi-view OCR strict trial | 1 / 0 (formatting policy withholds prices) | 1 / 0 |
| Image-assisted AI observation | 2 / 2 | 5 / 5 |

The visual agent observed a second PO row: Onion 1kg, quantity20, unit price65, line total1300. It also observed the already OCR-readable rice row (24,1850,44400) and printed total45700. These values are AI observations, not measured correct extractions; arithmetic plausibility cannot establish truth. Missing subtotal/tax/discount remain null.

The delivery note visual observation contains five descriptions and quantities: Mustard Oil 1L/6; Milk Powder 500g/20; Detergent 500g/12; Onion 1kg/12; Salt 1kg/2. The agent observed no monetary columns, total, or currency on the printed document, so those remain null. Their absence may be legitimate for a quantity-only delivery note; unavailable monetary arithmetic must not imply an erroneous document. Image-assisted reading demonstrates that table information can remain visible in pixels even when these recorded OCR strings lose it. It does not provide an available vision backend for the local application.

The experiment therefore bypassed the OCR-text-loss boundary inside a Codex sub-agent. The current application still lacks an unattended extraction/vision runtime provider and independently reviewed field truth. The gateway's evidence contract currently references original OCR; it cannot automatically accept these image-only values as OCR-supported. No synthetic evidence quotes were manufactured to force acceptance.

Final replay is saved separately as validation-final.json; the earlier validation.json is preserved. Both report the same aggregate trial counts for these saved outputs. Re-running validate_experiment.py now defaults to validation-final.json, or accepts an optional output filename.
