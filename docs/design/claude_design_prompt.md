# Prompt for Claude Design — Full Presentation Deck

## What this is

A 17-slide university pre-defence presentation. BUBT (Bangladesh University of Business and Technology), Department of CSE, CSE 498A capstone — a design-stage proposal defence in front of an academic panel. **Nothing described in this deck is built or implemented yet.** This is a design proposal being defended, not a product demo. That distinction must stay visible throughout — several slides explicitly say "nothing is running yet" and the deck should never accidentally read as showing a working system.

The project: a system that photographs paper invoices, receipts, delivery notes, and purchase orders from small shops, and turns them into clean, structured JSON data that an existing inventory/ERP system can consume through an API. The pitch, in one line: reads a document, checks its own work, and hands off clean data — nothing more, nothing held back.

## Audience and tone

Academic panel — CSE faculty evaluating engineering rigor at a design/proposal stage. Not a sales pitch, not a general public audience. The tone throughout is precise, honest about what's decided versus what's still open, and unafraid to name its own limitations before being asked. Several slides are written to pre-empt likely panel questions rather than dodge them — that character should come through visually too: confident, not defensive; plain-spoken, not hype-driven.

## Format

17 slides, each its own artboard/section, landscape widescreen proportions (design for a ~16:9 canvas per slide — something that reads correctly as one projected slide, not a scrolling document). Output as a single HTML artifact containing all 17 slides as sequential full-bleed sections (each sized to fill the viewport on its own, scrollable or paginated between them — whichever mechanism reads most like an actual slide deck). This deck needs to work as something presented live in a room, and also hold up as a leave-behind reference read on a laptop afterward.

## Visual system across the whole deck

- **One consistent visual language for all 17 slides** — same palette, same type pairing, same "module block" / "card" treatment reused wherever content repeats in shape (e.g. the six pipeline modules split across slides 7 and 8 must look like two halves of one continuous system, not two unrelated slides).
- Treatment: polished utilitarian, not editorial. Real typographic hierarchy, considered spacing, a genuine palette — but no giant decorative hero slides, no marketing flourish, no illustration unrelated to the actual content. This is a technical engineering defence, not a startup pitch deck.
- Pick a real, specific palette and type pairing for a document-processing / data-pipeline systems subject — something that reads as precise and structural, appropriate for a room of CSE faculty. Not a generic "tech blue" default, not a cream-and-terracotta AI-generated look, not a purple-gradient hero. Ground the palette in the actual subject: paper documents becoming structured data — there is real visual material here (the texture of a scanned invoice next to the crispness of clean JSON, for instance) worth drawing from rather than defaulting to abstract tech-brand color.
- No emoji as section markers or bullet replacements. No accent color bars/stripes down slide edges or card sides. Numbered elements (module 1–6, the five methodology phases, the six open decisions) are numbered because the order is real and meaningful — encode that with actual sequence/flow treatment, not decorative badge numbers.
- Both light and dark theme variants, per the standard token-based three-state pattern (bare `:root` = full light palette; `@media (prefers-color-scheme: dark)` guarded `:root:not([data-theme="light"])`; `:root[data-theme="dark"]` override) — this may be presented on a variety of room setups and should hold up either way.
- Everything on every slide must be readable at a glance from across a room when projected — this is presented live, not scrolled through slowly on a laptop.

## Exact content, slide by slide

Use this content verbatim in substance — do not invent numbers, claims, or facts beyond what's given here. Where a slide includes a "have ready if asked" note, that's speaker backup material, not something that necessarily needs to be printed on the slide itself — use judgment on what's core content for the slide face versus material to keep light/secondary (e.g. a footnote, a smaller aside) versus omit from the visual slide entirely and leave to the presenter to say aloud.

---

### Slide 1 — Title

Automated Inventory Data Entry through Intelligent Character and Document Structure Recognition

Subtitle: "Turning paper invoices into clean, structured data — automatically."

Team: Arifur Rahman, Meer Mushfiqur Rahman, Fatema Akter Akhi, Sheikh Ramisha Zubaydah
Supervisor: Md. Mijanur Rahman
Department of Computer Science and Engineering, BUBT — CSE 498A, Summer 2026

---

### Slide 2 — Problem Statement

Two-column layout, not a bullet list.

