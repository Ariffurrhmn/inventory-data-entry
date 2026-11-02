# Figures Index — Chapters 1–3 (Current Scope)

This index documents the figures currently referenced by `inventory_data_entry_report_ch1_2_3_draft.md`. All figures are hand-authored SVG (no Mermaid, no external libraries), styled consistently with a shared font stack (`'Segoe UI', Arial, sans-serif`), a blue palette for recognition/structure stages, green for output/success/API/verification, orange/purple for decision points or emphasis, and red reserved for content explicitly excluded from scope. Each SVG is rendered to PNG at roughly its original pixel width (2100–2400 px) for embedding in the report. Source for each figure lives in its own `.svg` file in this directory — see below rather than inline, since the sources are sized for direct editing in place.

This project's scope was cut during drafting: item-name standardization against a product catalog, and the confirm-once/human-in-the-loop (HITL) confirmation workflow, were both removed. The system now does OCR → document structure/type recognition → schema-constrained LLM extraction → arithmetic self-validation + confidence scoring (flag low-confidence records, no human review loop) → stateless idempotent JSON API delivery. The system owns no inventory state and no product catalog. Six of the seven figures below were rebuilt against this current scope; Figure 5 was already correct and is unchanged.

(Figure 3, the item-standardization workflow, has been fully removed from the report along with the standardization module and is not documented here. Figure 9, the Gantt chart, is deferred to Chapter 5 and is likewise not documented here.)

---

## Figure 1. Iterative, Evaluation-Driven Development Lifecycle

**Source:** `fig1_methodology.svg` / `fig1_methodology.png`

**What changed:** Reduced from six phases to the five phases Section 3.1 now describes — requirement analysis and document collection; data model and API contract design; recognition pipeline; verification and digitization API core; and evaluation and benchmarking. The old phase 4 ("Standardization, Verification & Human Loop") was removed; the verification work it described (arithmetic self-validation, confidence scoring) now lives inside the merged phase 4, "Verification & Digitization API Core." The feedback-loop arrow (evaluation feeds back into API contract / extraction design) is preserved.

**Caption (as used in the report):** *Development methodology: the phases of the iterative, evaluation-driven lifecycle and the feedback loop from evaluation back into the API contract and extraction design.*

---

## Figure 2. Proposed System Architecture

**Source:** `fig2_architecture.svg` / `fig2_architecture.png`

**What changed:** Removed the item-standardization stage, the confirmed-mapping cache, the cache-hit/miss decision diamond, and the human-reviewer box entirely. The pipeline is now a straight line: API Gateway → OCR + Document Structure/Type Classification → Schema-Constrained Extraction → Arithmetic Self-Validation + Confidence Scoring → JSON Output → authorized ERP/inventory system via API. Verification is shown as a step in the linear flow, not a branch to a human actor; a record failing the check is flagged `review_required: true` in the JSON but is delivered like any other record. A note box states the system's only persistent state (the Submission log) and that item-name reconciliation is left to the consuming ERP.

**Caption (as used in the report):** *Proposed system architecture: mobile capture, cloud-hosted recognition and extraction pipeline with arithmetic self-validation, and delivery to an authorized ERP or inventory system via the digitization API.*

---

## Figure 4. Detailed Processing Pipeline

**Source:** `fig4_pipeline.svg` / `fig4_pipeline.png`

**What changed:** Rebuilt to match modules 3.4.1–3.4.5 exactly (Document Capture → Character Recognition → Structure & Type Recognition → Schema-Constrained Extraction → Digitization API), with the Data Model (3.4.6) called out separately as a non-processing-stage note, since it is a data entity, not a pipeline step. The confirmed-mapping cache and the cache-hit/confidence-check decision pair are gone. In their place is a single verification decision — "Passes check & above threshold?" — with a "yes" branch to an "Included at full confidence" (`review_required: false`) box and a "no" branch to a "Flagged, still delivered" (`review_required: true`) box; both feed into the Digitization API module. There is no human-loop diamond and no routing to a reviewer actor.

