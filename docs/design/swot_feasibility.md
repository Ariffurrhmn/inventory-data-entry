# SWOT Analysis & Feasibility Study

**Project:** Automated Inventory Data Entry through Intelligent Character and Document Structure Recognition
**Stage:** Design-stage submission (CSE 498A). No implementation exists yet — this analysis is written against the proposed system described in the Chapter 1–3 report draft and the pre-defence deck, not a built product.

---

## 1. SWOT Analysis

### Strengths

- **Clear, narrow scope with a real handoff point.** The system commits to being a stateless, idempotent digitization *gateway* — not an inventory system — and outputs to a documented JSON API. This avoids the much harder problem of owning inventory state, catalog reconciliation, or replacing a shop's existing software, which keeps the engineering problem tractable within a two-semester capstone timeline.
- **Verification story is concrete and testable, not hand-wavy.** Arithmetic self-validation (`qty × unit_price == line_total`, line totals vs. grand total) is a zero-cost, model-free check that directly addresses the project's own stated central risk — silent LLM hallucination. It gives the team a real, measurable claim for Chapter 4 ("X% of injected errors caught") rather than a vague reliability promise.
- **Built entirely on mature, composable components.** OCR, document classification (LayoutLM-style), constrained/schema-guaranteed decoding, and hallucination-detection techniques (SelfCheckGPT, semantic entropy) are all established, commercially available, or published techniques. The contribution is composition and the trust layer around them, not a novel model — this substantially de-risks the technical build.
- **Two-stage document classifier decouples the schedule's riskiest dependency from the rest of the build.** Few-shot LLM classification works from day one with zero training data, so pipeline, API, and verification work can proceed in parallel while real documents are being collected for the fine-tuned classifier — the team isn't blocked waiting on shop cooperation.
- **Honest, well-scoped literature and competitive positioning.** Chapter 2's gap analysis against Textract/Document AI/Azure, Nanonets/Mindee/Veryfi, and Finale/HandiFox/Apptricity is specific rather than a blanket "nothing else exists" claim — it names exactly which requirement each competitor category fails (mostly: none treats document-type classification as a first-class, verified output in a stateless gateway).

### Weaknesses

- **Corpus collection depends entirely on external cooperation the team doesn't control.** The 30-per-type real-document target requires small shops to hand over commercially sensitive paperwork. The report itself flags this as the pacing risk for the whole project (Slide 13/17) — if shops are slow or reluctant, the fine-tuned classifier, the real evaluation numbers, and Chapter 4 all stall behind it.
- **Arithmetic verification has a known, named blind spot.** It cannot catch a *consistent* misread — e.g., OCR reads both quantity and unit price wrong in a way that still multiplies out correctly. The team has already acknowledged this (report §1.3, deck slide 4), which is good practice, but it means the headline "catches its own mistakes" claim is narrower than it may sound to a panel on first hearing.
- **Confidence-signal source (Decision 4) is the most load-bearing open decision and is still unresolved.** Token log-probabilities are cheap but often unavailable via commercial LLM APIs; sampled-consistency (SelfCheckGPT-style) works everywhere but multiplies inference cost per document. This decision gates the entire confidence-scoring half of verification and is deferred to "first implementation cycle" — a real schedule risk if it turns out to need significant tuning.
- **English-only scope, from a Bangladesh-based team, for a Bangladesh small-shop use case.** The report already flags this as the scope cut most likely to draw a pointed panel question. It's a defensible engineering decision (Bangla OCR/NLP tooling is materially less mature — see the project's own literature folder on "BanglaBengali NLP"), but it does narrow real-world deployability for the exact market the motivation section describes.
- **No real accuracy numbers exist yet.** Every quantitative claim in the current materials (worked examples, schema, confidence thresholds) is illustrative/hand-built. This is appropriate for a design-stage submission, but it means feasibility below is necessarily an estimate, not a measurement.

### Opportunities

