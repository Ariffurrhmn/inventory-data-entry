# SmartDox — Literature Review Draft

Auto-compiled from PDFs in `research/literature/`, organized by the 8 review buckets. Each entry lists the citation as read from the paper itself, what it found, how it supports SmartDox, and a bucket-fit check.

**Coverage note:** All 8 buckets have ≥3 papers (range 3–5), so none fall below the "thin" threshold (<2 solid papers). Bucket 6 (HITL/Active Learning) is the smallest at 3 papers — still adequate, but the shallowest if you want redundancy.

---

## 1. Multilingual / Handwritten OCR (low-resource, code-mixed scripts)

**[Saha & Rahman, 2024]** BanglaNet: Bangla Handwritten Character Recognition using Ensembling of Convolutional Neural Network. *arXiv:2401.08035v2 (cs.CV)*, 2024.
- Found: An ensemble of three CNNs (Inception-, ResNet-, and DenseNet-based) trained on three Bangla handwritten datasets (CMATERdb, BanglaLekha-Isolated, Ekush), averaging softmax outputs for a final prediction; reports 97–98%+ accuracy on basic characters, compound characters, numerals, and modifiers.
- Supports: Validates that Bangla handwritten character recognition is achievable at high accuracy, underpinning feasibility of the handwritten-Bangla component of SmartDox's OCR stage.
- Bucket check: confirmed, with the caveat that it's isolated character recognition, not full-document/word-level OCR — a narrower supporting piece rather than an end-to-end system.

**[Rabby, Ali, Islam, Abujar & Rahman, 2024]** Enhancement of Bengali OCR by Specialized Models and Advanced Techniques for Diverse Document Types. *arXiv:2402.05158v1 (cs.CV)*, 2024. (Apurba Technologies / U. Alabama Birmingham; Bangladesh Ministry of ICT EBLICT project.)
- Found: A full production Bengali OCR pipeline handling computer-composed, letterpress, typewriter, and handwritten documents, with specialized segmentation, layout reconstruction, signature/logo detection, CPU-oriented model quantization, and Kafka-based async queuing; ~98% confusion-matrix accuracy and ~87% Levenshtein accuracy across document types, beating Tesseract by a wide margin.
- Supports: The single strongest match in this folder — directly demonstrates heterogeneous document-type handling (printed/handwritten/typewriter) and a queuing/pipeline architecture analogous to SmartDox's OCR-to-ledger flow.
- Bucket check: confirmed; also substantively supports the on-device/quantized-LLM bucket given its CPU quantization discussion — worth cross-referencing there.

**[Alom, Sidike, Hasan, Taha & Asari, year not found]** Handwritten Bangla Character Recognition Using The State-of-Art Deep Convolutional Neural Networks. *Venue not stated in extractable text.*
- Found: Benchmarks six DCNN architectures (VGG, All-Conv, NiN, ResNet, FractalNet, DenseNet) on Bangla digits, 50-character alphabet, and 13 special characters; DenseNet performs best across all three (99.13% digits, 98.31% alphabet, 98.18% special characters).
- Supports: Reinforces CNN-based (especially DenseNet) architectures as a strong baseline for Bangla handwritten recognition, supporting the OCR bucket's feasibility claim.
- Bucket check: confirmed, but character-level isolated recognition only, same caveat as BanglaNet.
- **CITATION FLAG:** Venue and publication year could not be extracted from the PDF text at all (no header/footer/DOI). Self-citation to the authors' own arXiv:1705.02680 (2017) suggests a 2017–2019 publication, but this is inferred, not confirmed — **needs manual verification before citing.**

