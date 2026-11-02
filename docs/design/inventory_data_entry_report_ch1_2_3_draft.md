# Automated Inventory Data Entry through Intelligent Character and Document Structure Recognition — Chapters 1–3

**Note:** Document-structure-recognition citations (LayoutLM family, Donut) in Section 2.1.1 are currently sourced from web summaries rather than read directly from the papers — verify against source before finalizing references.

---

## Abstract

Small shops and fulfilment centres overwhelmingly keep their purchase and sale records on paper — printed invoices, thermal receipts, and handwritten chits in inconsistent, vendor-specific formats. Because manual data entry into an inventory or ERP system is slow and tedious, this digitization step is rarely done consistently, leaving businesses without a reliable, structured view of their transactions. This report presents the proposed system, a mobile-to-cloud document digitization gateway that converts heterogeneous supplier invoices, receipts, and inventory documents into a standardized JSON output, served via an API that authorized inventory and ERP systems can call to automate what is currently manual data entry. The system's primary technical objective is character recognition and document structure recognition — reading the text of a scanned document and identifying its structural role (e.g., a purchase order, a customer copy, a line-item table) — with a cloud-hosted language model performing the schema-constrained extraction of that content into structured line items. Recognizing that language models can produce incorrect or invented values, the system engineers reliability around the model through arithmetic self-validation and confidence scoring before any output is finalized; reconciling item names across suppliers is left to the consuming inventory/ERP system. This report covers the introduction, background study, and research methodology of the project: Chapter 1 states the problem, objectives, motivation, significance, contributions, and complex engineering analysis; Chapter 2 reviews the supporting literature across four thematic areas and analyzes the problem against existing commercial systems, establishing the gap the project addresses; and Chapter 3 presents the proposed research methodology, covering the system architecture, the design of each module, the corpus collection plan, and the evaluation framework.

---

## Chapter 1: Introduction

Inventory record-keeping for small and medium retail businesses depends heavily on paper documents. Every purchase from a supplier produces an invoice, receipt, or delivery slip, and every one of these documents must currently be read by a person and typed into whatever inventory or accounting system the business uses. This document-to-record step is slow, repetitive, and error-prone, and it is the actual bottleneck standing between a business and an up-to-date, structured view of its stock and costs. Optical character recognition (OCR) and large language models (LLMs) have both matured to the point where automated understanding of such documents is now technically practical; however, using an LLM to extract structured fields from a heterogeneous document introduces a reliability question, since language models can produce incorrect or invented values with no indication that anything has gone wrong. This project addresses the digitization bottleneck directly. It is a mobile-to-cloud document digitization gateway: a mobile application captures a document (photograph or scan), a cloud service performs character recognition and document structure recognition, an LLM extracts the document's content into a schema-constrained structured record, and the result is served as a standardized JSON output via an API that any authorized inventory or ERP system can call. This chapter states the problem (Section 1.1) and its background (Section 1.2), sets out the research objectives (Section 1.3), and presents the motivations (Section 1.4), significance (Section 1.5), and contributions (Section 1.6) of the work, followed by a complex engineering analysis (Section 1.7) and the organization of the report (Section 1.8).

### 1.1 Problem Statement

Small shops and fulfilment centres receive their purchase and sale records as unstructured documents — printed invoices, thermal-printer receipts, and handwritten chits — issued by many different suppliers with no common layout or standard. When one of these documents arrives at an inventory management system, a person currently has to read it and manually enter its contents; this manual step is slow and tedious, so businesses frequently fall behind on keeping their records current, or skip structured recording altogether. Existing inventory management systems do not solve this because they assume the data entry has already happened by the time information reaches them — they consume clean, structured input, not a photograph of a paper slip. Off-the-shelf OCR alone is not sufficient either: it produces raw text without structure, so a downstream system still cannot tell which text is a line-item description, which is a quantity, and which document type it is looking at in the first place (a purchase order, a delivery note, a customer copy, and so on). The engineering problem this project addresses is recognizing the characters and document structure of heterogeneous, unstructured supplier documents so that their content and document type can be identified automatically. The output of this pipeline is a standardized JSON representation of the document's content, served through an API that an authorized ERP or inventory management system can call to eliminate the manual data-entry step; reconciling item names that differ across suppliers (for example, "Coca-Cola" versus "Coke") is left to the consuming ERP or inventory system.

### 1.2 Problem Background

A large share of small and medium retail businesses still process supplier documents by hand: an employee reads each invoice or receipt and types its contents into whatever system the business uses to track inventory or accounts. This remains the case even as OCR and language-model technology have both become capable enough, in principle, to automate the reading step. Two factors make this harder than it may first appear. First, the input documents are heterogeneous: they arrive printed, handwritten, or thermal-printed, in layouts that differ from supplier to supplier, and a system must also determine what kind of document it is looking at — a purchase order is not structured the same way as a customer copy or a delivery note — before it can correctly interpret the text within it. Second, even once a document's text and structure have been read, converting it into a clean, schema-valid structured record requires an LLM extraction step, and language models are known to occasionally produce incorrect output with no visible indication that anything is wrong, so an extracted value cannot simply be trusted without some verification step. Running this kind of processing reliably at usable speed and accuracy currently favors cloud-hosted models over on-device inference — attempting to run a capable language model directly on a mobile device introduces reliability, performance, and maintenance problems that a cloud-hosted approach avoids; the mobile application's role is therefore to capture the document, while all recognition and extraction processing happens server-side.

No existing category of software addresses this combination well. Commercial inventory and accounting software assumes that structured, typed input already exists by the time it reaches the system. General-purpose OCR services can read text from a document but do not, on their own, resolve document structure/type the way a specific inventory workflow needs. Purpose-built invoice-extraction platforms (surveyed in Chapter 2) come closest, but none of the reviewed platforms treats document structure/type recognition as a first-class capability integrated directly into a capture-to-API pipeline the way this project proposes. The gap — automated character and document-structure recognition of heterogeneous supplier documents, delivered as a JSON API a business's existing inventory system can consume — is the problem this project takes up. A detailed analysis of this gap against existing systems is presented in Chapter 2.

### 1.3 Research Objectives

The primary objective is to develop a mobile-to-cloud document digitization gateway that performs character recognition and document structure recognition on supplier invoices, receipts, and inventory documents, and outputs a standardized JSON representation via an API for consumption by authorized inventory and ERP systems. The supporting objectives are:

- To build a document recognition pipeline that combines character recognition (OCR) with document structure/type recognition, so that the system can both read the text of a heterogeneous set of supplier documents (printed and handwritten, English-language) and correctly identify what kind of document it is looking at (e.g., purchase order, customer copy, delivery note, receipt).
- To design a schema-constrained extraction component in which a cloud-hosted language model converts recognized document content into structured line-item records conforming to a fixed JSON schema.
- To engineer a verification step around the language model's extraction output — cross-checking extracted numeric fields against the document's own arithmetic and flagging low-confidence records for review — so that no unverified value is silently finalized.
- To design the digitization service as a stateless, idempotent API: each submission (e.g., a mobile-app-scanned document) produces a JSON output without the system itself owning or persisting inventory state, while ensuring a retried or duplicate submission cannot produce duplicate or conflicting output to the downstream ERP/inventory system.
- To evaluate the system on character/structure recognition accuracy and extraction accuracy, including the rate at which arithmetic self-validation catches extraction errors.