- **The underlying technique generalizes beyond inventory.** The report explicitly notes (§1.5) that "document structure recognition → schema-constrained extraction → arithmetic/consistency self-validation" isn't inventory-specific — it could extend to expense reports, tax documents, logistics paperwork, or any domain where a language model extracts structured records from heterogeneous source documents. This gives the project a plausible second life beyond the capstone.
- **Small-business digitization is a large and underserved local market.** Bangladesh (and similar markets) have a large base of small/medium retail businesses still on paper-based record-keeping, per the project's own problem statement — a working version of this system, even English-only initially, addresses a real and currently unmet local need, with room to extend to Bangla in a future phase.
- **Two-stage classifier design creates a natural research/publication opportunity.** Comparing few-shot LLM classification against a fine-tuned layout-aware model on a purpose-collected, vendor-heterogeneous small-shop document corpus is a concrete empirical contribution (as the report already claims in §2.2.3) that could stand alone as a paper or extended technical report.
- **Constrained-decoding and hallucination-mitigation tooling is actively improving.** Since this is an area of fast-moving commercial and research progress (better JSON-mode support, cheaper log-prob access, better calibration techniques), the system stands to get more reliable and cheaper to run over time without the team needing to re-architect it — the design deliberately treats these as swappable, provider-agnostic decisions (Table 3.3).

### Threats

- **Commercial platforms could add the missing capability.** The gap analysis (Table 2.2) is accurate today, but general cloud document-AI platforms (Textract, Document AI, Azure) are large, well-resourced products; if any of them adds first-class document-type classification with arithmetic verification, the specific gap this project occupies narrows. This is a competitive risk for any post-capstone commercialization ambition, though it doesn't invalidate the capstone's academic contribution.
- **LLM API pricing, availability, or policy changes are outside the team's control.** The system's cost model and Decision 2 (LLM provider) both assume continued affordable access to commercial LLM APIs with JSON-mode/schema support; a pricing increase or provider deprecation of a needed feature would force a rework mid-project.
- **Data-sensitivity concerns could suppress shop participation.** Supplier invoices reveal pricing, volumes, and trading relationships — commercially sensitive information. Shops may be more reluctant to share real documents than anticipated even with informed consent and anonymization commitments in place, compounding the corpus-collection risk above.
- **Panel skepticism about the "no human-in-the-loop" claim.** Purpose-built commercial competitors (Nanonets, Mindee, Veryfi) all keep a human-review step for low-confidence fields; this project's fully automatic verification is a deliberate differentiator, but it's also the single easiest point for an academic panel to probe ("what happens when both the arithmetic check and confidence score are wrong at once?"). Worth having a rehearsed answer beyond what's already noted in `plan.md`.

---

## 2. Feasibility Study

### 2.1 Technical Feasibility — **Feasible, moderate-to-high confidence**

Every individual component the pipeline depends on already exists and is either commercially available or published with reference implementations:

