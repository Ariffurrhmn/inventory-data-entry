# Project overview

Inspected 2026-10-19.

## Purpose and stage

Title: Automated Inventory Data Entry through Intelligent Character and Document Structure Recognition.
The directory name says Inventory Management System, but the current written design is a document-digitization gateway feeding existing inventory/ERP systems.

The original report and presentation sources describe a CSE 498A design-stage project. Classifier implementation began on 2026-10-19 in services/document_classifier/. No mobile app or digitization backend has been identified. See STATUS.md for current implementation results.

## Proposed processing flow

Mobile photograph/scan → cloud OCR (text and bounding boxes) → four-class document image classification → schema-constrained LLM extraction → arithmetic checks and confidence scoring → JSON API for a consuming ERP.

Four document classes: purchase_order, receipt, delivery_note, customer_copy. Capture is mobile; processing is cloud-side. Proposed API semantics are stateless with respect to inventory and idempotent for submissions. A Submission record supports processing status, result references, audit, and retry handling.

Arithmetic checks compare quantity × unit price with line totals and totals with document totals. Low-confidence/mismatched output is flagged through review_required. This flag does not imply an implemented human review queue. Consistently wrong values can pass arithmetic checks.

## Scope boundaries

Current user scope (2026-10-20): English-language printed/typeset/thermal documents only. Handwritten slips, handwritten transaction fields and handwriting-style synthetic bodies are outside scope. Photographs of printed documents remain valid candidates; ignore incidental signatures rather than transcribing them. No owned product catalog, stock ledger, valuation, item-name reconciliation, on-device inference, or internal human approval loop in the current design. Older literature and diagrams may discuss broader ideas; do not infer scope from a paper's presence.

## Primary evidence

- ../docs/design/inventory_data_entry_report_ch1_2_3_draft.md — detailed design, collection protocol, schema, evaluation plan.
- ../docs/design/presentation_slide_content.md and pages.md — presentation narrative.
- ../docs/design/demo_worked_example.md — illustrative clean and flagged JSON.
- ../docs/design/swot_feasibility.md — risks and feasibility discussion.
- ../figures/figures.md — diagram descriptions.
- ../ChatGPT_Bridge/STATUS.md — latest explicit image workflow checkpoint (2026-10-10).
- ../synthetic_dataset/README.md — synthetic corpus provenance and expected composition.

These are project-authored claims, not independently verified research results. The report explicitly warns that some document-structure citations need checking against the original papers.


Latest user scope clarification (2026-10-19): the classifier ONLY predicts purchase_order, receipt, delivery_note, or customer_copy. Table/region detection and numerical extraction are outside this classifier. Dataset-2 contains photographs of printed synthetic/generated originals, confirmed by the user.

Implementation update 2026-10-19: an experimental local OCR-text four-class classifier is now implemented alongside the historical image baseline. See Context/OCR_TEXT.md. OCR/text comparisons and a training-only augmentation run have been measured; this does not implement downstream LLM/table extraction, a mobile app or the gateway API.

Running prototype update (2026-10-20): printed-only OCR/classification now has a trained active model and local image-upload/pasted-text UI on port8767. Services/document_classifier/PRINTED_CLASSIFIER.md documents its grouped development split, heading-assisted inference and preliminary validation. No downstream table/number extraction, ERP API or mobile application was implemented.

Current selected implementation (2026-10-20): printed_v3_explainable is an explainable hybrid of corrected local OCR, versioned printed-document rules and trained TF-IDF/ComplementNB. It crossed90% on adaptive development checks, with no new independent final evaluation. See services/document_classifier/EXPLAINABLE_CLASSIFIER.md. Classification remains four types only; no downstream table/number extraction added.

Supervisor demo update (2026-10-20): classifier/ now packages the local Document Lab demo and consolidated engine/research history. It shows image/OCR classification, faithful explanations, recorded development examples and explicit JSON report saving. Current user launch: classifier/Open Demo.cmd, port8770. Raw Dataset/ and annotation history remain separate and preserved; shared memory stays in Context/.


Downstream update (2026-10-24 follow-up): local gateway now optionally localizes ruled tables/cells automatically, retaining separate OCR evidence and original coordinates. This remains downstream of the unchanged classifier. A separate offline human field-evaluation workflow is implemented, without creating independent truth or an internal ERP approval loop. No unpaid unattended generative model endpoint has been provisioned; see services/document_pipeline/experiments/2026-10-24/downstream_followup/README.md for the actual hardware/provisioning blocker and measured development experiments.