### 1.4 Motivations

The motivation for this work arises from three converging observations.

**A widespread, unautomated manual process.** Businesses that receive paper or image-based supplier documents overwhelmingly still enter their contents by hand into whatever inventory or accounting system they use. This is true even where the business already uses digital inventory software — the software assumes structured input has already been produced by a person. Removing that manual step, by having a mobile app capture the document and a cloud service parse it directly into structured output, attacks the actual bottleneck rather than adding another manual-entry destination.

**A newly practical technical opportunity, deliberately kept simple.** Cloud-hosted OCR and language models are now mature and widely available as commercial APIs (surveyed in Chapter 2), removing the need to solve document understanding from first principles. The engineering opportunity is in composing character recognition, document structure recognition, and schema-constrained LLM extraction into a single reliable pipeline — not in re-deriving any of those component technologies, and not in trying to fit a capable model onto a phone, which the supervisor's guidance specifically ruled out as unnecessarily difficult for this project's scope.

**The reliability gap in language models.** Language models used for extraction can produce an incorrect value without any visible sign that something is wrong. This is the central design challenge for the extraction component: an unverified value cannot be trusted as-is, so the system cross-checks extracted numeric fields against the document's own arithmetic and flags low-confidence records rather than finalizing them silently. The literature on hallucination detection, self-verification, and confidence calibration (Section 2.1.3) informs how this project designs that verification step.

### 1.5 Significance of the Research

The significance of this work is twofold.

**Practical significance.** For a small or medium business, the system removes the manual data-entry step between receiving a supplier document and having its contents available in a structured, usable form — without requiring the business to replace its existing inventory or ERP system, since the system's output is delivered as a JSON API those systems can simply call.

**Technical significance.** The project demonstrates an architectural pattern for building automation around an unreliable language-model component: document structure/character recognition supplies structured input to a schema-constrained extraction step, and arithmetic self-validation and confidence scoring catch extraction errors before output is finalized, without requiring a human in the loop for every submission. This pattern is not specific to inventory documents and could generalize to any setting where a language model extracts structured records from heterogeneous source documents.

### 1.6 Research Contributions

The contributions of this project are as follows:

1. **A character and document structure recognition pipeline** for heterogeneous, English-language supplier documents (printed and handwritten), including recognition of document type (e.g., purchase order, customer copy, delivery note, receipt) as a first-class output, not just raw text.
2. **A schema-constrained extraction and verification layer**, in which an LLM converts recognized document content into structured line items conforming to a fixed JSON schema, with arithmetic self-validation and confidence scoring flagging low-confidence records rather than silently finalizing them.
3. **A stateless, idempotent digitization API design**, in which the system does not own persistent inventory state but guarantees that a retried or duplicate document submission cannot result in duplicate or conflicting JSON output being delivered to a downstream ERP/inventory system.
4. **An evaluation methodology** for such a system, covering character/structure recognition accuracy and extraction accuracy, including the rate at which arithmetic self-validation catches extraction errors.

### 1.7 Complex Engineering Analysis

This project is mapped to the Washington Accord Knowledge Profile (WK), Complex Engineering Problem (WP), and Complex Engineering Activity (EA) attributes. The knowledge profile is engaged as follows: evaluation metrics and confidence scoring apply mathematics and statistics (WK2); mobile-to-cloud system architecture, API design, and database design form the engineering fundamentals (WK3); NLP, language models, OCR, and document structure recognition constitute forefront specialist knowledge (WK4); the API contract, the document-type taxonomy, and the extraction and verification pipeline demand deliberate engineering design (WK5); cloud deployment practices, version control, and systematic testing apply current engineering practice (WK6); data handling for business records and professional responsibility for output correctness engage the engineer's role in society (WK7); and the project builds directly on the research literature in OCR, document understanding, structured LLM output, and hallucination mitigation (WK8).

#### 1.7.1 Complex Engineering Problems

Table 1.1 maps the project to the complex engineering problem attributes.

| Attribute | How the project satisfies it |
|---|---|
| WP1: Depth of knowledge | Requires in-depth ML/NLP knowledge (OCR, document structure recognition) plus systems and API design, with sustained engagement with the research literature. |
| WP2: Conflicting requirements | Extraction automation vs. correctness; keeping the mobile client lightweight vs. giving the cloud service enough context to resolve document structure; usability for non-technical staff vs. system sophistication. |
| WP3: Depth of analysis | No off-the-shelf platform combines document-structure recognition with schema-constrained extraction tuned to heterogeneous, vendor-specific supplier documents; the recognition, verification, and evaluation methods must be designed, none having a closed-form answer. |
| WP4: Familiarity of issues | Reliable document-type recognition for small-business inventory documents is not a well-established, off-the-shelf combination in industry or research. |
| WP5: Applicable codes | Handling supplier/business documents engages data-handling and access-control expectations for the API (authorized-consumer access to the JSON output) and for any interim storage of submitted documents. |
| WP6: Stakeholder involvement | Shop/business staff submitting documents and the downstream ERP/inventory systems consuming the API form a stakeholder set with differing needs around speed, accuracy, and integration effort. |
| WP7: Interdependence | Character recognition, document structure recognition, and schema-constrained extraction are tightly coupled — a structure-recognition error can misroute how downstream fields are extracted — so the sub-problems must be analyzed and tested jointly. |

#### 1.7.2 Complex Engineering Activities

Table 1.2 maps the project to the complex engineering activity attributes.

| Attribute | How the project satisfies it |
|---|---|
| EA1: Range of resources | Cloud OCR/document-AI services, language models, mobile app development tooling, and API infrastructure. |
| EA2: Level of interactions | Resolving interactions between document-structure recognition accuracy, extraction reliability, and the design of the verification and confidence-scoring layer. |
| EA3: Innovation | Creative composition of existing recognition and language-model technologies into a schema-constrained, arithmetic-verified document-capture-to-API pipeline — a combination not found as a first-class feature in the existing systems surveyed in Chapter 2. |
| EA4: Consequences to society | Lowers the data-entry burden for small and medium businesses, allowing existing inventory/ERP tooling to be automated without requiring a full software replacement. |
| EA5: Familiarity | Extends beyond prior coursework by applying principles-based approaches — system design under model uncertainty, API contract design, and evaluation methodology — to an open-ended, industry-relevant problem. |

### 1.8 Project Organization

The remainder of this report is organized as follows. Chapter 2 presents the background study: a literature review spanning four thematic areas — character and document structure recognition, schema-constrained language-model output, hallucination mitigation and confidence calibration, and document-gateway API and idempotency design — followed by a problem analysis that decomposes the technical challenges and positions the project against existing commercial systems. Chapter 3 presents the research methodology: the proposed framework, the dataset and software project requirements, the algorithm and model analysis underlying each design choice, and an explanation of each pipeline module. Chapter 4 will cover implementation and result analysis, including the evaluation metrics and performance measurements not yet available at this design stage. Chapter 5 will discuss standards, constraints, and milestones, including the project timeline. Chapter 6 will conclude the report with limitations and directions for future work.