| Capability needed | Maturity |
|---|---|
| OCR on printed/handwritten/thermal text | High — TrOCR and commercial cloud OCR (Textract/Document AI/Azure) all demonstrated on this exact document class |
| Document type/structure classification | Medium-high — LayoutLM family reports 90–95% on document image classification; not yet validated on this project's specific vendor-heterogeneous documents |
| Schema-guaranteed JSON output | High — provider-native JSON mode and constrained-decoding libraries (Outlines/XGrammar) are production-ready |
| Arithmetic self-validation | High — this is deterministic logic the team writes itself; no external dependency or research risk |
| Confidence/hallucination detection | Medium — SelfCheckGPT and semantic-entropy techniques are published and reproducible, but tuning them for *structured field* confidence (rather than open-ended QA, their original evaluation setting) is genuinely unexplored territory per the report's own gap statement |
| Idempotent stateless API design | High — standard, well-understood pattern (Helland's idempotency principles); low technical risk |

**Verdict:** the highest-risk technical unknown is not any single component but the **composition** — specifically, how well document-type classification errors propagate into extraction errors, and whether confidence scoring (Decision 4) can be made reliable and affordable simultaneously. Neither is a blocking risk; both are exactly the kind of open question an iterative, evaluation-driven methodology (already the chosen approach) is designed to resolve.

### 2.2 Operational Feasibility — **Feasible, contingent on corpus collection**

- The mobile-capture-to-cloud-to-API architecture is already proven viable at the operational level — Finale, HandiFox, and Apptricity run this exact integration pattern in production today (report §2.2.2c). Operationally, businesses adopting this kind of gateway is not a novel ask.
- The single largest operational dependency is **document collection from real shops**, which the team does not control and which the report already names as the pacing risk for the whole project. Recommended mitigation (already partially planned): start outreach to candidate shops immediately and in parallel with pipeline development, not after; the two-stage classifier already ensures this doesn't block other work streams.
- Team composition (4 members) is adequate for the module breakdown (capture, OCR/classification, extraction/verification, API/data model) but leaves little slack — annotation (with double-annotation for inter-annotator agreement) is an additional, easy-to-underestimate time cost once documents start arriving.

### 2.3 Economic Feasibility — **Feasible at capstone scale; cost-sensitive at production scale**

- At capstone/demo scale (dozens to low hundreds of documents for evaluation), commercial OCR and LLM API costs are low — well within typical student-project budgets, especially given the report's own stated preference for cost-optimized providers (Decisions 1–2, Table 3.3).
- The confidence-scoring method chosen under Decision 4 has a direct cost implication: log-probability-based confidence is essentially free, while sampled-consistency approaches (SelfCheckGPT-style) require multiple LLM calls per document, multiplying per-document cost. This decision should be evaluated on cost as well as accuracy, not accuracy alone.
- At real deployment scale (a shop processing dozens of invoices daily), per-document cloud OCR + LLM cost becomes the dominant recurring expense and the main lever for commercial viability — this is out of scope for the capstone itself but worth flagging as the key follow-on question if the project continues past CSE 498B.

### 2.4 Schedule Feasibility — **Feasible for CSE 498A/498B split, with one named critical path**

- The report's own five-phase methodology (requirement analysis & collection → data model/API design → recognition pipeline → verification/API core → evaluation) is realistic for a two-semester capstone, and the iterative/feedback-loop structure (evaluation results feeding back into schema and extraction design) is appropriate given how many decisions (schema shape, confidence threshold, taxonomy) genuinely can't be finalized before real documents are seen.
- **Critical path:** document collection (Phase 1) gates the fine-tuned classifier (part of Phase 3) and the real evaluation numbers (Phase 5). Everything else — API design, schema-constrained extraction, arithmetic verification, idempotency — can and should proceed in parallel using the few-shot classifier and hand-built/synthetic examples, exactly as currently planned.
- Recommended schedule safeguard: set an early go/no-go checkpoint on corpus collection (e.g., "X documents per type by mid-498A") so that if shop cooperation is slower than expected, the team can lean more heavily on public benchmarks (SROIE, CORD, FUNSD) and synthetic data to keep evaluation on schedule rather than discovering the shortfall late in 498B.

### 2.5 Overall Feasibility Verdict

**The project is feasible as scoped.** Its technical components are individually mature and its architectural boundaries (capture-only client, no owned inventory state, stateless idempotent API) are deliberately chosen to keep the engineering problem bounded. The project's success is not gated by any single unsolved research problem — it's gated by **execution discipline on the one dependency outside the team's direct control (real document collection)** and by **resolving the confidence-signal decision (Decision 4) early enough** that the verification-accuracy evaluation in Chapter 4 isn't rushed. Both risks are already correctly identified in the team's own materials; this study's main contribution is making them explicit as feasibility-gating items rather than background risks.

---

*This analysis was written from the existing Chapter 1–3 report draft, the pre-defence deck content spec, and the worked examples in this `docs/design/` folder. No new claims, numbers, or features are introduced beyond what those documents already establish or directly imply.*
