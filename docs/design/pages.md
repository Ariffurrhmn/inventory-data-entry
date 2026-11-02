# Presentation Pages — Exact Text

One page = one slide. This is the exact text to put on each slide, nothing more. Full detail and speaker notes live in `presentation_slide_content.md` — this file is the quick-reference version.

---

## Page 1 — Title

Automated Inventory Data Entry through Intelligent Character and Document Structure Recognition

*Subtitle, smaller text underneath: "Turning paper invoices into clean, structured data — automatically."*

Arifur Rahman, Meer Mushfiqur Rahman, Fatema Akter Akhi, Sheikh Ramisha Zubaydah

Supervisor: Md. Mijanur Rahman

Department of Computer Science and Engineering, BUBT — CSE 498A, Summer 2026

---

## Page 2 — Problem Statement

Two-column layout, not a flat bullet list.

**Left column — what happens today:**
A shop owner gets a paper invoice. Different suppliers lay them out differently — no fixed template across the board. Someone reads it, line by line, and retypes it into whatever system the shop uses. Every single day.

**Right column — why nothing solves this:**
Inventory software expects the data to already be typed in — it isn't built to take a photo as input.
Plain OCR reads the text, but has no idea if it's looking at a price, a quantity, or even what kind of document this is.

**Bottom line, standing alone, pulling both sides together:**
The real bottleneck isn't reading the document — it's turning it into something a system can actually use.

**Have ready, don't necessarily put on the slide:** if asked "how do you know this is a real bottleneck and not just an annoyance" — the honest answer at this stage is that this is the motivating problem informing the design, not yet backed by our own measured data; that measurement is part of what the evaluation plan (page 14) will produce. Don't claim a number we don't have.

---

## Page 3 — Motivation

Three points, each with a line underneath explaining *why* it's true — not just the headline.

**1. The manual process is everywhere.**
Even a shop that already bought inventory software is still stuck doing this by hand — the software was never the bottleneck. The data entry was.

**2. The technology is finally ready.**
Two specific things changed recently, not just "AI got better" in general: language model providers started offering a mode that guarantees structured output instead of free-form text, and running these models at the volume a small shop needs became cheap enough to be practical. Both of those are recent — this wasn't a reasonable engineering bet even two or three years ago.

**3. But LLMs can fail silently.**
The model reads "24" as "21," produces a confident-looking number, and nothing about the output looks wrong. The danger isn't that it fails — it's that failure looks identical to success. That's the real design challenge this project takes on. *(We'll show exactly how we catch this in a few slides — hold that thought.)*

---

## Page 4 — Objectives