### Summary

This chapter has stated the engineering problem the project addresses — recognizing the characters and structure of heterogeneous supplier documents and extracting their content into a schema-valid structured record a human can trust — and situated it within the broader difficulty of automating small-business data entry. It set out the primary and supporting research objectives, the motivations arising from the scale of the manual-entry problem and the newly practical technical opportunity to address it, and the practical and technical significance of the work. It listed four concrete contributions, from the recognition pipeline itself to the schema-constrained extraction and verification layer and the stateless, idempotent API design, and mapped the project against the Complex Engineering Problem and Complex Engineering Activity attributes required of a capstone project at this level. The chapters that follow substantiate this problem statement: Chapter 2 reviews the supporting literature and existing commercial systems, and Chapter 3 presents the research methodology by which the system will be designed and built.

---

## Chapter 2: Background Study

This chapter establishes the academic and practical foundations of the project. Section 2.1 reviews the research literature the system design draws on, organized into four thematic areas corresponding to the system's pipeline stages: character and document structure recognition, schema-constrained language-model extraction, hallucination mitigation and confidence calibration, and API/idempotency design for a stateless service. Each subsection closes by identifying the gap that remains between the surveyed work and the requirements of this project. Section 2.2 then analyzes the problem itself: it decomposes the technical challenges, examines why existing commercial systems do not solve them, and consolidates the resulting research gap that the remainder of this report addresses.

### 2.1 Literature Review

#### 2.1.1 Character and Document Structure Recognition

Recognizing a document's text and its structural role is the entry point of the pipeline. Li et al. [1] introduced TrOCR, an end-to-end, convolution-free OCR architecture pairing a pre-trained image Transformer encoder with a pre-trained text Transformer decoder, achieving state-of-the-art results on printed receipts, handwritten text, and scene text without hand-built pre- or post-processing; because the project is now English-only, TrOCR's demonstrated results (which are themselves on English/Latin-script benchmarks) are directly applicable rather than merely architecturally suggestive, and its receipt benchmark covers exactly the printed-document class this project targets. Beyond reading text, the pipeline must also recognize document structure and type — distinguishing a purchase order from a customer copy or a line-item table, for instance. *[Note: the following two entries are drawn from web-sourced summaries and should be verified directly against the papers before finalizing.]* The LayoutLM family of models [2] extends a BERT-style architecture with two-dimensional position embeddings derived from OCR bounding-box coordinates, and later versions add visual features directly, allowing the model to learn that spatially co-located text is often semantically related (e.g., a price sitting next to its line-item description); reported results include document image classification (distinguishing invoice, receipt, purchase order, and other document types) at 90–95% accuracy. Kim et al. [3] proposed Donut, an OCR-free document understanding Transformer that reads a document image end-to-end without a separate text-recognition step, avoiding the error-propagation risk of a two-stage OCR-then-understanding pipeline. Gap: TrOCR and similar general OCR architectures are demonstrated on relatively clean, single-format benchmarks and do not themselves address document-type/structure classification; the LayoutLM and Donut lines of work address structure and type recognition but are not evaluated specifically on the heterogeneous, vendor-specific invoice and receipt layouts this project targets — motivating this project's own evaluation of document structure recognition on real supplier documents, rather than relying on benchmark results alone.

#### 2.1.2 Schema-Constrained Structured Output from Language Models

Converting recognized document content into the standardized JSON output requires the language model's output to conform to a rigid schema. Willard and Louf [4] reformulated guided generation as transitions over a finite-state machine, precomputing an index over the model's vocabulary so invalid tokens can be masked with O(1) average overhead per step; this is the foundational algorithm behind practical constrained-decoding libraries and extends to context-free grammars via pushdown automata. Geng et al. [5] demonstrated that grammar-constrained decoding lets frozen, few-shot LLMs rival fine-tuned task-specific models on structured NLP tasks. Geng et al. [6] contributed JSONSchemaBench, a benchmark of roughly ten thousand real-world JSON schemas across six constrained-decoding frameworks, documenting efficiency and schema-coverage gaps between engines and measurable accuracy gains from constraining, directly relevant to selecting a cloud-side decoding engine for the system's JSON API output. As a counterpoint, Tam et al. [7] found that strict format restriction can degrade reasoning performance relative to freer generation, with the degradation attributable to reasoning itself rather than parsing failures — a caution against relying on schema constraints alone to guarantee correct extraction. Gap: constrained decoding guarantees the JSON output is syntactically valid, not that a given extracted value is correct — a schema-valid output can still contain an incorrect field value — motivating this project's separate arithmetic-verification layer.

#### 2.1.3 Hallucination Mitigation, Self-Verification, and Confidence Calibration

The verification layer around the language model's extraction output draws on three strands of reliability research. On detecting unreliable output, Manakul et al. [8] proposed SelfCheckGPT, which samples multiple stochastic generations and measures their mutual consistency to detect hallucination without access to model internals or external databases — directly applicable to a cloud-API-based language model, where internal token probabilities are often unavailable. Farquhar et al. [9] introduced semantic entropy — entropy computed over clusters of semantically equivalent samples — which outperformed naive entropy and self-evaluation baselines at predicting incorrect answers across multiple models and datasets. On self-correction, Ji et al. [10] showed that an iterative generate–score–refine self-reflection loop measurably reduces hallucination, providing a control-loop template this project can adapt for extraction. On confidence, Guo et al. [11] established that modern neural networks are systematically overconfident and that temperature scaling is a nearly universal post-hoc fix, while Kadavath et al. [12] showed that language models can produce usefully calibrated self-evaluations of their own answer correctness, improving with model scale. Gap: these techniques are developed and evaluated on open-ended question answering and free-form generation; their application specifically to scoring confidence in a structured field extracted from a supplier document — where the relevant ground truth is the document's own arithmetic, not an external fact — is unexplored, and is the opportunity the verification layer exploits.

#### 2.1.4 Document-Gateway Architecture and API Idempotency

The final design concern is architectural: how a document-digitization capability is packaged so that an existing inventory or ERP system can consume it. The prevailing industry pattern — variously described as a *smart document* service or a *document-processing API gateway* — separates capture from processing from consumption: a thin client submits a document image to a cloud endpoint, the recognition and extraction pipeline runs server-side, and the structured result is returned to an authorized consuming system through a documented API contract rather than written directly into the consumer's database. This separation is what allows a business to automate its data entry without replacing the inventory software it already runs, and it is the pattern the system adopts. Its practical viability is evidenced by the commercial platforms surveyed in Section 2.2.2, where mobile-capture-to-cloud-to-API integration is standard across both purpose-built extraction services and inventory-side platforms.