**[Li, Lv, Chen, Cui, Lu, Florencio, Zhang, Li & Wei, 2022]** TrOCR: Transformer-based Optical Character Recognition with Pre-trained Models. *arXiv:2109.10282v5 (cs.CL)*, 2022. (Beihang University / Microsoft.)
- Found: An end-to-end, convolution-free OCR architecture pairing a pre-trained image Transformer encoder (ViT/BEiT/DeiT) with a pre-trained text Transformer decoder (RoBERTa), achieving SOTA on printed (SROIE), handwritten (IAM), and scene-text benchmarks without external LMs or hand-built pre/post-processing.
- Supports: Architecturally foundational for SmartDox's OCR stage — shows a pure Transformer encoder-decoder can jointly leverage pretrained vision+language models for robust text recognition, a plausible base to fine-tune for mixed Bangla-English slip OCR.
- Bucket check: **weak fit on the "multilingual/code-mixed" criterion specifically** — this paper is English-only/Latin-script (IAM, SROIE, scene text) and never touches Bangla or code-mixing. Keep it as a general OCR-architecture reference, but flag it clearly as background rather than a multilingual paper.
- **CITATION FLAG:** Widely known as an AAAI 2023 publication, but the extractable PDF text only shows the arXiv header (v5, Sept 2022) with no AAAI proceedings info — confirm which version (arXiv preprint vs. AAAI camera-ready) you intend to cite.

---

## 2. Schema-Constrained / Structured Output LLM Extraction

**[Willard & Louf, 2023]** Efficient Guided Generation for Large Language Models. *arXiv:2307.09702*, 2023.
- Found: Reformulates regex/CFG-guided decoding as transitions over a finite-state machine, precomputing an index over the LLM vocabulary so each generation step needs only O(1) work to mask invalid tokens; extends to CFGs via pushdown automata.
- Supports: The foundational algorithm (basis of the Outlines library and cited by later engines) for making a small model's output conform to a rigid schema at near-zero runtime cost — exactly what SmartDox needs to parse OCR'd slip text into structured fields.
- Bucket check: confirmed.

**[Geng, Josifoski, Peyrard & West, 2023]** Grammar-Constrained Decoding for Structured NLP Tasks without Finetuning. *EMNLP 2023*, pp. 10932–10952.
- Found: Casts structured NLP tasks (IE, entity disambiguation, parsing) as grammar-constrained decoding; introduces "input-dependent grammars" (grammar varies per input, e.g. restricting output to a candidate set), showing few-shot grammar-constrained LLaMA/Vicuna can rival finetuned task-specific models.
- Supports: Backs schema-constrained extraction, and its input-dependent-grammar mechanism is directly analogous to constraining output to a shop's known item/party names during entity resolution — useful with no labeled data.
- Bucket check: confirmed (primary fit here; secondary relevance to entity resolution via the input-dependent grammar mechanism).

**[Geng, Cooper, Moskal, Jenkins, Berman, Ranchin, West, Horvitz & Nori, 2025]** JSONSchemaBench: A Rigorous Benchmark of Structured Outputs for Language Models. *arXiv:2501.10868v3*, 2025.
- Found: A 10K-real-world-JSON-schema benchmark evaluating six constrained-decoding frameworks (Guidance, Outlines, llama.cpp, XGrammar, OpenAI, Gemini) on efficiency, schema-feature coverage, and downstream quality; finds large gaps between frameworks and up to 4% accuracy gains from constrained decoding even on loosely-structured tasks (GSM8K).
- Supports: Directly informs SmartDox's choice of constrained-decoding engine — notably benchmarks llama.cpp itself, the planned on-device backend — and its under-/over-constrained failure taxonomy is relevant to designing the arithmetic self-validation layer.
- Bucket check: confirmed; also touches the on-device bucket since llama.cpp is one of the evaluated backends.