**Left column — what happens today:** A shop owner gets a paper invoice. Different suppliers lay them out differently — no fixed template across the board. Someone reads it, line by line, and retypes it into whatever system the shop uses. Every single day.

**Right column — why nothing solves this:** Inventory software expects the data to already be typed in — it isn't built to take a photo as input. Plain OCR reads the text, but has no idea if it's looking at a price, a quantity, or even what kind of document this is.

**Bottom line, standing alone, pulling both sides together:** The real bottleneck isn't reading the document — it's turning it into something a system can actually use.

---

### Slide 3 — Motivation

Three points, each with a "why it's true" line underneath — not just headlines.

**1. The manual process is everywhere.** Even a shop that already bought inventory software is still stuck doing this by hand — the software was never the bottleneck. The data entry was.

**2. The technology is finally ready.** Two specific things changed recently: language model providers started offering a mode that guarantees structured output instead of free-form text, and running these models at the volume a small shop needs became cheap enough to be practical. Both recent — this wasn't a reasonable engineering bet even two or three years ago.

**3. But LLMs can fail silently.** The model reads "24" as "21," produces a confident-looking number, and nothing about the output looks wrong. The danger isn't that it fails — it's that failure looks identical to success. That's the real design challenge this project takes on. *(A small forward-pointer here is worth including: "shown in detail later in the deck.")*

---

### Slide 4 — Objectives

Four objectives (not five — evaluation is folded into objective 4 rather than standing alone as a peer goal), each with a "why it matters" line.

**1. Build a recognition pipeline combining OCR with document structure/type recognition.** The real objective is reading the text *and* knowing what kind of document it is at the same time, because the same field means something different on a purchase order than on a delivery note.

**2. Design a schema-constrained extraction step.** The output is *guaranteed* to match the schema — structurally impossible to be malformed, not just usually correct. Most inventory and ERP software already accepts structured data through an API — that's the natural handoff point this is designed for.

**3. Engineer a verification step, and design the service as a stateless, idempotent API.** Verification catches errors using the document's own internal math (quantity × price = stated total) — and plainly: it catches numbers that don't add up internally, but won't catch an error where every related number was misread consistently so the math still checks out despite being wrong. That's a real, named limit. Separately: the system owns no inventory data, so a retried or duplicate submission can't corrupt anything downstream.

**4. Evaluate the system on recognition accuracy and extraction accuracy.** Prove all of the above is measurable and testable once built.

---

### Slide 5 — Related Work / Gap

Present as a small comparison table, not bullets. Rows = the three competitor categories plus this project; columns = three gap criteria.

| | Knows document type | Owns no inventory data | Auto-verifies output |
|---|---|---|---|
| General cloud document-AI (Textract, Document AI, Azure) | Partial | — | — |
| Purpose-built invoice extraction (Nanonets, Mindee, Veryfi) | Partial | — | Partial (human-reviewed, not automatic) |
| Inventory/ERP platforms (Finale, HandiFox, Apptricity) | — | No (owns the inventory data) | — |
| **This project** | **Yes** | **Yes** | **Yes** |

---

### Slide 6 — System Architecture

Keep this diagram intentionally simple — 3 to 4 blocks, a "zoomed out" view (mobile app → cloud pipeline → API → consuming system), since slides 7–8 hold the detailed zoomed-in version. It should read as a deliberately higher-level companion to slides 7–8, not a competing diagram of the same thing.

- Mobile app: capture only. No processing on the device.
- Everything else — OCR, extraction, verification — runs in the cloud.
- Output: a stateless JSON API call, consumed by the shop's existing ERP/inventory system.

---

### Slide 7 — Pipeline Detail, Part 1: Capture Through Classification

*Modules 1–3 of a 6-module pipeline. This slide visually pairs with slide 8 (modules 4–6) as two halves of one continuous, numbered sequence — same module-block visual treatment, same numbering style, a sense of continuation from this slide into the next.*

**1. Document Capture** — Take the photo, check it's not blurry or cut off, tag it so it's never processed twice. *Why:* a bad photo poisons everything downstream; catching it here is cheap, catching it later isn't.

**2. Character Recognition (OCR)** — Read the text off the image. *Why:* this is the foundation everything else stands on.

**3. Document Structure & Type Recognition** — Figure out what kind of document this is: purchase order, receipt, customer copy, or delivery note. *Why:* the same field means something different on different document types.