Adopting this pattern brings one specific reliability obligation. Because the system is a stateless gateway rather than a system that owns persistent inventory state, its correctness requirement is narrower than in a data-owning architecture, but it is not trivial: a retried or duplicate document submission (for example, a mobile-app upload retried after a network failure) must not result in duplicate or conflicting JSON output being delivered downstream, since the consuming ERP would otherwise double-count stock. Helland [13] shows that in any system where an operation may be retried, message processing must be designed idempotent — a message may be delivered zero or more times, never guaranteed exactly once — which directly motivates giving each document submission a client-supplied identifier that the API can use to recognize and safely ignore a duplicate resubmission. **Gap:** the idempotency literature is written largely for systems that own persistent state (event-sourced ledgers, databases), and the smart-document-gateway pattern itself is documented mainly in product literature rather than in peer-reviewed work; the specific combination — an idempotent, stateless recognition gateway with no owned inventory state — is not directly addressed in either body of work.

#### 2.1.5 Summary of the Literature

Table 2.1 consolidates the reviewed literature by theme and the design decision each theme informs.

| Theme | Key works | Informs |
|---|---|---|
| Character & document structure recognition | TrOCR [1]; LayoutLM family [2]; Donut [3] | OCR stage architecture and document-type/structure classification |
| Schema-constrained output | FSM-guided decoding [4]; grammar-constrained LLMs [5]; JSONSchemaBench [6]; format-restriction caution [7] | JSON output stage; choice of cloud-side decoding approach |
| Hallucination & calibration | SelfCheckGPT [8]; semantic entropy [9]; self-reflection [10]; calibration [11]; self-knowledge [12] | Verification of extracted fields before finalizing output |
| Document-gateway architecture / idempotency | Idempotence [13]; commercial gateway practice (Section 2.2.2) | Stateless capture-to-API packaging; idempotent submission design |

### 2.2 Problem Analysis

This section decomposes the problem into its constituent technical challenges, examines why existing systems fail to address them, and consolidates the research gap.

#### 2.2.1 Decomposition of the Technical Problem

The end-to-end task — from a photographed supplier document to a correct, standardized JSON output — factors into three sub-problems, each with a distinct failure mode.

**(1) Recognition under heterogeneity.** Documents vary along two axes: production method (printed, thermal, handwritten) and layout (no two suppliers share a template), and the system must also determine the document's type/structure before its content can be correctly interpreted. Template-based parsing is ruled out by the layout axis, so the recognition stage must be format-agnostic and must explicitly classify document structure/type, not just extract raw text.

**(2) Structured extraction, schema conformance, and verification.** Mapping recognized text to typed fields (item, quantity, unit price, line total, document type) is an inference task performed by a language model. Constrained decoding [4] eliminates malformed-output failures, but syntactic validity does not imply semantic correctness — the residual risk is a well-formed JSON record containing an incorrect field value. The system addresses this by cross-checking extracted numeric fields against the document's own arithmetic (quantity × unit price versus line and document totals) and flagging records that fail the check as low-confidence, rather than presenting every extracted field with equal, unverified confidence.

**(3) Reliable, idempotent API delivery without owned persistent state.** Because the system does not own or persist inventory state, its correctness obligation is narrower than in a ledger-owning design: each document submission must produce its JSON output reliably, and a retried or duplicate submission must not cause duplicate or conflicting output to be delivered to the downstream ERP/inventory system that ultimately owns the inventory data.

#### 2.2.2 Analysis of Existing Systems

Following the supervisor's guidance that the review should examine existing software alongside the academic literature, this section surveys the commercial landscape in three categories. Existing software and services approach parts of the problem from distinct directions, and none addresses the combination this project targets.

**(a) General-purpose cloud document-AI platforms.** AWS Textract, Google Document AI, and Azure AI Document Intelligence provide strong character recognition and, to varying degrees, field and table extraction for invoices and receipts. All three expose the capability as a cloud API, and all three are plausible foundations on which a system such as this could be built rather than competitors to it. Their reported accuracy differs materially on the specific sub-task that matters most here: independent benchmarking reports Azure and AWS as currently stronger than Google Document AI on invoice line-item extraction, with Google reported at roughly 82% field accuracy but substantially weaker on line-item structure. Critically, none of these platforms treats document-type classification (distinguishing a purchase order from a customer copy or delivery note) as a first-class output the way this project does.

**(b) Purpose-built invoice and receipt extraction APIs.** Nanonets, Mindee, Veryfi, Docsumo, Affinda, and Klippa go further than the general platforms, offering invoice-specific field extraction together with a human-review interface for low-confidence fields — a pipeline shape closely matching this project's own extraction and verification stage. These platforms are strong points of comparison for the extraction sub-problem, but they are general document-processing tools rather than a document-structure-recognition-first pipeline purpose-built for the supplier-document taxonomy (purchase order, customer copy, delivery note, receipt) this project targets.

**(c) Inventory and ERP-side platforms.** Finale Inventory, HandiFox, and Apptricity already support mobile-capture-to-cloud-to-API integration for supplier invoices, typically routing a captured document through OCR and an approval step before pushing the result into an accounting or inventory backend. Their existence confirms that the mobile-to-cloud-to-API architecture this project adopts is an established, low-risk pattern in this product category rather than a novel one. These platforms treat document capture as one step in a larger owned inventory system, rather than as a standalone, stateless recognition gateway a business can call from whatever system it already runs.

Table 2.2 summarizes the comparison against the requirements derived in the decomposition in Section 2.2.1.

| Requirement | General cloud document-AI | Purpose-built invoice APIs | Inventory/ERP platforms | Proposed system |
|---|---|---|---|---|
| Reads printed and handwritten documents | Partial | Partial | No (assumes input) | Yes |
| Classifies document type (PO vs. receipt vs. customer copy vs. delivery note) | Partial | Partial | No | Yes |
| Recognizes document structure (line-item table regions) | Partial | Yes | No | Yes |
| Arithmetic self-validation of extracted fields before finalizing output | Partial | Yes | No | Yes |
| Mobile-capture-to-cloud gateway integration pattern | Partial (API only) | Yes | Yes | Yes |
| Delivered as a stateless JSON API for existing ERP/inventory systems, with no owned inventory state | Yes | Yes | Partial (owns inventory state) | Yes |

#### 2.2.3 Consolidated Research Gap

Reading the literature review and the systems analysis together, the gap is specific. The research literature and the commercial landscape together supply every individual ingredient the problem demands — recognition architectures for heterogeneous documents (Section 2.1.1), decoding constraints that guarantee schema validity (Section 2.1.2), and hallucination detection and calibration techniques (Section 2.1.3) — and the commercial landscape demonstrates that a mobile-capture-to-cloud-API architecture (Section 2.2.2) is an established, viable pattern. However, no reviewed academic work or commercial product composes document structure/type recognition as a first-class, verified output with a stateless, idempotent capture-to-API pipeline purpose-built for the heterogeneous, vendor-specific supplier-document taxonomy small and medium businesses actually receive. The proposed system occupies this intersection: a system contribution (composing existing recognition and extraction techniques into this specific pipeline) and an empirical contribution (measuring its recognition and extraction accuracy on real supplier documents). The methodology by which the system is built and evaluated is the subject of the next chapter.

### Summary