**[Tam, Wu, Tsai, Lin, Lee & Chen, 2024]** Let Me Speak Freely? A Study on the Impact of Format Restrictions on Performance of Large Language Models. *EMNLP 2024 Industry Track*, pp. 1218–1236.
- Found: Forcing LLMs into strict structured formats (JSON-mode/constrained decoding) significantly degrades reasoning-task accuracy (GSM8K, Last Letter, Shuffled Objects) versus freer formats, though structured formats help classification-style tasks; degradation isn't primarily parsing errors but a genuine reasoning effect.
- Supports: An important counterpoint for SmartDox — evidence that naively forcing strict JSON while reasoning about handwritten/mixed-language content could hurt extraction accuracy, motivating decoupled reasoning-then-format approaches and reinforcing the need for arithmetic self-validation and HITL as a safety net.
- Bucket check: confirmed, but note this is the bucket's cautionary/counter-evidence paper, not a straightforward advocate for schema constraints. Also touches the hallucination/calibration bucket.
- **File-naming flag:** This PDF is stored without a `.pdf` extension ("Let Me Speak Freely_ A Study on the Impact of") — it's a valid, readable PDF, just misnamed; rename it so it doesn't get missed in future folder scans.

**[Dong, Ruan, Cai, Lai, Xu, Zhao & Chen, 2025]** XGrammar: Flexible and Efficient Structured Generation Engine for Large Language Models. *8th MLSys Conference*, 2025.
- Found: Splits the vocabulary into context-independent tokens (precomputed) and context-dependent tokens (checked at runtime via a persistent pushdown automaton), achieving up to 100x lower per-token latency than prior libraries; demonstrates cross-platform deployment including on-device iPhone inference with near-zero structured-generation overhead.
- Supports: Concretely supports SmartDox's on-device llama.cpp deployment goal — explicitly benchmarks edge scenarios (iPhone 14 Pro Max, MacBook), showing schema-constrained extraction is practically feasible on resource-constrained hardware, not just server GPUs.
- Bucket check: confirmed; strongly relevant to the on-device bucket too — worth cross-listing there.

**Note:** This folder had 5 PDFs, not the expected 4 — see file-naming flag above (all 5 are legitimate and well-placed).

---

## 3. LLM Hallucination Mitigation, Self-Verification, Confidence Calibration

**[Farquhar, Kossen, Kuhn & Gal, 2024]** Detecting hallucinations in large language models using semantic entropy. *Nature*, vol. 630, 2024.
- Found: Introduces "semantic entropy" — clustering sampled LLM outputs by bidirectional entailment before computing entropy, distinguishing confident-but-differently-worded answers from genuine confabulation. Outperforms naive entropy, P(True) self-eval, and supervised regression at predicting wrong answers (avg. AUROC 0.79) across LLaMA 2/Falcon/Mistral on 5+ datasets.
- Supports: A domain-agnostic, unsupervised uncertainty score that could flag inconsistent field extractions (item names/quantities varying across repeated LLM samples) for human confirmation instead of relying on brittle token-probability confidence.
- Bucket check: confirmed.

**[Kadavath, Conerly, Askell, Henighan, Drain, Perez et al. (Anthropic), 2022]** Language Models (Mostly) Know What They Know. *arXiv:2207.05221*, 2022.
- Found: Shows LMs are well-calibrated on multiple-choice/true-false formats, and "self-evaluation" (asking a model to judge P(True) of its own answer, especially after seeing its own brainstormed alternatives) separates correct from incorrect answers, improving with scale.
- Supports: Provides the mechanistic basis for confidence-routed HITL — P(True)-style self-evaluation could gate which extracted fields are auto-committed to the ledger versus escalated to a human.
- Bucket check: confirmed.

**[Guo, Pleiss, Sun & Weinberger, 2017]** On Calibration of Modern Neural Networks. *ICML 2017 (PMLR 70)*, 2017.
- Found: Modern deep networks are systematically overconfident despite higher accuracy than older nets; temperature scaling (a single learned scalar) is nearly always the simplest, most effective post-hoc calibration fix, beating histogram binning, isotonic regression, and Platt scaling variants.
- Supports: A cheap, validated recipe for calibrating confidence scores from the extraction model so that HITL-routing thresholds are trustworthy rather than arbitrary.
- Bucket check: confirmed.