---

### Slide 8 — Pipeline Detail, Part 2: Extraction Through Data Model

*Modules 4–6, continuing directly from slide 7's numbering and visual system.*

**4. Schema-Constrained Extraction** — Turn the text into structured data, in a fixed format every time. *Why:* guarantees the output is never malformed — that's what makes it safe to hand off automatically.

**5. Digitization API** — Send a document in, get the structured result back. Safe to retry without creating duplicates. *Why:* this is the actual handoff to the real world — where this project's output becomes someone else's input.

**6. Data Model** — The only thing this system remembers: a record of what was submitted and when. *Why:* deliberate, not an oversight — the system remembers almost nothing on purpose, because it's not supposed to own the shop's inventory data.

---

### Slide 9 — Worked Example (Clean Case)

**Important framing, should be visually foregrounded on the slide itself, not buried:** "Hand-built, illustrative example — nothing is running yet. This shows what the pipeline is designed to produce, once built." This caveat needs to be visually prominent, not a small disclaimer — the whole point is this must never read as a demo of a working system.

Two-panel layout: input on one side, output on the other.

**Input panel:** A photo/mockup of a purchase order. Supplier: ACME Beverage Distributors. Three line items — Coca-Cola, Sprite, Mineral Water — each with quantity, unit price, line total, plus a grand total.

**Output panel, in plain terms (not raw JSON syntax on the slide):**
- Document type: purchase order, high confidence.
- Three items extracted correctly.
- Every line's math checks out.
- Nothing flagged — this document goes straight through.

---

### Slide 10 — Worked Example (Flagged Case)

The payoff of the two-part story — the "trust" moment of the deck. Same illustrative-example framing as slide 9 should carry through visually (same caveat treatment).

**Input panel:** Same invoice as slide 9, but OCR misreads one number: quantity "24" read as "21."

**Output panel:**
- 21 × 15.00 = 315.00 — but the invoice states the line total as 360.00. Mismatch.
- That line marked as failed.
- The record gets flagged, needs a second look.
- The record still goes through — nothing is blocked, nothing sits in a queue waiting for a person.

Closing line, should be visually emphasized as the takeaway of this slide: the system caught its own mistake automatically, using nothing but the invoice's own arithmetic — no manual review step anywhere in the pipeline.

---

### Slide 11 — What's Explicitly Out of Scope

A clean, honest list — five items, presented as deliberate boundaries, not gaps or apologies.

- No item-name matching or catalog. "Coke" vs. "Coca-Cola" is left to the consuming ERP.
- No human-in-the-loop confirmation. Verification is fully automatic.
- No inventory ownership. No stock, transactions, valuations, or product catalog stored here.
- No on-device processing. Everything but capture runs in the cloud.
- **English-only, in this version.** This is the one item that may draw the most pointed question from a Bangladesh-based panel — the visual treatment shouldn't hide it or make it look like an afterthought; it should read as a stated, deliberate scope decision, same weight as the others.

---

### Slide 12 — Data Model

*Reference the same diagram concept as the report's data model — a single entity called "Submission."*

**Framing, visually prominent, same treatment as slide 9's caveat:** "Nothing is built yet — this is a design decision, not a working database."

**What's proposed — one thing:** a record of each submission: which shop it came from, when it arrived, whether it's done processing, and where to find the result. Nothing more.

**Why so little, on purpose:** the moment this system starts holding stock counts, a product list, or transaction history, it stops being a simple gateway and starts competing with the software the shop already runs. Keeping it minimal is what makes it safe to plug into any existing system without a fight over who owns the data.

---

### Slide 13 — Methodology

Five phases, iterative — presented as a real sequence with a feedback loop, not a static list. Mark phase 1 as "currently here."

1. Requirement analysis & document collection *(current phase)*
2. Data model & API contract design
3. Recognition pipeline
4. Verification & digitization API core
5. Evaluation & benchmarking

Evaluation results feed back into the API contract and extraction design — show this as a return arrow/loop from phase 5 back toward phase 2, not just implied in text.

Worth surfacing visually: phase 1's document collection is a dependency that phase 3's classifier work depends on — this is the phase most likely to set the pace for the whole project, since it depends on outside cooperation (shops sharing documents), not just internal work rate.

---

### Slide 14 — How the System Learns to Recognize Different Slip Types