**Caption (as used in the report):** *Detailed pipeline diagram: per-stage inputs and outputs from captured image through to JSON response, showing where arithmetic self-validation and confidence flagging attach.*

---

## Figure 5. Document-Type Taxonomy (unchanged)

**Source:** `fig5_doctype_taxonomy.svg` / `fig5_doctype_taxonomy.png`

**Status:** Not modified. This figure was already correct for the current scope — it shows the four document-type classes (purchase order, delivery note, customer copy, receipt) and their distinguishing cues, and does not touch standardization or HITL concepts. It served as the visual style reference (colors, fonts, rounded-rectangle header-band treatment, bottom explainer box) for rebuilding the other six figures.

**Caption (as used in the report):** *Document-type taxonomy: the four target classes with the structural and lexical cues that distinguish them, and the inventory implication of each.*

---

## Figure 6. API Sequence Diagram

**Source:** `fig6_api_sequence.svg` / `fig6_api_sequence.png`

**What changed:** Removed the "Human Reviewer" actor/lane and the cache-hit-fast-path and confirm-once-branch swimlanes entirely. Actors are now Mobile Client, API Gateway, Pipeline, and Consuming ERP. The sequence shows: normal submission (POST with idempotency key → 202 Accepted → server-side OCR → structure recognition → extraction → arithmetic self-validation/confidence scoring → result ready), result delivery (GET by the consuming ERP → 200 OK with JSON per Table 3.4), and duplicate submission (same idempotency key → original result returned, no reprocessing) per module 3.4.5 and Section 2.1.4.

**Caption (as used in the report):** *API sequence diagram: capture → submit (with idempotency key) → process → result retrieval by the consuming ERP, including the duplicate-submission path returning the original result without reprocessing.*

---

## Figure 7. Entity-Relationship Diagram (Data Model)

**Source:** `fig7_data_model.svg` / `fig7_data_model.png`

**What changed:** Reduced from four entities (Shop, Submission, CatalogEntry, ConfirmedMapping) to the single entity Section 3.4.6 now describes: **Submission** (`submission_id` PK, `shop`, `received_at`, `processing_status`, `result_json_ref`). Added an explicit "deliberately excluded" callout box, styled after Figure 5's explainer-box convention, listing Shop, CatalogEntry, ConfirmedMapping, Stock, Transaction, and Valuation as entities that belong to the consuming ERP rather than this system.

**Caption (as used in the report):** *Entity-relationship diagram: the Submission record, alongside the inventory and catalog entities deliberately excluded from the gateway's scope.*

---

## Figure 8. Evaluation Framework

**Source:** `fig8_evaluation.svg` / `fig8_evaluation.png`

**What changed:** Reduced to the module rows the current "Material Reserved for Later Chapters" evaluation table specifies: Character Recognition (3.4.2), Document Type & Structure (3.4.3), Schema-Constrained Extraction (3.4.4), Verification (arithmetic self-validation + confidence scoring — no module number, since it is not one of the six 3.4.x modules), and Digitization API (3.4.5). The "Standardization" row and the "Verification & HITL" row (with its confirmations-required-per-document metric) are both gone. The verification row's metrics are now silent-error rate at varying confidence thresholds and arithmetic-check catch rate, with baseline "no verification (extracted values returned as-is)"; the Digitization API row has no baseline. The headline-evaluation callout no longer cites "Margatina and Aletras [20]" (removed from the report's references) — the caution sentence is reworded to state plainly that a threshold tuned on public benchmarks may not transfer to real documents, matching the report's current "A caution on validity" paragraph.

**Caption (as used in the report):** *Evaluation framework: each pipeline module mapped to its metrics and its comparison baseline, with the verification accuracy tradeoff curve identified as the headline contribution.*

---

## Rendering notes

Each SVG was rendered to PNG using `sharp` (via `npx sharp-cli -i figN.svg -o figN.png resize <width> <height>`), matching the original PNG's pixel dimensions as closely as the redesigned layout allowed. No Mermaid CLI or other diagramming library was used for the final artifacts — Mermaid was only ever a prototyping option, never the delivered format, per the convention this file originally established.