**[Manakul, Liusie & Gales, 2023]** SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models. *EMNLP 2023 Findings*, pp. 9004–9017.
- Found: Detects hallucination without external databases or token probabilities, by sampling multiple stochastic responses and measuring mutual consistency (BERTScore, QA-based, n-gram, NLI, LLM prompting). Outperforms grey-box uncertainty metrics on a manually annotated GPT-3 WikiBio dataset.
- Supports: A black-box self-verification layer usable for SmartDox's cloud-LLM fallback path (where token probabilities aren't exposed) — sample-consistency checks could complement arithmetic self-validation for non-numeric fields (item/vendor names).
- Bucket check: confirmed.

**[Ji, Yu, Xu, Lee, Ishii & Fung, 2023]** Towards Mitigating Hallucination in Large Language Models via Self-Reflection. *EMNLP 2023 Findings*, pp. 1827–1843.
- Found: Studies hallucination in medical generative QA, proposing an iterative "self-reflection" loop (generate → score factuality → refine → generate answer → score consistency → refine → check entailment) that reduces hallucination and improves consistency, validated by automatic metrics and human evaluation.
- Supports: A concrete generate-score-refine control-loop template for combining arithmetic self-validation with confidence-routed HITL — score extraction consistency against source text and arithmetic totals before auto-commit or human routing.
- Bucket check: confirmed.

---

## 4. Entity Resolution / Record Linkage / Fuzzy Matching

**[Papadakis, Skoutas, Thanos & Palpanas, 2020]** A Survey of Blocking and Filtering Techniques for Entity Resolution. *arXiv:1905.06167v4*, 2020.
- Found: A comprehensive survey unifying Blocking (clustering likely matches to avoid all-pairs comparison) and Filtering (similarity-join techniques) across non-learning, learning-based, and hybrid methods, plus parallelizations and a survey of open-source ER tools (JedAI, Magellan, LIMES).
- Supports: Directly informs how to pre-filter candidate item/product matches efficiently before applying lexical/embedding/learned-alias matching, important as a shop's ledger grows.
- Bucket check: confirmed.

**[Fellegi & Sunter, 1969]** A Theory for Record Linkage. *Journal of the American Statistical Association*, Vol. 64, No. 328, pp. 1183–1210, 1969.
- Found: Formal probabilistic model for record linkage; defines a link/non-link/possible-link decision rule from field-agreement likelihood ratios, proven optimal for fixed error rates.
- Supports: The foundational statistical theory behind all modern weighted/probabilistic matching — SmartDox's accept/reject/route-to-human decision for entity matches is a direct descendant, giving a principled basis for threshold-setting.
- Bucket check: confirmed.
- **CITATION FLAG:** This PDF is an OCR'd scan with visible artifacts (e.g., "IVAX P. FELLEGIANDALANB. SUNTEB" for "Ivan P. Fellegi and Alan B. Sunter"). It also has a **second, unrelated paper stapled to the end** ("Fiddling Around with Nonmatches and Mismatches" by Scheuren & Oh, apparently a 1970s–80s ASA Proceedings paper) — **do not conflate the two; cite Fellegi & Sunter separately if the second paper is used.**

**[Li, Li, Suhara, Doan & Tan, 2020/2021]** Deep Entity Matching with Pre-Trained Language Models. *Proceedings of the VLDB Endowment, Vol. 14, No. 1, pp. 50–60*, 2021 (arXiv:2004.00584v3, 2020).
- Found: Presents Ditto, fine-tuning pre-trained Transformers (BERT/DistilBERT/RoBERTa) for entity matching as sequence-pair classification, with domain-knowledge injection, summarization, and data augmentation pushing F1 up to 29% above prior SOTA with less labeled data; demonstrated at 789K×412K record scale (96.5% F1).
- Supports: Demonstrates how a fine-tuned LM matches noisy, heterogeneous product names purely from serialized text — the embedding/learned-alias half of SmartDox's matching strategy.
- Bucket check: confirmed.