This chapter reviewed the literature underpinning each stage of the proposed pipeline — character and document structure recognition, schema-constrained output, hallucination mitigation, and document-gateway architecture — and, per the project's supervision, examined the existing commercial landscape alongside it: general cloud document-AI platforms, purpose-built invoice extraction APIs, and inventory/ERP-side platforms. The problem analysis decomposed the technical challenge into three sub-problems and consolidated a specific research gap: no reviewed work, academic or commercial, combines document-structure recognition as a first-class output with a verified, stateless, idempotent document-capture-to-API pipeline for small-business inventory documents. Chapter 3 now presents the research methodology by which the system is designed to occupy that gap.

---

## Chapter 3: Research Methodology

This chapter presents the research methodology for the system. Section 3.1 presents the proposed framework — the development approach and system architecture. Section 3.2 covers the dataset and software project requirements. Section 3.3 analyzes the algorithms and models underlying each design choice, including the design decisions that remain open at this stage. Section 3.4 explains each of the six pipeline modules in turn.

The work described here is **proposed rather than completed**. This report is submitted at the design stage of the project: the framework, dataset plan, algorithm analysis, and module designs presented below define what will be implemented, while the implementation itself and its evaluation are the subject of Chapter 4. Where a design decision remains genuinely open, this chapter states the decision, the options considered, and the currently preferred choice, rather than presenting an unresolved question as though it were settled.

### 3.1 Proposed Framework

The engineering problem stated in Section 1.1 is recognizing the characters and structure of a heterogeneous supplier document and extracting its content into a schema-valid structured record. Recognition is a perception task with established architectures and well-defined accuracy metrics, so its design question is which components to compose and how to measure them on documents that are messier than the benchmarks those components were validated on. Extraction is an inference task under uncertainty, where the model's output cannot be accepted on its own authority, so its design question is how to bound the rate of silently wrong output using the document's own internal evidence.

**Development approach.** The project follows an **iterative, evaluation-driven development lifecycle** — an Agile-style adaptation of the classical SDLC in which the recognition pipeline is built and refined across short, measurable cycles rather than in a single waterfall pass. The methodology proceeds in five phases — requirement analysis and document collection; data model and API contract design; recognition pipeline; verification and digitization API core; and evaluation and benchmarking — as shown in Figure 1. These phases are not a strict sequence: results from the evaluation phase (Chapter 4) feed back into the API contract and the extraction design, and the pipeline is refined across repeated cycles rather than built once.

An iterative approach is chosen deliberately rather than by default. As established in the complex engineering analysis (Section 1.7, WP3), the central design variables of this system have no closed-form answer: the confidence threshold that flags a low-confidence extraction for review trades false-positive rate against silent-error rate, and the correct operating point cannot be derived analytically — it must be measured on real documents and then tuned. Similarly, the JSON output schema cannot be finalized before the corpus reveals which fields actually appear across vendors, and the document-type taxonomy cannot be fixed before real examples of each type have been examined. A waterfall pass would force these decisions to be made at their point of least information. The feedback loop shown in Figure 1 exists precisely to allow them to be revised as evidence accumulates, and the deliverables of the early phases — the schema in Section 3.4 and the taxonomy in Section 3.4 — are treated as provisional, expected to be revised at least once after the corpus described in Section 3.2 is collected.

![Figure 1](figures/fig1_methodology.png)

**Figure 1.** Development methodology: the phases of the iterative, evaluation-driven lifecycle and the feedback loop from evaluation back into the API contract and extraction design.

**System architecture.** The proposed architecture is shown in Figure 2. A mobile application captures a supplier document as a photograph or scan and uploads it to a cloud endpoint. Server-side, the document passes through recognition (OCR and document structure/type classification), schema-constrained extraction, and arithmetic self-validation. The result is a standardized JSON representation, retrieved by an authorized ERP or inventory management system through the digitization API.

![Figure 2](figures/fig2_architecture.png)

**Figure 2.** Proposed system architecture: mobile capture, cloud-hosted recognition and extraction pipeline with arithmetic self-validation, and delivery to an authorized ERP or inventory system via the digitization API.

Two architectural boundaries are load-bearing and are stated explicitly because they constrain every module design in Section 3.4.

**The mobile client is capture-only.** No recognition, extraction, or language-model inference runs on the device. All processing is cloud-hosted. This follows the reasoning given in Section 1.2: running a capable language model on a mobile device introduces reliability, performance, and maintenance problems that a cloud-hosted deployment avoids, and the capability gap between what runs comfortably on a phone and what is needed for reliable extraction over noisy documents is large enough that attempting on-device inference would compromise the primary objective. The client's responsibilities are limited to image acquisition, basic capture-quality checks, idempotency-key generation, and upload.

**The system owns no inventory state.** The system is a digitization gateway, not an inventory management system. It does not maintain stock levels, valuations, transaction history, or a product catalog; those remain the responsibility of the consuming ERP. The system's only persistent state is operational: a submission log sufficient to enforce idempotency, detailed in Section 3.4. This boundary is what allows the system to be adopted without replacing software a business already runs, and it narrows the correctness obligation to the one described in Section 2.1.4 — that a retried submission must not produce duplicate downstream output.

Figure 4 expands Figure 2 into a stage-by-stage view, showing the input and output of each module and the point at which the pipeline departs from a straight line: the confidence-routed branch into arithmetic self-validation and low-confidence flagging.

![Figure 4](figures/fig4_pipeline.png)

**Figure 4.** Detailed pipeline diagram: per-stage inputs and outputs from captured image through to JSON response, showing where arithmetic self-validation and confidence flagging attach.

### 3.2 Data Set Analysis / Software Project Requirement

#### 3.2.1 Data Set Analysis

**The corpus described in this section has not yet been collected.** What follows is the collection and annotation protocol that will be executed.

**Rationale.** The system must be evaluated on documents representative of what it will actually encounter. Public document-understanding benchmarks are valuable but insufficient on their own: they are comparatively clean and do not include the thermal-printed and handwritten formats common in small-shop practice, which this project's document-structure recognition targets.

**Collection protocol.** Small shops and fulfilment centres will be approached and asked to contribute supplier documents they have already received. Contribution is voluntary and by informed consent, with the purpose of the research, the intended use of the documents, and the retention period explained in advance. Documents will be captured through the same mobile capture path the system uses in production, so that image characteristics match deployment conditions rather than being idealized scans.

**Target composition.** The corpus is stratified along two axes, since both drive difficulty. By production method: printed, thermal-printed, and handwritten. By document type: purchase order, customer copy, delivery note, and receipt. The target is a minimum of 30 documents per document-type class to support a meaningful confusion matrix in Chapter 4, with the printed/thermal/handwritten split reflecting natural prevalence rather than being forced to uniformity — a corpus that over-represents handwritten documents would misstate expected accuracy in deployment. Table 3.1 summarizes the target composition.

**Table 3.1 — Target corpus composition (provisional).**

| Document type | Printed | Thermal-printed | Handwritten | Minimum total |
|---|---|---|---|---|
| Purchase order | majority | — | some | 30 |
| Delivery note | some | some | majority | 30 |
| Customer copy | majority | some | some | 30 |
| Receipt | some | majority | some | 30 |

**Annotation.** Two layers of ground truth will be produced: (i) a document-type label per document; and (ii) field-level transcription of line items — description, quantity, unit price, line total — and document-level totals.