Two-stage answer, presented side by side or as a sequence (stage one active now, stage two coming once data exists).

**Stage one — no training data needed, starts immediately.** Ask a language model to guess the document type from recognized text and rough layout. No training required. Less accurate, costs more per document, but works from day one.

**Stage two — a purpose-built classifier, trained on real examples.** Once real documents are collected, fine-tune a layout-aware model (reads text *and* where it sits on the page) on that data. Checked against the stage-one baseline to confirm it's actually better.

**Why two stages:** data collection shouldn't block the rest of the build. Stage one unblocks everything else while real documents are gathered in parallel.

**Where the data comes from:** small shops, approached directly, with informed consent — told how documents will be used, how long they're kept, free to withdraw. Business-sensitive details anonymized. Targeting at least 30 examples per document type (purchase order, receipt, delivery note, customer copy), deliberately matching real-world proportions of printed/handwritten/thermal-printed rather than forcing an even split.

---

### Slide 15 — Evaluation Plan

No real numbers exist yet — this is the plan for how success will be measured, once built. State that plainly on the slide, not hidden.

Present as a scannable checklist — bold the metric name, keep elaboration minimal on the slide face itself (this is dense content; the visual treatment should favor a clean grid/table over paragraphs).

- **Character recognition:** how much of the text was read correctly (character/word-level comparison against ground truth).
- **Document type & structure:** did it correctly identify the document type — full confusion-matrix-style breakdown of what gets confused with what, not just one accuracy number.
- **Schema-constrained extraction:** did output come out in the correct structured format, and were the values inside it correct.
- **Verification (the headline test):** how often does the arithmetic check catch a real mistake, versus how often does a wrong value slip through — measured across different sensitivity thresholds.
- **Digitization API:** latency, and correctness under duplicate submission.

The one claim the whole evaluation plan is built to prove, worth visual emphasis as a closing statement on this slide: checking a document's own math and scoring confidence catches meaningfully more errors than not checking at all.

---

### Slide 16 — Open Decisions

Six items, presented as resolved engineering calls with stated reasoning — not open questions or gaps. Confident framing throughout.

1. **OCR service** — cost-optimized among comparable-accuracy options.
2. **Language model** — cost-optimized among top-ten providers.
3. **Output-format enforcement** — the provider's built-in JSON mode (guarantees valid structured output without a separate tool).
4. **Confidence scoring** — try the free method first (model-reported confidence where available); fall back to asking the same question multiple times and checking agreement where it isn't.
5. **Document-type classifier** — the two-stage plan already covered (slide 14).
6. **Result delivery** — synchronous by default (send a document, wait, get the answer in that same request); revisit only if processing proves too slow.

---

### Slide 17 — Closing / Q&A

**One sentence, should be the visual centerpiece of this slide, set apart from the rest:** "This system reads a document, checks its own work, and hands off clean data — nothing more, nothing held back, nothing hidden from the receiving system."

**Recap — four contributions:**
- A recognition pipeline that reads text and knows what kind of document it's looking at.
- Extraction that's guaranteed to come out structured, backed by a verification step that catches its own mistakes.
- A stateless, idempotent API — safe to plug into any system without owning anyone else's data.
- A plan for proving all of the above actually works, once built.

**Where this stands:** design-stage submission (CSE 498A). Implementation and real results come next semester (CSE 498B).

**Biggest open risk, named proactively:** collecting enough real documents from real shops to properly train the stage-two document-type classifier — the piece most outside direct control.

Thank you. Questions?

## What NOT to do

- Do not invent extra metrics, numbers, features, or claims beyond what's given above.
- Do not let any slide imply a working system exists — the "nothing is built yet" framing on slides 9, 10, and 12 is load-bearing and must stay visually prominent, not buried as fine print.
- Do not soften or hide slide 11's English-only scope cut — it should read as a clearly stated, deliberate decision, not something tucked away.
- Do not design slides 7 and 8 (or 9 and 10) as visually unrelated — each pair is explicitly two halves of one continuous idea and must share a visual system that makes that obvious.
- Do not add a company logo, generic stock icon set, or decorative illustration unrelated to the actual pipeline/document content.
- Do not default to a generic "tech startup" or "AI product" visual identity — this is an academic engineering defence for a specific, concrete system; ground the design in that.