**[Mudgal, Li, Rekatsinas, Doan, Park, Krishnan, Deep, Arcaute & Raghavendra, 2018]** Deep Learning for Entity Matching: A Design Space Exploration. *SIGMOD '18*, pp. 19–34, 2018.
- Found: Defines a design-space taxonomy of DL architectures for entity matching; shows DL is on par with classic learning-based EM on clean data but outperforms it by 6–33% F1 on textual and "dirty" (misaligned-attribute) data.
- Supports: The "dirty EM" findings directly inform SmartDox's OCR'd slip scenario, where fields are often misaligned (e.g., brand name landing in the item field) — DL-based matching that ignores attribute boundaries recovers accuracy lost to such misalignment.
- Bucket check: confirmed.

**[Ebraheem, Thirumuruganathan, Joty, Ouzzani & Tang, 2018]** Distributed Representations of Tuples for Entity Resolution. *Proceedings of the VLDB Endowment, Vol. 11, No. 11, pp. 1454–1467*, 2018.
- Found: Introduces DeepER — converts tuples into distributed vectors (via GloVe/LSTM composition), uses cosine similarity as match-classifier features, and proposes an LSH-based blocking scheme for scaling; strong results with limited labeled data, even cross-language and cross-domain.
- Supports: Essentially the blueprint for the "embedding" component of SmartDox's entity resolution, with an LSH-based blocking approach that scales without hand-tuned blocking keys — useful as a small shop's ledger grows.
- Bucket check: confirmed.

---

## 5. On-Device / Quantized LLM Deployment (llama.cpp, GGUF, edge inference)

**[Frantar, Ashkboos, Hoefler & Alistarh, 2023]** GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers. *ICLR 2023*, 2023.
- Found: One-shot weight quantization via approximate second-order (Hessian) error compensation, compressing LLMs to 3–4 bits/weight with negligible accuracy loss; quantizes OPT-175B in ~4 GPU-hours with 3.25–4.5x inference speedups.
- Supports: The foundational one-shot PTQ method underlying most llama.cpp/GGUF quantization schemes — justifies compressing a small extraction model to run on modest shop hardware with minimal accuracy loss.
- Bucket check: confirmed.

**[Dettmers, Lewis, Belkada & Zettlemoyer, 2022]** LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale. *NeurIPS 2022*, 2022.
- Found: Identifies a small number of "outlier" activation feature dimensions that cause quantization failure at scale; a vector-wise quantization + mixed-precision decomposition scheme achieves zero-degradation 8-bit inference up to 175B parameters, halving memory.
- Supports: Establishes the outlier-feature problem later quantization schemes (including GGUF) must handle, informing safe low-bit quantization choices for the on-device model.
- Bucket check: confirmed.

**[Xiao, Lin, Seznec, Wu, Demouth & Han, 2023]** SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models. *ICML 2023 (PMLR 202)*, 2023.
- Found: Migrates quantization difficulty from activations to weights via a per-channel smoothing transform, enabling accurate W8A8 quantization up to 530B parameters with up to 1.56x speedup and ~2x memory reduction.
- Supports: A practical technique for low-precision inference without accuracy loss, reinforcing feasibility of quantized small-model deployment on constrained shop hardware.
- Bucket check: confirmed.

**[Microsoft, 2024]** Phi-3 Technical Report: A Highly Capable Language Model Locally on Your Phone. *arXiv:2404.14219v4*, 2024.
- Found: phi-3-mini (3.8B params, 3.3T training tokens) matches quality of much larger models (Mixtral 8x7B, GPT-3.5); once 4-bit quantized (~1.8GB), runs natively offline on an iPhone 14 (A16 chip) at 12+ tokens/sec.
- Supports: A direct, concrete precedent for SmartDox's plan — a small quantized LM deployed fully on-device at usable inference speed, closely mirroring the intended llama.cpp/GGUF deployment.
- Bucket check: confirmed, strongest direct fit in this bucket.
- **CITATION FLAG:** No individual lead author distinguished — author field lists only "Microsoft," with ~90+ names in an appendix; arXiv preprint only, not peer-reviewed. (Typical for this kind of industry tech report, but worth noting for your citation style.)