Annotation will be performed by team members against a written guideline. A subset will be double-annotated and inter-annotator agreement reported, since an evaluation against ground truth of unmeasured reliability would overstate its own precision.

**Supplementary public data.** Public benchmarks including SROIE, CORD, and FUNSD will be used for pretraining and for sanity-checking recognition performance against published figures.

**Ethical considerations.** Supplier documents contain commercially sensitive information: prices, volumes, and trading relationships. Contributing businesses' and suppliers' identifying details will be anonymized in any published artifact of this research, documents will be stored with access limited to the project team, and contributors may withdraw their documents. These commitments follow directly from the responsibilities identified in Section 1.7 (WK7 and WP5).

#### 3.2.2 Software Project Requirement

Table 3.2 sets out the proposed technology stack. Several entries depend on the open decisions recorded in Section 3.3.

**Table 3.2 — Proposed technology stack (provisional).**

| Layer | Tool / technology | Purpose | Justification |
|---|---|---|---|
| Mobile client | Cross-platform mobile framework | Document capture, quality checks, upload | Single codebase across platforms; the client is thin, so framework choice is low-risk |
| Backend service | Python web framework | API endpoints, pipeline orchestration | Python aligns with the ML/NLP tooling the pipeline depends on |
| OCR / document AI | Commercial cloud service | Text and layout recognition | Per Decision 1, Section 3.3 |
| Language model | Commercial LLM API | Schema-constrained extraction | Per Decision 2, Section 3.3 |
| Constrained decoding | Provider JSON mode or constrained-decoding library | Schema-valid output | Per Decision 3, Section 3.3 |
| Datastore | Relational database | Submission log | The data model in Section 3.4 is relational and modest in scale |
| Version control | Git | Source management and collaboration | Standard practice |
| Testing | Unit and integration test framework; scripted evaluation harness | Correctness and reproducible metrics for Chapter 4 | The evaluation methodology must be repeatable across iterations |

The evaluation harness is listed as a build requirement deliberately: because the methodology is iterative and metrics are recomputed each cycle, the measurement pipeline is itself part of the system rather than an afterthought, even though its output is reported only in Chapter 4.

### 3.3 Algorithm/Model Analysis

This section analyzes the algorithmic approach behind each stage of the pipeline and records the design decisions that remain genuinely open. Section 3.4 then explains how these algorithms are composed into concrete modules.

**Character recognition.** The recognition stage is deliberately built on an existing cloud OCR service rather than a model trained from scratch — the contribution of this project is the composition and the trust layer around the model, not a novel OCR architecture. The architecture underlying modern OCR of this kind is well established: TrOCR [1] demonstrates that a Transformer encoder–decoder pairing pretrained vision and language models achieves strong results across printed, handwritten, and receipt-domain text without hand-built preprocessing, and bounding-box output is retained specifically because the structure-recognition stage depends on spatial information. An OCR-free alternative, Donut [3], was considered and rejected: it forecloses the use of mature commercial OCR services whose accuracy on noisy real-world documents is well characterized, and it requires substantially more training data than the corpus plan in Section 3.2 will produce.

**Document structure and type classification.** The same visual field means different things depending on document type, so classification must precede extraction. The LayoutLM family of models [2] establishes the relevant technique — extending a text encoder with two-dimensional positional embeddings derived from OCR bounding boxes, so the model learns that spatially co-located text is often semantically related, with document-image classification among its demonstrated tasks. (Reference [2] is among the citations flagged at the head of this document as not yet verified against the source publication.) Because the corpus does not yet exist, the classifier is staged: few-shot prompting of a language model over recognized text and coarse layout description is used first, requiring no training data at the cost of per-document inference expense and lower expected accuracy; a layout-aware classifier is fine-tuned once the Section 3.2 corpus is collected and labelled, and evaluated against the few-shot baseline. This two-stage approach avoids blocking downstream work on corpus collection.

**Schema-constrained extraction.** Malformed output is made impossible by construction rather than caught after the fact. Willard and Louf [4] show that guided generation can be reformulated as transitions over a finite-state machine, precomputing an index over the model's vocabulary so invalid tokens can be masked with negligible per-step overhead; Geng et al. [5] demonstrate that grammar-constrained decoding allows few-shot models to rival fine-tuned task-specific ones on structured tasks. JSONSchemaBench [6] documents that constrained-decoding engines differ substantially in real-world schema coverage, which is why the specific engine is treated as an open decision below rather than an implementation detail. Constraining the output guarantees syntactic validity, not semantic correctness — a schema-valid record can still contain a hallucinated price — and Tam et al. [7] further caution that strict format restriction can itself degrade a model's reasoning relative to freer generation. Both findings motivate the separate verification algorithm described next, rather than reliance on the schema alone.

**Verification and confidence scoring.** Two independent mechanisms verify an extracted record before it reaches the output. The first is deterministic **arithmetic self-validation**: where quantity, unit price, and line total are all extracted, the identity quantity × unit price = line total is checked directly, and line totals are summed and compared against the stated grand total — a zero-cost signal requiring no model. The second is **confidence scoring**: each extracted record is scored, and a record falling below threshold is flagged as `review_required` in the output rather than silently returned at full confidence. The reliability of the confidence signal itself is not to be taken for granted: Guo et al. [11] establish that modern neural networks are systematically overconfident and that temperature scaling is a simple, effective post-hoc correction. Where model-internal probabilities are unavailable, as they often are through commercial APIs, SelfCheckGPT [8] provides a black-box alternative — sampling multiple responses and measuring their mutual consistency — with semantic entropy [9] offering a more principled clustering-based variant.

**Open algorithm and model decisions.** Table 3.3 records the choices that remain genuinely open at this design stage, rather than presenting them as already settled.

**Table 3.3 — Open algorithm and model decisions.**

| # | Decision | Options | Current preference and rationale |
|---|---|---|---|
| 1 | OCR / document-AI service | AWS Textract; Google Document AI; Azure AI Document Intelligence | Azure or AWS, on the line-item extraction benchmarking reported in Section 2.2.2; final choice pending a pilot on collected documents |
| 2 | Language model for extraction | Commercial LLM API providers | Undecided pending a pilot on collected documents; evaluated on schema-conformance and field accuracy |
| 3 | Constrained-decoding mechanism | Provider-native JSON mode; a library such as Outlines or XGrammar | Provider-native mode if schema coverage suffices, per JSONSchemaBench findings; library fallback otherwise |
| 4 | **Confidence signal source** | Token log-probabilities; sampled-consistency (SelfCheckGPT-style); a separately calibrated classifier | Undecided — the most load-bearing open item. Log-probabilities are cheapest but frequently unavailable through commercial APIs; sampled consistency is always available but multiplies inference cost |
| 5 | Document-type classifier | Few-shot LLM prompting; fine-tuned layout-aware model | Staged, as above: few-shot first, fine-tune after corpus collection |
| 6 | Result delivery | Synchronous response; asynchronous job with polling or webhook | Synchronous by default, since no human-confirmation step intervenes between submission and result; revisited if processing latency requires otherwise |