Four objectives, each with a line underneath explaining why it matters — not just what it is. (Evaluation is folded into objective 4 rather than standing alone — it's how we prove 1 through 3 actually worked, not a separate peer goal.)

**1. Build a recognition pipeline combining OCR with document structure/type recognition.**
Reading text alone isn't the gap — plenty of tools already do that. The real objective is reading the text *and* knowing what kind of document it is at the same time, because the same field means something different on a purchase order than on a delivery note.

**2. Design a schema-constrained extraction step.**
Not "use an LLM to extract fields" — the output is *guaranteed* to match the schema. Structurally impossible to be malformed, not just usually correct.
Worth saying why JSON specifically: most inventory and ERP software already accepts structured data through an API — that's the natural handoff point. Producing clean structured output is what lets this plug into systems that already exist, rather than requiring a new integration built just for us.

**3. Engineer a verification step, and design the service as a stateless, idempotent API.**
Verification: catch errors using the document's own internal math — quantity times price should equal the stated total. Say plainly what this does and doesn't do: it catches numbers that don't add up internally. It won't catch an error where every related number was misread consistently, so the math still checks out despite being wrong. That's a real limit, not an oversight — worth naming before it's asked.
Stateless API: this system owns no inventory data, so a retried or duplicate submission can't corrupt anything downstream.

**4. Evaluate the system on recognition accuracy and extraction accuracy.**
Prove all of the above is measurable and testable — this closes the loop on objectives 1 through 3, once the system is actually built.

---

## Page 5 — Related Work / Gap

Show as a small table, not bullets — rows are the three categories below, columns are the three gap criteria (knows document type / owns no inventory data / auto-verifies its own output). Makes the gap visible at a glance instead of asking the audience to hold three bullets in their head and compare mentally.

| | Knows document type | Owns no inventory data | Auto-verifies output |
|---|---|---|---|
| General cloud document-AI (Textract, Document AI, Azure) | Partial | — | — |
| Purpose-built invoice extraction (Nanonets, Mindee, Veryfi) | Partial | — | Partial (human-reviewed, not automatic) |
| Inventory/ERP platforms (Finale, HandiFox, Apptricity) | — | No (owns the inventory data) | — |
| This project | Yes | Yes | Yes |

**Have ready, don't need to say unprompted:** AWS Textract's "AnalyzeExpense" feature does get close to document-type-aware extraction for a narrow set of expense-document types. The honest distinction: it's tuned for expense/invoice-like documents specifically, not a general purchase-order/receipt/delivery-note/customer-copy taxonomy, and it's a feature bolted onto a general OCR platform rather than the platform's central design goal. If pressed, say that plainly rather than overstating the gap.

---

## Page 6 — System Architecture

*Figure 2 — keep this one intentionally simple (3-4 boxes), since page 7 is where the detail lives. If the two diagrams end up looking too similar side by side, consider presenting them as one build/reveal sequence — this slide as the "zoomed out" first frame, page 7 as the "zoomed in" reveal — rather than two separate static diagrams.*

- Mobile app: capture only. No processing on the device.
- Everything else — OCR, extraction, verification — runs in the cloud.
- Output: a stateless JSON API call, consumed by the shop's existing ERP/inventory system.

**Have ready if asked "what if there's no smartphone, or no internet at the moment of capture?"**
What's actually designed for: a network failure during upload is handled — each capture gets an ID, so retrying the same upload after a dropped connection doesn't create a duplicate. What's not decided yet: fully offline capture with a queued upload for later, or a no-smartphone fallback. Be honest that this wasn't in scope for the design stage rather than implying it's handled — "retry-safe" is not the same claim as "works offline," and the difference matters if asked directly.

---

## Page 7 — Pipeline Detail, Part 1: Capture Through Classification

*Figure 4, first half — modules 1-3 highlighted*

**1. Document Capture**
Take the photo, check it's not blurry or cut off, tag it so it's never processed twice.
Why: a bad photo poisons everything downstream. Catching it here is cheap — catching it three steps later isn't.

**2. Character Recognition (OCR)**
Read the text off the image.
Why: this is the foundation everything else stands on. Get the text wrong here, and no later step can fix it.

**3. Document Structure & Type Recognition**
Figure out what kind of document this is: purchase order, receipt, customer copy, or delivery note.
Why: covered already on page 4 — this is where that objective actually gets built. (Don't re-explain the reasoning here live; a quick "as mentioned" is enough.)

---

## Page 8 — Pipeline Detail, Part 2: Extraction Through Data Model

*Figure 4, second half — modules 4-6 highlighted*

**4. Schema-Constrained Extraction**
Turn the text into structured data, in a fixed format every time.
Why: not just "extract the data" — guarantee the output is never malformed. That guarantee is what makes it safe to hand off automatically.

**5. Digitization API**
The connection point: send a document in, get the structured result back. Safe to retry without creating duplicates.
Why: this is the actual handoff to the real world — where this project's output becomes someone else's input.

**6. Data Model**
The only thing this system remembers: a record of what was submitted and when.
Why: deliberate, not an oversight — the system remembers almost nothing on purpose, because it's not supposed to own the shop's inventory data.

---

## Page 9 — Worked Example (Clean Case)

**Say this line first, before revealing anything on the slide — order matters here:** "This is a hand-built, illustrative example. Nothing is running yet — this shows what the pipeline is designed to produce, once built." Only then move to the invoice and output. Disclosing the caveat after showing a clean, working-looking result risks it landing as a demo of something real.

This is the moment the abstract pipeline becomes something real — but say it *is* an example, not a demo. First of a two-part story; page 10 breaks this same example on purpose.

**Left side — the input:** a photo of a real-looking purchase order. Supplier: ACME Beverage Distributors. Three line items — Coca-Cola, Sprite, Mineral Water — each with a quantity, a unit price, and a line total, plus a grand total at the bottom.

**Right side — the output, in plain terms, not raw JSON:**
- Document type: purchase order, high confidence.
- Three items extracted, each with its quantity, price, and total read correctly.
- Every line's math checks out — quantity times price equals the stated total.
- Nothing flagged. This document goes straight through.

*(Full source invoice + exact JSON in `demo_worked_example.md`.)*

---

## Page 10 — Worked Example (Flagged Case)

The payoff of the two-part story — this is the "trust" moment of the talk. Say that out loud before showing it.

**Left side — the input:** same invoice as page 8, but OCR misreads one number: the quantity "24" gets read as "21."

**Right side — the output, in plain terms, not raw JSON:**
- 21 times the unit price of 15.00 is 315.00 — but the invoice actually states the line total as 360.00. Those don't match.
- That one line gets marked as failed.
- The whole record gets a flag saying it needs a second look.
- The record still goes through. Nothing is blocked, nothing sits in a queue waiting for a person. It's flagged, and whatever system receives it downstream sees that flag.

One line underneath, the core point: the system caught its own mistake automatically, using nothing but the invoice's own arithmetic — no manual review step anywhere in the pipeline.

**Have ready, one sentence, don't need to volunteer it:** this catches numbers that don't add up internally — it won't catch a misread that stays internally consistent (e.g. if OCR also misread the price to match). That limit is already named on page 4; if asked here, a short "yes, that's a known limit, covered in the objectives" is enough — no need to re-explain it in full.

---

## Page 11 — What's Explicitly Out of Scope

- No item-name matching or catalog. "Coke" vs. "Coca-Cola" is left to the consuming ERP.
- No human-in-the-loop confirmation. Verification is fully automatic. *(Why not route flagged records to a person? Two reasons: it reintroduces the exact manual bottleneck this project exists to remove, and it's the downstream ERP's decision to make, not this system's — this system's job ends at producing a verified, flagged-or-not JSON record.)*
- No inventory ownership. No stock, transactions, valuations, or product catalog stored here.
- No on-device processing. Everything but capture runs in the cloud.
- **English-only, in this version.** This is a real, deliberate scope cut, not an oversight — say so directly. A BUBT panel will likely ask "who is this actually for, then, in a Bangla-speaking market?" Have this answer ready, said plainly rather than avoided: reliable OCR and layout recognition for Bangla and handwritten Bangla is a genuinely harder, less mature problem than English recognition — bundling that difficulty into a first version would have put the whole project's timeline at risk. English was chosen to prove the pipeline design works at all; Bangla support is future work, not something ruled out permanently.

---

## Page 12 — Data Model

*Figure 7*

**Nothing is built yet — this is a design decision, not a working database.** Say that clearly before showing the diagram.

**What we're proposing to store — one thing:**
A record of each submission: which shop it came from, when it arrived, whether it's done processing, and where to find the result. Nothing more.

**Why so little, on purpose:**
This isn't a limitation — it's a boundary drawn deliberately at the design stage. The moment this system starts holding stock counts, or a product list, or transaction history, it stops being a simple gateway and starts becoming an inventory system of its own — competing with, not feeding into, whatever software the shop already runs. Keeping it to one record is what makes it safe to plug into any existing system without a fight over who owns the data.

**Say plainly:** we're not planning to track any of this — not because it's hard, but because it's not our job.

**Have ready if asked "doesn't 'whether it's done processing' and 'where to find the result' already imply more state than 'one record' suggests — especially if results need to be fetched later?"**
Fair point, and the honest answer: this is a deliberate v1, not a permanent ceiling. If a future version needs asynchronous processing (see page 16's open decision on synchronous vs. async delivery), the schema can grow to support that without changing the core boundary — it would still be operational bookkeeping about submissions, never the shop's actual inventory data. "Minimal" describes what kind of data we store, not a promise that the schema will never change.

---

## Page 13 — Methodology

*Figure 1*

Five phases, iterative:
1. Requirement analysis & document collection *(currently here, going into this defense)*
2. Data model & API contract design
3. Recognition pipeline
4. Verification & digitization API core
5. Evaluation & benchmarking

Evaluation results feed back into the API contract and extraction design.

**The one dependency worth naming out loud, not just implying:** phase 1's document collection is what phase 3's document-type classifier depends on — the stage-two trained classifier described on page 14 can't start until real documents are in hand. That makes phase 1 the phase most likely to set the pace for everything after it, since it depends on shops actually agreeing to share documents, not just on our own work rate.

**Say plainly where things stand:** this is genuinely where we are right now — not a hypothetical five-phase plan, but the actual next step in front of us.

---

## Page 14 — How the System Learns to Recognize Different Slip Types

The question a panel will likely ask: how does it actually learn to tell a purchase order from a receipt from a handwritten delivery note?

**Two-stage answer:**

**Stage one — no training data needed, starts working immediately.**
Ask a language model to look at the recognized text and rough layout, and guess what kind of document it is. No training required. Works from day one, but less accurate and costs more to run per document, since it's asking the model to reason it out fresh each time.

**Stage two — a purpose-built classifier, trained on real examples.**
Once we've collected real documents from real shops, we train a dedicated model — one built specifically to understand position on the page, not just the words. It reads text *and* where that text sits on the page, so it learns things like: totals sit at the bottom, headers sit at the top, a line-item table has a particular shape. This gets fine-tuned once we have real data, and gets checked against the first-stage guesser to see if it's actually better.

**Why two stages, not just one:**
We don't want data collection to block the rest of the build. Stage one lets every other piece of the pipeline get built and tested right away, while real documents are still being gathered in the background. Stage two takes over once there's real data to learn from.

**Where the real data comes from:**
Small shops, approached directly, asked to share documents they already have — with informed consent, told in advance how the documents will be used and how long they'll be kept, and free to withdraw them later. Business-sensitive details — supplier pricing, customer information — are handled carefully: identifying details get anonymized in anything published, and access is limited to the project team. We're aiming for at least 30 examples of each document type — purchase orders, receipts, delivery notes, customer copies — and deliberately not forcing an even mix of printed, handwritten, and thermal-printed. If delivery notes are usually handwritten in real life, our examples should be too — otherwise our accuracy numbers would lie about how well this actually works in the real world.

**Have ready if pushed on "30 per class is thin for training a model":**
That's a fair challenge on its own — but this isn't training from scratch. Stage two fine-tunes an already-pretrained layout-aware model (the LayoutLM family, which already understands general document structure from large-scale pretraining) rather than teaching a blank model everything from these 30 examples alone. Fine-tuning a pretrained model on a smaller, task-specific set is standard practice and far more defensible than training from zero. Worth also framing 30 as a floor for a first pilot, with more collection ongoing, not a hard ceiling. (One honest caveat to hold in reserve, not volunteer: the specific LayoutLM citation in the written report is flagged as not yet independently verified against the source paper — if asked to cite it precisely, say that verification is still pending rather than overstating certainty.)

---

## Page 15 — Evaluation Plan

No numbers exist yet — this is the plan for how we'll prove the system works, once built. Say that plainly if asked.

**Character recognition — how much of the text did we read correctly?**
Measured by comparing what OCR read against what the document actually says, word by word and character by character.

**Document type & structure — did it correctly tell what kind of document this is?**
Not just "did it guess right overall" — a full breakdown of exactly which document types get confused with which others, so we know precisely where it struggles, not just an average score.

**Schema-constrained extraction — did the output actually make sense?**
Two checks: did every output come out in the correct structured format, and separately, were the actual values inside it correct.

**Verification — this is the headline test.**
How often does the arithmetic check catch a real mistake, versus how often does a wrong value slip through undetected? This is measured across different sensitivity settings, not just one fixed threshold.

**Digitization API — does it hold up under real conditions?**
How fast is it, and — critically — if the same document gets submitted twice by accident, does it correctly avoid processing it twice?

**The one claim we most want to prove:** checking a document's own math and scoring confidence catches meaningfully more errors than not checking at all. Everything else on this slide supports that one claim.

**If pressed "what accuracy would you consider a pass?"** — don't say "we haven't decided," that lands worse live than having a reference point. The honest, grounded answer: the classifier architecture we're building on (LayoutLM-family) reports 90–95% document classification accuracy in its own published benchmarks. That's the literature's number, on cleaner benchmark data, not a promise about our result — real small-business documents are messier. But it's a reasonable floor to be targeting and measuring against, not an arbitrary guess.

**Build note for whoever makes the actual slide:** six sub-evaluations is a lot to present at defense pace. Bold just the metric name per line on the physical slide, keep the fuller explanation in speaker notes only — the slide itself should read as a scannable checklist, not six paragraphs read aloud.

---

## Page 16 — Open Decisions

Present these as resolved calls, not gaps — "we've made a decision on each, here's why."

**1. Which OCR service — cost-optimized among comparable-accuracy options.**
Several providers can do this job at a similar level. Once accuracy is roughly equivalent above a threshold, the deciding factor becomes cost — that's a deliberate optimization, not a shortcut on rigor.

**2. Which language model — cost-optimized among the top-ten providers.**
Same logic — narrow to proven, reliable options first, then optimize for cost rather than chasing marginal quality gains between similar-tier models.

**3. How we enforce the output format — the provider's built-in JSON mode.**
Most providers already have a setting that guarantees valid structured output. Using that instead of building a separate enforcement tool is simpler and one less thing to maintain.

**4. How we score confidence — try the free method first.**
Some providers can tell you how confident the model was in a specific answer, at no extra cost. Where that's available, use it. Where it isn't, fall back to asking the model the same question multiple times and checking if the answers agree — more reliable, but costs more since it means multiple calls per document.

**5. How the document-type classifier learns — the two-stage plan already covered.**
Guessing with no training data first, a properly trained model once real documents are collected. Already explained in detail on page 13.

**6. How results get delivered — synchronous by default.**
Meaning: you send a document, you wait, you get the answer back in that same request — no separate step to come back and check later. Simpler to build and use. We'd revisit this only if processing turns out to take too long to make people wait comfortably.

**One line to have ready if pushed on any of these:** none of these are guesses — each is a deliberate call based on the tradeoff, made explicit rather than left open.

**Have ready if pushed on item 6 — "how slow is too slow, do you actually know your latency?"**
Be honest: no measured number exists yet, since nothing is built. But have a ballpark in mind going in — a realistic total for OCR plus an LLM call plus verification lands somewhere in the single-digit seconds per document, which is tolerable for someone standing there waiting after taking a photo, but would need to be watched carefully if it crept higher. If it turns out too slow in practice, that's precisely the trigger for revisiting synchronous delivery — not a vague "we'll see."

---

## Page 17 — Closing / Q&A

**One sentence that ties everything together, said plainly before the recap:**
This system reads a document, checks its own work, and hands off clean data — nothing more, nothing held back, nothing hidden from the receiving system.

**Recap — four contributions:**
- A recognition pipeline that reads text and knows what kind of document it's looking at.
- Extraction that's guaranteed to come out structured, backed by a verification step that catches its own mistakes.
- A stateless, idempotent API — safe to plug into any system without owning anyone else's data.
- A plan for proving all of the above actually works, once built.

**Where this stands:**
This is a design-stage submission. Implementation and real results come next semester.

**Name the biggest open risk before anyone asks:**
The part most likely to slow us down isn't the pipeline design — it's collecting enough real documents, from real shops, to properly train the stage-two document-type classifier. That's the piece most outside our direct control.

Thank you. Questions?