**[Lin, Tang, Tang, Yang, Chen, Wang, Xiao, Dang, Gan & Han, 2024]** AWQ: Activation-aware Weight Quantization for On-Device LLM Compression and Acceleration. *7th MLSys Conference, 2024 (Best Paper Award)*.
- Found: Only ~1% of weight channels are "salient" (by activation magnitude, not weight magnitude); protecting them via per-channel scaling substantially reduces quantization error. The TinyChat inference system achieves 3–4x speedup over FP16, enabling Llama-2-70B on a Jetson Orin and 7B models on a Raspberry Pi 4.
- Supports: The single strongest fit in this bucket — explicitly cites and benchmarks against llama.cpp, targets on-device/edge deployment as its stated goal, and demonstrates exactly SmartDox's target deployment profile (resource-constrained shop hardware).
- Bucket check: confirmed — arguably the bucket's anchor paper.

---

## 6. Confidence-Threshold HITL Routing / Active Learning

*(Thinnest bucket at 3 papers — still adequate, but the one with least redundancy if a paper gets cut.)*

**[Wu, Xiao, Sun, Zhang, Ma & He, 2022]** A Survey of Human-in-the-Loop for Machine Learning. *arXiv:2108.00941v3 (cs.LG)*, 2022.
- Found: Classifies HITL work into data processing, model training/inference, and system-level applications; concludes confidence-based sample selection is the dominant technique for identifying "key samples" needing human intervention, though less established outside classification tasks.
- Supports: Confirms confidence/uncertainty-based sample selection as the standard mechanism for deciding which model outputs need human review — directly underpinning SmartDox's low-confidence-field routing design.
- Bucket check: confirmed.

**[Settles, 2009, updated 2010]** Active Learning Literature Survey. *Computer Sciences Technical Report 1648, University of Wisconsin–Madison*, 2009/2010.
- Found: The canonical AL survey — query scenarios, query-strategy frameworks (uncertainty sampling, query-by-committee, expected error/model change, density-weighted methods), theoretical/empirical evidence, and practical issues (noisy oracles, variable labeling costs, batch-mode querying).
- Supports: Provides the formal uncertainty-sampling framework (least-confidence, margin, entropy) SmartDox can adopt directly as its confidence metric for HITL routing decisions.
- Bucket check: confirmed — foundational reference for this bucket.

**[Margatina & Aletras, 2023]** On the Limitations of Simulating Active Learning. *Findings of ACL 2023*, pp. 4402–4419.
- Found: Argues most AL research is validated only via "simulation" on already-labeled datasets, introducing biases (artificially balanced seed data, no annotation-cost variability) that may explain why AL often fails to beat random sampling in deployed systems; gives guidelines for more trustworthy AL evaluation.
- Supports: A direct cautionary reference — warns that confidence-routing thresholds tuned on clean benchmark data may not transfer to real messy buy/sell slips, recommending evaluation with real annotation-cost/quality variability.
- Bucket check: confirmed (also weakly relevant to hallucination/calibration given its focus on evaluation validity).

---

## 7. Bangla/Bengali NLP

**[Bhattacharjee, Hasan, Ahmad, Samin, Islam, Iqbal, Rahman & Shahriyar, 2022]** BanglaBERT: Language Model Pretraining and Benchmarks for Low-Resource Language Understanding Evaluation in Bangla. *Findings of ACL: NAACL 2022*, 2022.
- Found: Introduces BanglaBERT (ELECTRA-based, pretrained on 27.5GB Bangla web text) and BanglishBERT (bilingual variant), plus the first Bangla Language Understanding Benchmark (sentiment, NLI, NER, QA); outperforms multilingual models (mBERT, XLM-R) while being far more compute/sample-efficient.
- Supports: A strong, efficient, publicly available pretrained Bangla encoder that could underlie NER/classification stages of slip-field extraction.
- Bucket check: confirmed; also touches schema-constrained extraction as a backbone-choice reference.

