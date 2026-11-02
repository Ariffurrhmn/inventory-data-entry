# Pre-Defence Slide Content

Content only — no design, no layout, no file built yet. Pulled from the report and `demo_worked_example.md` so nothing here is invented. 15 slides, matching the outline in `plan.md`.

---

## Slide 1 — Title

**On slide:**
> Automated Inventory Data Entry through Intelligent Character and Document Structure Recognition
>
> [Team member names + IDs]
> Supervisor: Md. Mijanur Rahman
> Department of CSE, BUBT — CSE 498A, Summer 2026

**Speaker note:** Just introduce the team and the title. Ten seconds, move on.

---

## Slide 2 — Problem Statement

**On slide:**
- Small shops receive invoices, receipts, delivery notes — as paper or photos.
- No common layout. Every supplier's document looks different.
- Someone has to read each one and type it into the inventory system by hand.
- Slow. Error-prone. Often just doesn't happen consistently.
- Existing inventory software assumes clean data already exists — it doesn't solve this.
- Plain OCR alone isn't enough either — it reads text, but doesn't know if it's looking at a price, a quantity, or what kind of document it even is.

**Speaker note:** Ground this in something visual if possible — hold up or show a real receipt/invoice. The core line: "someone still has to type this in by hand."

---

## Slide 3 — Motivation

**On slide:**
- **The manual process is everywhere.** Even businesses with digital inventory software still type in data by hand — the software assumes someone already did the data entry.
- **The technology is finally ready.** Cloud OCR and language models are mature, cheap, and API-accessible now — this wasn't practical a few years ago.
- **But LLMs can be wrong silently.** A language model can misread a price or invent a value with no visible sign anything's wrong. That's the real design challenge — not reading the document, but trusting what you read.

**Speaker note:** Three points, in that order — problem is real, technology is ready, but trust is the hard part. This sets up why verification (later slide) matters.

---

## Slide 4 — Objectives

**On slide:**
1. Build a recognition pipeline combining OCR with document structure/type recognition — read the text *and* know what kind of document it is.
2. Design a schema-constrained extraction step — an LLM converts recognized text into structured JSON, guaranteed to match a fixed schema.
3. Engineer a verification step — cross-check extracted numbers against the document's own arithmetic, flag anything uncertain.
4. Design the service as a stateless, idempotent API — no owned inventory state, safe against duplicate submissions.
5. Evaluate the system on recognition accuracy and extraction accuracy.

**Speaker note:** These map 1:1 to the 6 pipeline modules shown two slides from now. Don't over-explain here — just state them, the architecture slide does the explaining.

---

## Slide 5 — Related Work / Gap

**On slide:**
- **General cloud document-AI** (AWS Textract, Google Document AI, Azure) — reads text well, but doesn't treat document-type classification as a first-class feature.
- **Purpose-built invoice extraction APIs** (Nanonets, Mindee, Veryfi, etc.) — good field extraction, but general-purpose, not built around a document-structure-first pipeline.
- **Inventory/ERP platforms** (Finale Inventory, HandiFox, Apptricity) — support mobile capture, but document capture is one step inside a bigger owned system, not a standalone gateway.
- **The gap:** nobody combines document-structure recognition as a first-class output with a stateless, verified, API-first pipeline built for messy small-business documents.

**Speaker note:** Keep this to "here's what exists, here's what's missing" — don't read the whole comparison table, just the gap line at the end is the takeaway.

---

## Slide 6 — System Architecture

**On slide:** *Figure 2 (`figures/fig2_architecture.png`)*

- Mobile app: capture only. No processing on the device.
- Everything else — OCR, extraction, verification — runs in the cloud.
- Output: a stateless JSON API call, consumed by the shop's existing ERP/inventory system.

**Speaker note:** Walk the diagram left to right: capture → cloud pipeline → API → consuming system. Emphasize "mobile app does nothing but take the photo" — that's a deliberate boundary, not a limitation.

---

## Slide 7 — Pipeline Detail (6 Modules)

**On slide:** *Figure 4 (`figures/fig4_pipeline.png`)*

1. **Document Capture** — photo/scan, quality checks, idempotency key.
2. **Character Recognition (OCR)** — text + bounding boxes.
3. **Document Structure & Type Recognition** — classifies PO / receipt / customer copy / delivery note.
4. **Schema-Constrained Extraction** — LLM converts text into structured JSON.
5. **Digitization API** — stateless, idempotent submission + retrieval endpoints.
6. **Data Model** — the only stored state: a `Submission` record (for idempotency/audit).

*(Verification sits between modules 4 and 5 — arithmetic check + confidence scoring — covered on its own in the next two slides via the worked example.)*

**Speaker note:** This is the core technical slide. Go module by module, one sentence each. Don't rush — this is what most Q&A questions will reference back to.

---

## Slide 8 — Worked Example (Clean Case)