Decision 4 is highlighted because the confidence-scoring mechanism described above depends on it entirely, and because the choice is constrained by the provider selected in Decision 2. It is scheduled for resolution during the first implementation cycle in Chapter 4, and its resolution is a prerequisite for the extraction-accuracy evaluation described there.

### 3.4 Explanation of Different Modules

This section explains each of the six modules that compose the pipeline of Figure 4. For each, the purpose, input, processing, output, and principal failure mode are stated; the algorithmic reasoning behind each module's processing was analyzed in Section 3.3 and is not repeated here.

#### 3.4.1 Document Capture Module

**Purpose.** Acquire a usable image of a supplier document and submit it for processing.

**Input.** A physical document presented to the device camera, or an existing image or PDF from device storage.

**Processing.** The module performs capture-quality checks before upload, because recognition accuracy downstream is bounded by image quality and a rejected capture is far cheaper than a silently misread document. The checks are: edge/boundary detection to confirm the full document is within frame, blur detection, and glare or low-contrast detection — each surfaced to the user as an actionable prompt to retake rather than a silent failure. The module then generates a client-supplied idempotency key (a UUID bound to the capture event, not to the upload attempt) so that a retried upload after a network failure carries the same key as the original, and uploads the image together with that key.

**Output.** An image payload plus idempotency key transmitted to the API gateway.

**Failure mode.** A poor-quality capture that passes the quality checks propagates recognition errors through the entire pipeline. This is mitigated rather than eliminated; the arithmetic and confidence checks downstream provide the second line of defence.

#### 3.4.2 Character Recognition Module

**Purpose.** Convert the document image into machine-readable text with positional information.

**Input.** The uploaded document image.

**Processing.** A cloud OCR service performs text detection and recognition, returning recognized text tokens together with their bounding-box coordinates, using the architecture analyzed in Section 3.3.

**Output.** Recognized text tokens with bounding boxes and per-token recognition confidence where the service exposes it.

**Failure mode.** Misrecognized digits are the most damaging error class, since a wrong quantity or price is both consequential and hard to detect by inspection. Chapter 4 therefore reports character error rate on numeric fields separately from the overall figure.

#### 3.4.3 Document Structure and Type Recognition Module

**Purpose.** Determine what kind of document is being processed and locate its structurally meaningful regions. This is the primary stated objective of the project.

**Input.** Recognized text tokens with bounding boxes from Section 3.4.2.

**Processing.** The module performs two related tasks using the staged approach analyzed in Section 3.3: **document-type classification**, assigning the document to one of the taxonomy classes shown in Figure 5 — purchase order, customer copy, delivery note, or receipt — and **structural region detection**, locating the line-item table, header block, and total block within the page.

**Output.** A document-type label with confidence, plus bounding-box regions for the line-item table, header, and totals.

**Failure mode.** A misclassified document type propagates a systematic misinterpretation of every field extracted from it — the most consequential single failure in the pipeline, and the reason Chapter 4 reports a full confusion matrix rather than accuracy alone.

![Figure 5](figures/fig5_doctype_taxonomy.png)

**Figure 5.** Document-type taxonomy: the four target classes with the structural and lexical cues that distinguish them, and the inventory implication of each.

#### 3.4.4 Schema-Constrained Extraction Module

**Purpose.** Convert the recognized text of the identified regions into structured line-item records conforming to a fixed JSON schema.

**Input.** Recognized text, structural regions, and document type from Sections 3.4.2–3.4.3.

**Processing.** A cloud-hosted language model performs the extraction under the constrained-decoding approach analyzed in Section 3.3, guaranteeing that output conforms to the schema in Table 3.4.

**Output.** A set of line-item records conforming to the schema in Table 3.4.

**Failure mode.** A well-formed record containing a wrong value. This is the residual risk that arithmetic self-validation and confidence scoring exist to address.

**Table 3.4 — Target JSON output schema (provisional; to be revised after corpus collection).**

| Field | Type | Required | Description |
|---|---|---|---|
| `submission_id` | string (UUID) | Yes | Client-supplied idempotency key |
| `document_type` | enum | Yes | `purchase_order` \| `customer_copy` \| `delivery_note` \| `receipt` |
| `document_type_confidence` | float | Yes | Classifier confidence, 0–1 |
| `supplier_name` | string | No | As printed on the document |
| `document_date` | date (ISO 8601) | No | Document-issue date |
| `document_number` | string | No | Invoice or reference number |
| `line_items` | array | Yes | Zero or more line-item objects |
| `line_items[].raw_text` | string | Yes | Item description exactly as recognized |
| `line_items[].quantity` | number | No | Quantity as extracted |
| `line_items[].unit_price` | number | No | Unit price as extracted |
| `line_items[].line_total` | number | No | Line total as extracted |
| `line_items[].arithmetic_check` | enum | Yes | `passed` \| `failed` \| `not_applicable` |
| `grand_total` | number | No | Document total as extracted |
| `review_required` | boolean | Yes | True if any line item fails the arithmetic check or falls below the confidence threshold |

The `arithmetic_check` field is deliberately part of the contract rather than internal state: a consuming ERP must be able to distinguish a value the system verified from one it merely extracted.

#### 3.4.5 Digitization API Module

**Purpose.** Expose the pipeline as a service an authorized ERP or inventory system can consume.

**Input.** Submissions from the mobile client; result requests from consuming systems.

**Processing.** The API exposes a submission endpoint accepting a document image and idempotency key, and a retrieval path returning the standardized JSON. Consuming systems authenticate as authorized clients scoped to a particular shop. Idempotency is enforced at the submission endpoint: Helland [13] shows that in any system where an operation may be retried, message delivery guarantees are "zero or more times" rather than exactly once, so the service records each `submission_id` it has processed, and a submission arriving with a previously seen key returns the original result rather than reprocessing the document.

**Output.** A standardized JSON document conforming to Table 3.4.

**Failure mode.** Two genuinely distinct captures colliding on one idempotency key would suppress a real document. The key is therefore generated per capture event rather than per user action, and bound to the image payload.

![Figure 6](figures/fig6_api_sequence.png)

**Figure 6.** API sequence diagram: capture → submit (with idempotency key) → process → result retrieval by the consuming ERP, including the duplicate-submission path returning the original result without reprocessing.

#### 3.4.6 Data Model

Although the system holds no inventory state, it maintains the minimum persistent state its own operation requires. A single entity is proposed. **Submission** is the idempotency and audit record referenced by Section 3.4.5: submission ID, shop, received timestamp, processing status, and a reference to the generated JSON result.

The deliberate omission is as important as what is included: there is no Shop-owned catalog, Stock, Transaction, or Valuation entity, because item-name reconciliation and inventory state both belong to the consuming ERP. A reviewer checking whether the architectural boundary of Section 3.1 is genuinely respected can verify it against this data model.

![Figure 7](figures/fig7_data_model.png)

**Figure 7.** Entity-relationship diagram: the Submission record, alongside the inventory and catalog entities deliberately excluded from the gateway's scope.

### Summary