**[Bhattacharjee, Hasan, Ahmad & Shahriyar, 2023]** BanglaNLG and BanglaT5: Benchmarks and Resources for Evaluating Low-Resource Natural Language Generation in Bangla. *Findings of ACL: EACL 2023*, 2023.
- Found: Introduces a 6-task Bangla generation benchmark and BanglaT5 (T5-style, same 27.5GB corpus), which beats larger multilingual generation models (mT5, mBART-50, IndicBART) on most tasks while being smaller/faster.
- Supports: A candidate lightweight generative backbone for structured extraction from Bangla-English slips; its "Hallucinated Text" limitations section is directly relevant to the arithmetic self-validation design.
- Bucket check: confirmed; secondary relevance to schema-constrained extraction and hallucination/calibration.

**[Akil, Sultana, Bhattacharjee & Shahriyar, 2022]** BanglaParaphrase: A High-Quality Bangla Paraphrase Dataset. *AACL-IJCNLP 2022 (Vol. 2, Short Papers)*, 2022.
- Found: A synthetic ~466K-pair (later ~600K) Bangla paraphrase dataset via back-translation plus a multi-stage filtering pipeline; models trained on it beat IndicBART on quality metrics.
- Supports: Mainly useful as a data-augmentation resource — could generate paraphrase variants of shop vocabulary (item names, units) to improve lexical-matching robustness in entity resolution.
- Bucket check: **weak fit for SmartDox's core pipeline** — tangential; keep as a Bangla NLP resource but don't lean on it as a central citation.

**[Kabir, Islam, Laskar, Nayeem, Bari & Hoque, 2024]** BenLLM-Eval: A Comprehensive Evaluation into the Potentials and Pitfalls of Large Language Models on Bengali NLP. *LREC-COLING 2024*, 2024.
- Found: Zero-shot evaluates GPT-3.5, LLaMA-2-13b-chat, and Claude-2 across 7 Bengali NLP tasks against fine-tuned Bangla SOTA models; LLMs are competitive on some tasks but substantially worse on most, with documented failure modes including hallucination-like context deviation and non-compliant outputs.
- Supports: Direct evidence that general-purpose LLMs (candidates for the cloud-fallback tier) can't be trusted for zero-shot Bangla-English structured extraction without schema constraints and validation — motivates SmartDox's design.
- Bucket check: **suggest cross-listing (or moving) to the hallucination/calibration bucket** — this is fundamentally an LLM reliability/error-analysis study; it's Bangla-specific but its core contribution is about LLM failure modes, not Bangla NLP resources per se.

**[Hasan, Bhattacharjee, Islam, Samin, Li, Kang, Rahman & Shahriyar, 2021]** XL-Sum: Large-Scale Multilingual Abstractive Summarization for 44 Languages. *Findings of ACL-IJCNLP 2021*, 2021.
- Found: A 1M-sample, 44-language (including Bengali) abstractive summarization dataset from BBC, validated via human evaluation of faithfulness/hallucination and intrinsic metrics; fine-tuned mT5 achieves the first public Bengali summarization benchmark.
- Supports: Provides Bengali training/eval data reused by the other BUET papers here, and its faithfulness/hallucination evaluation protocol is a reusable template for SmartDox's self-validation design.
- Bucket check: confirmed; secondary relevance to hallucination/calibration.

---

## 8. Event-Sourced / Append-Only / Idempotent Ledger Design

**[Overeem, Spoor, Jansen & Brinkkemper, 2021]** An Empirical Characterization of Event Sourced Systems and Their Schema Evolution – Lessons from Industry. *Journal of Systems and Software* (also arXiv:2104.01146), 2021.
- Found: Grounded-theory interviews with 25 engineers across 19 production event-sourced systems; formalizes event/stream/store definitions, append/read operations with optimistic concurrency, and identifies five schema-evolution techniques and three degrees of immutability actually used in industry.
- Supports: Gives SmartDox a concrete, empirically-validated definition of append-only storage with sequence-number-based optimistic concurrency for idempotent writes, plus proven schema-evolution strategies for the inventory ledger.
- Bucket check: confirmed.