**On slide:**
- Sample invoice image (fake/illustrative — clearly labeled as such).
- Purchase order: 3 line items, printed, clean layout.
- Runs through all 6 modules.
- Output JSON — every `arithmetic_check: "passed"`, `review_required: false`.

*(Use the exact JSON from `demo_worked_example.md`, clean-case block.)*

**Speaker note:** Say explicitly: "This is a hand-built illustrative example — nothing is implemented yet." Walk through the JSON briefly, point at `arithmetic_check` and `review_required` fields specifically, since those matter for the next slide.

---

## Slide 9 — Worked Example (Flagged Case)

**On slide:**
- Same invoice, one field misread: quantity "24" read as "21".
- Math doesn't add up: 21 × 15.00 = 315.00 ≠ stated line total 360.00.
- Result: `arithmetic_check: "failed"`, `review_required: true` on that line.
- The record is still returned — just flagged. No human review queue. No blocking.

**Speaker note:** This is the "trust" moment of the talk. The point: the system catches its own extraction errors automatically, using nothing but the document's own math — no manual confirmation step anywhere in the pipeline.

---

## Slide 10 — What's Explicitly Out of Scope

**On slide:**
- **No item-name matching / catalog.** "Coke" vs. "Coca-Cola" reconciliation is left to the consuming ERP.
- **No human-in-the-loop confirmation.** Nothing gets queued for a person to approve. Verification is fully automatic.
- **No inventory ownership.** No stock levels, no transactions, no valuations, no product catalog stored anywhere in this system.
- **No on-device processing.** Everything but capture runs in the cloud — ruled out on purpose, keeps the mobile client thin.
- **English-only**, in this version.

**Speaker note:** State this proactively before anyone asks. One line each is enough — the point is "we know what we cut, and why."

---

## Slide 11 — Data Model

**On slide:** *Figure 7 (`figures/fig7_data_model.png`)*

- One entity: `Submission` — id, shop, timestamp, processing status, result reference.
- That's it. No Shop-owned catalog, no Stock, no Transaction, no Valuation entity.
- Deliberate: this system is a gateway, not an inventory system.

**Speaker note:** Short slide. The point is the *absence* of entities, not the one that exists. "What's not here is the design decision."

---

## Slide 12 — Methodology

**On slide:** *Figure 1 (`figures/fig1_methodology.png`)*

Five phases, iterative — not a strict waterfall sequence:
1. Requirement analysis & document collection
2. Data model & API contract design
3. Recognition pipeline
4. Verification & digitization API core
5. Evaluation & benchmarking

Evaluation results feed back into the API contract and extraction design — the cycle repeats.

**Speaker note:** Emphasize "iterative, not waterfall" — say why: the confidence threshold and JSON schema can't be finalized correctly before real documents are collected and tested against.

---

## Slide 13 — Evaluation Plan

**On slide:**
| Module | What we'll measure |
|---|---|
| Character recognition | Character/Word Error Rate |
| Document type & structure | Classification accuracy, confusion matrix |
| Schema-constrained extraction | Schema-validity rate, field-level precision/recall |
| Verification | Silent-error rate at varying confidence thresholds |
| Digitization API | Latency, correctness under duplicate submission |

**Headline claim to test:** arithmetic self-validation + confidence scoring measurably reduce silent errors, compared to no verification at all.

**Speaker note:** No numbers exist yet — this is the *plan* for Chapter 4. Say that plainly if asked.

---

## Slide 14 — Open Decisions

**On slide:**
1. OCR service — cheapest option.
2. LLM for extraction — cheapest among top-10 providers.
3. Constrained-decoding mechanism — provider-native JSON mode.
4. Confidence signal — token log-probabilities first; fall back to sampled consistency if unavailable.
5. Document-type classifier — few-shot first, fine-tune once the corpus is collected.
6. Result delivery — synchronous by default.

**Speaker note:** Present these as resolved defaults, not open gaps — "we've made a call on each, here's what and why." Decision 4 (confidence signal) is the one most likely to get a follow-up question — know the tradeoff (log-probs are free but often unavailable via commercial APIs; sampling always works but costs more).

---

## Slide 15 — Closing / Q&A

**On slide:**
- Recap: 4 contributions — recognition pipeline, schema-constrained extraction + verification, stateless idempotent API, evaluation methodology.
- This is a design-stage submission (CSE 498A). Implementation and results come next (CSE 498B).
- Thank you. Questions?

**Speaker note:** Keep it tight. Don't re-explain — just point back at slide 4's objectives as "these are what we delivered on, at the design level."

---

## Notes for whoever builds the actual slides

- Slides 6, 7, 11, 12 use existing figures directly — no new diagrams needed.
- Slides 8–9 need the fake invoice image (not yet chosen — pick a stock/sample image, or a real anonymized one).
- No slide currently plans a mobile-app wireframe — per `ui_demo_plan.md`, that's optional/lowest priority; add only if time allows after the rest is solid.
- Every claim above traces back to the report or `demo_worked_example.md` — nothing invented for the slides.