This chapter has presented the research methodology for the system. Section 3.1 set out the proposed framework: an iterative, evaluation-driven development approach chosen because the project's central design variables cannot be fixed correctly before evidence is gathered, and a system architecture constrained by two explicit boundaries — a capture-only mobile client and a gateway that owns no inventory state. Section 3.2 described the dataset collection and annotation protocol, not yet executed, and the software project requirements. Section 3.3 analyzed the algorithms underlying recognition, classification, extraction, and verification, and recorded six open design decisions rather than presenting them as settled. Section 3.4 explained each of the six pipeline modules in turn, together with its failure mode and the shared data model underlying them.

What has been presented is a design, not a result. Chapter 4 will report the implementation of this methodology, the evaluation metrics and performance analysis it produces, and a comparison against the baselines identified throughout this chapter.

---

## Material Reserved for Later Chapters

The following content was developed during the Chapter 3 restructuring and is preserved here verbatim for reuse. It does not belong in Chapter 3 under the required report structure (3.1 Proposed Framework / 3.2 Data Set Analysis and Software Project Requirement / 3.3 Algorithm and Model Analysis / 3.4 Explanation of Different Modules), but both pieces are complete, useful drafts for the chapters that do call for them.

### For Chapter 4 (Implementation and Result Analysis): Evaluation Methodology

Evaluation is organized per module, so that a failure can be attributed to the stage that caused it rather than observed only as degraded end-to-end output. Each module is measured against a baseline representing the reasonable simpler alternative, since a result that does not beat the simple approach does not justify the complex one.

**Table — Planned evaluation metrics and baselines.**

| Module | Metrics | Baseline for comparison |
|---|---|---|
| Character recognition | Character Error Rate (CER) and Word Error Rate (WER); CER on numeric fields reported separately | Off-the-shelf cloud OCR output without project-specific handling |
| Document type & structure | Classification accuracy; macro-averaged F1; full confusion matrix; region-detection IoU | Rule/keyword heuristic classifier |
| Schema-constrained extraction | Schema-validity rate; field-level precision, recall, F1 | Unconstrained LLM decoding with post-hoc JSON parsing |
| Verification | Silent-error rate at varying confidence thresholds; arithmetic-check catch rate | No verification (extracted values returned as-is) |
| Digitization API | End-to-end latency (median, 95th percentile); correctness under duplicate submission | — |

**The headline evaluation.** The central empirical claim of the project is that arithmetic self-validation and confidence scoring measurably reduce the silent-error rate relative to unverified extraction. This is measured as a curve, not a point: the confidence threshold is swept, and for each setting both the review-flag rate and the resulting silent-error rate are recorded, tracing the tradeoff and identifying a defensible operating point.

**A caution on validity.** A threshold tuned against clean public benchmarks would likely not transfer to real supplier documents. It is a principal reason the corpus described in the dataset analysis is collected at all, and the verification evaluation will be conducted on that corpus rather than on public data.

![Figure 8](figures/fig8_evaluation.png)

**Figure 8.** Evaluation framework: each pipeline module mapped to its metrics and its comparison baseline, with the verification accuracy tradeoff curve identified as the headline contribution.

### For Chapter 5 (Standards, Constraints, and Milestones): Project Timeline and Gantt Chart

The work is divided across the two capstone phases. CSE 498A covers problem definition, literature and systems review, architecture and module design, the API contract, and the corpus collection protocol — the content of this report. CSE 498B covers corpus collection and annotation, implementation of the pipeline modules, resolution of the open decisions recorded in the algorithm/model analysis, evaluation against the framework above, and reporting.

**A Gantt chart mapping this timeline across CSE 498A and 498B is not yet included and will be added for Chapter 5.**

Corpus collection is the critical path. The fine-tuned document-type classifier depends on it, and it is the phase least under the team's direct control, since it depends on the cooperation of participating businesses. Its early scheduling in 498B is deliberate, and the staged classifier strategy exists specifically so that implementation work is not blocked while collection proceeds.

---

## References (Chapter 1–2, revised)

[1] M. Li, T. Lv, J. Chen, L. Cui, Y. Lu, D. Florencio, C. Zhang, Z. Li, and F. Wei, "TrOCR: Transformer-based optical character recognition with pre-trained models," in *Proc. AAAI Conference on Artificial Intelligence*, vol. 37, pp. 13094–13102, 2023.

[2] Y. Xu et al., "LayoutLM: Pre-training of Text and Layout for Document Image Understanding" (and successors LayoutLMv2, LayoutLMv3) — *citation to be verified directly against the papers before finalizing; currently sourced from secondary/web summaries, not read directly.*

[3] G. Kim, T. Hong, M. Yim, J. Nam, J. Park, J. Yim, W. Hwang, S. Yun, D. Han, and S. Park, "OCR-free Document Understanding Transformer," in *Proc. European Conference on Computer Vision (ECCV)*, 2022. (arXiv:2111.15664) — *has a clear arXiv ID; still recommend downloading and verifying directly before finalizing.*

[4] B. T. Willard and R. Louf, "Efficient guided generation for large language models," arXiv preprint arXiv:2307.09702, 2023.

[5] S. Geng, M. Josifoski, M. Peyrard, and R. West, "Grammar-constrained decoding for structured NLP tasks without finetuning," in *Proc. EMNLP*, pp. 10932–10952, 2023.

[6] S. Geng, H. Cooper, M. Moskal, S. Jenkins, J. Berman, N. Ranchin, R. West, E. Horvitz, and H. Nori, "JSONSchemaBench: A rigorous benchmark of structured outputs for language models," arXiv preprint arXiv:2501.10868, 2025.

[7] Z. R. Tam, C.-K. Wu, Y.-L. Tsai, C.-Y. Lin, H. yi Lee, and Y.-N. Chen, "Let me speak freely? A study on the impact of format restrictions on performance of large language models," in *Proc. EMNLP: Industry Track*, pp. 1218–1236, 2024.

[8] P. Manakul, A. Liusie, and M. J. F. Gales, "SelfCheckGPT: Zero-resource black-box hallucination detection for generative large language models," in *Findings of ACL: EMNLP 2023*, pp. 9004–9017, 2023.

[9] S. Farquhar, J. Kossen, L. Kuhn, and Y. Gal, "Detecting hallucinations in large language models using semantic entropy," *Nature*, vol. 630, pp. 625–630, 2024.

[10] Z. Ji, T. Yu, Y. Xu, N. Lee, E. Ishii, and P. Fung, "Towards mitigating hallucination in large language models via self-reflection," in *Findings of ACL: EMNLP 2023*, pp. 1827–1843, 2023.

[11] C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, "On calibration of modern neural networks," in *Proc. ICML, PMLR 70*, 2017.

[12] S. Kadavath, T. Conerly, A. Askell, T. Henighan, D. Drain, E. Perez, et al., "Language models (mostly) know what they know," arXiv preprint arXiv:2207.05221, 2022.

[13] P. Helland, "Idempotence is not a medical condition," *Communications of the ACM*, vol. 55, no. 5, pp. 56–65, 2012.

*A full literature review update (with LayoutLM/Donut citations verified directly from source, and any additional existing-systems research) will be finalized as part of the complete literature review deliverable.*