**[Helland, 2012]** Idempotence Is Not a Medical Condition. *Communications of the ACM*, Vol. 55, No. 5, 2012.
- Found: In loosely-coupled distributed messaging, delivery is only guaranteed "zero or more times," so every message-driven operation must be designed idempotent to tolerate retries and reordering.
- Supports: Directly motivates SmartDox's requirement that ledger-append operations be idempotent (e.g., via client-supplied transaction IDs) so a retried slip-confirmation never double-books inventory.
- Bucket check: confirmed.

**[Helland, 2015]** Immutability Changes Everything. *7th Biennial Conference on Innovative Data Systems Research (CIDR '15)*, 2015.
- Found: Surveys how immutable, identity-bearing data (append-only logs, versioned datasets, copy-on-write structures) underlies reliable, coordination-light distributed systems, now practical given cheap storage; notes trade-offs like write amplification.
- Supports: The architectural rationale for treating each confirmed slip as an immutable, uniquely-identified event appended to the ledger, enabling safe replay/recovery.
- Bucket check: confirmed.

**[Overeem, Spoor & Jansen, 2017]** The Dark Side of Event Sourcing: Managing Data Conversion. *IEEE SANER 2017*, Klagenfurt, Austria, 2017.
- Found: Defines a taxonomy of event-store upgrade operations and five upgrade techniques, scored against ISO/IEC 25010 quality attributes; distinguishes "technical immutability" (never altering events) from "functional immutability" (preserving business meaning while allowing transformation).
- Supports: A concrete playbook for evolving the ledger's event schema as new slip types/currencies are added without breaking the append-only guarantee.
- Bucket check: confirmed — companion/deep-dive to the Overeem et al. 2021 paper above.

---

## Summary of Flags for Your Attention

**Citation flags (verify before submission):**
1. *Handwritten Bangla Character Recognition Using...* — venue and year missing entirely from extractable text; likely ~2017–2019 based on self-citation, but unconfirmed.
2. *TrOCR* — confirm whether you're citing the arXiv preprint or the AAAI 2023 camera-ready version.
3. *A Theory for Record Linkage* (Fellegi & Sunter) — OCR-scan artifacts in author names, and a second unrelated paper is stapled to the end of the same PDF file. Cite carefully, don't conflate.
4. *Phi-3 Technical Report* — author field is just "Microsoft"; fine for an industry tech report but note the citation-style implication.

**Miscategorization / weak-fit flags:**
1. *TrOCR* (OCR bucket) — English/Latin-script only; weak fit for the "multilingual/code-mixed" framing specifically, though fine as general OCR background.
2. *BanglaParaphrase* (Bangla NLP bucket) — weak fit for SmartDox's core pipeline; tangential data-augmentation resource only.
3. *BenLLM-Eval* (Bangla NLP bucket) — suggest moving/cross-listing to the Hallucination Mitigation bucket; it's fundamentally an LLM failure-mode study.
4. *Let Me Speak Freely?* (Schema-Constrained bucket) — correctly placed, but it's counter-evidence/caution rather than support; make sure your write-up frames it that way.

**Cross-bucket relevance worth citing in more than one section:**
- *Enhancement of Bengali OCR...* → also relevant to On-Device/Quantized bucket (CPU quantization).
- *JSONSchemaBench* and *XGrammar* (Schema-Constrained bucket) → both explicitly benchmark on-device/llama.cpp scenarios, relevant to bucket 5.
- *LLM.int8()* → tangential relevance to hallucination/calibration (accuracy-preservation framing).
- *Margatina & Aletras* and *Ji et al. (Self-Reflection)* → both touch hallucination/calibration ↔ HITL boundary.

**File-hygiene note:** the Schema-Constrained folder contains a valid PDF missing its `.pdf` extension ("Let Me Speak Freely_ A Study on the Impact of") — rename it so future automated scans of the folder don't skip it.

**Bucket thinness:** No bucket is below the 2-paper threshold. Bucket 6 (HITL/Active Learning) is thinnest at 3 papers — consider adding one more (e.g., a paper specifically on cost-sensitive/threshold-tuned routing in production systems, rather than general AL theory) for redundancy, though it's not urgent.
