# Automated Inventory Data Entry through Intelligent Character and Document Structure Recognition

A BUBT CSE capstone (CSE 498A / 498B) on turning paper business documents into structured, checkable data for inventory and ERP systems.

Small shops still key purchase orders, receipts and delivery notes into their inventory systems by hand. This project designs a document-digitisation gateway to take over that step. A photograph or scan is read with OCR and classified by document type. A language model then extracts the fields into a fixed JSON schema, and arithmetic checks flag anything that does not add up.

- **Supervisor:** Md. Mijanur Rahman
- **Repository:** <https://github.com/Ariffurrhmn/inventory-data-entry>

---

## Source of truth

> **The signed Chapters 1–3 report is the authoritative statement of the project's scope, design and evaluation plan.**

| File | What it is |
|---|---|
| [`deliverables/Signed/Capstone_Report_Ch1_3.pdf`](deliverables/Signed/Capstone_Report_Ch1_3.pdf) | The signed copy handed to the supervisor |
| [`deliverables/Report/Capstone_Report_Ch1_3.pdf`](deliverables/Report/Capstone_Report_Ch1_3.pdf) | Unsigned PDF of the same report |
| [`deliverables/Report/Capstone_Report_Ch1_3.docx`](deliverables/Report/Capstone_Report_Ch1_3.docx) | Word source of the report |
| [`deliverables/Signed/Proposal.pdf`](deliverables/Signed/Proposal.pdf) | Signed project proposal |

Everything under [`deliverables/`](deliverables/) was copied into this repository **without modification**. The files are byte-identical to the originals. [`.gitattributes`](.gitattributes) disables line-ending conversion so no checkout can alter them. Do not edit, re-export or "tidy" anything in that folder. If the report changes, add a new, clearly named file next to it.

`docs/design/` also holds working drafts, such as the Markdown draft of Chapters 1–3, slide scripts and plans. These are editable working material and **not** the submitted report.

---

## Where the project stands

The report describes a mobile-to-cloud gateway covering both printed and handwritten documents. The implementation so far is narrower, and the notes in [`Context/`](Context/) record each narrowing as a decision:

| Area | Report (design) | As built so far |
|---|---|---|
| Documents | Printed and handwritten | English **printed** documents only (user decision, 2026-10-20) |
| Classes | PO, receipt, delivery note, customer copy | The same four: `purchase_order`, `receipt`, `delivery_note`, `customer_copy` |
| Capture | Mobile app | Local web upload (no mobile app) |
| Processing | Cloud OCR + cloud LLM | Local Tesseract OCR; extraction is a manual handoff to an AI sub-agent |
| API | Stateless, idempotent JSON API | Local gateway with idempotent submissions and a demo consumer |

Measured results, with their limits:

- **Document classifier (`printed_v3_explainable`).** An explainable hybrid of corrected OCR, versioned printed-document rules and TF-IDF + ComplementNB. It scored **23/25 (92 %)** on the adaptive *development* validation set. The grouped training check scored 146/150 (97.3 %). Neither figure is independent final accuracy, because the rules and model were tuned against those sets.
- **Downstream pipeline.** OCR, classification, extraction-JSON handoff, `Decimal` arithmetic verification and persisted submissions pass **49 automated checks**. These are software checks, not extraction accuracy. No independent extraction accuracy is claimed.
- **Not done yet:**
  - There is no independent real-document test set (the holdout manifest is empty).
  - There is no unattended LLM backend.
  - There is no mobile app or cloud deployment.
  - Human-verified field truth does not exist.

[`Context/STATUS.md`](Context/STATUS.md) is the dated, detailed log. When it disagrees with this summary, it wins. Synthetic or hand-built examples are never presented as measured results.

---

## How it works

```
Photo / scan ─► OCR (text + boxes) ─► 4-class document classifier
                                              │
                                              ▼
              JSON for the ERP ◄─ arithmetic checks ◄─ schema-constrained extraction
                                  + review_required flag
```

1. **OCR** reads the text and word boxes (Tesseract locally).
2. **Classification** picks one of four types. Each prediction comes with a trace of the rules and n-grams that produced it.
3. **Extraction** turns the text into line items under a fixed JSON schema. Today this is a handoff to an AI sub-agent. The prompt is exported, and the JSON it returns is imported.
4. **Verification** checks quantity × unit price against line totals, and line totals against document totals. Anything unverifiable sets `review_required`. Consistently wrong values can still pass arithmetic checks, so a pass is not proof of correctness.
5. **Submission** keeps a record per document with a unique key. Replaying the same key returns the same result, and reusing a key with changed content is a conflict.

Figures for the architecture, pipeline, data model and schedule are in [`figures/`](figures/) (SVG sources and PNG exports).

---

## Repository layout

```
.
├── deliverables/           Submitted work, UNMODIFIED (report, proposal, slides, research log, signed copies)
├── docs/
│   ├── design/             Editable report draft, slide scripts, plans, SWOT, viva prep
│   ├── research-logs/      Editable research logs
│   ├── data-collection/    Document collection guide, holdout collection protocol
│   └── LARGE_FILES.md      Files kept out of git (≥ 10 MB) and where to get them on Drive
├── research/
│   ├── literature/         Reference papers grouped by topic
│   └── datasets/           Public-dataset search, source assessment and provenance CSVs
├── figures/                Diagram sources (SVG) and PNG exports
├── Dataset/                Collected/curated corpus, annotations, intake batches, holdout area
├── synthetic_dataset/      Fabricated documents (HTML, JSON ground truth, generators)
├── ChatGPT_Bridge/         Prompts, generated images, review history and answer keys for the synthetic set
├── classifier/             Four-class classifier: engine, demo app ("Document Lab"), tests
├── services/
│   ├── document_pipeline/  Downstream gateway: OCR → classify → extract → verify → submit
│   ├── annotation_portal/  Local app for reviewing transcriptions
│   └── document_classifier/  Legacy location, kept so historical paths still resolve
├── supervisor_showcase/    Supervisor-meeting app and saved meeting decisions
├── Context/                Shared project memory: status, decisions, handoffs
├── AGENTS.md / CLAUDE.md   Entry points for AI coding assistants
└── .gitignore / .gitattributes
```

Rules for where new files go are in [`Context/ORGANIZATION.md`](Context/ORGANIZATION.md). Paths inside the notes, manifests and launchers refer to this layout. Moving folders will break them, so check references first.

---

## Running things

The launchers are written for **Windows** (`.cmd` / PowerShell). The Python code itself is portable.

**Requirements:** Python 3.12–3.14 and Tesseract OCR. The HEIC photographs additionally need `pillow-heif`.

**One-time setup**

```powershell
./classifier/setup.ps1
```

This creates a virtual environment and writes `classifier/engine/runtime.local.json`. That file holds a machine-specific interpreter path and is deliberately **not** committed. Dependencies are listed in `classifier/requirements-demo.txt` and, pinned, in `classifier/engine/requirements-lock.txt`.

| App | Launch | URL |
|---|---|---|
| Document Lab (classifier demo) | `classifier/Open Demo.cmd` | <http://127.0.0.1:8770> |
| Supervisor showcase | `supervisor_showcase/Open Showcase.cmd` | <http://127.0.0.1:8780> |
| Document pipeline (gateway) | `services/document_pipeline/Open Pipeline.cmd` | <http://127.0.0.1:8772> |
| Annotation portal | `services/annotation_portal/Open Portal.cmd` | <http://127.0.0.1:8765> |

Add `-RegionOcr` to `services/document_pipeline/start.ps1` to enable automatic table-cell OCR.

Each component has its own README with details: [`classifier/`](classifier/README.md), [`services/document_pipeline/`](services/document_pipeline/README.md), [`services/annotation_portal/`](services/annotation_portal/README.md), [`supervisor_showcase/`](supervisor_showcase/README.md).

**Tests:** each component keeps its tests beside its code: `classifier/tests/`, `classifier/engine/test_*.py`, `services/document_pipeline/test_*.py`, `services/annotation_portal/test_portal.py` and `supervisor_showcase/tests/`. Some historical engine tests need PyTorch, which is not part of the demo requirements.

---

## Data

| Source | Location | Notes |
|---|---|---|
| Curated corpus (140 images used) | `Dataset/{Purchase_Order,Receipt,Delivery_Note,Customer_Copy}` | Fixed split 86 / 26 / 28. Excluded samples stay in `_excluded/`. |
| Phone photos of printed synthetic documents | `Dataset/Dataset-2/` | 54 HEIC files (21 PO, 24 delivery notes, 9 customer copies). These are synthetic documents, not real transactions. |
| Reference transcriptions | `Dataset/annotations/` | AI-assisted drafts, `human_verified=false` throughout. Versioned editions (`utf8-v2`) and scope definitions (`printed-only-v1`). |
| Reviewed external intake | `Dataset/intake/2026-10-19/` | 91 accepted additions (ExpressExpense SRD under MIT; Company Documents v2 under Apache-2.0). Not merged into the training corpus. |
| External candidates | `Dataset/external_candidates/` | Provenance notes for every source. Samples whose redistribution rights are unresolved are not published here. |
| Synthetic documents | `synthetic_dataset/` | 120 fabricated examples, 30 per class. |

Do not regenerate datasets or bridge prompts just to look at them. The generators can overwrite files. Source licences and attributions are in [`research/datasets/sources.csv`](research/datasets/sources.csv) and in the licence files next to each source.

---

## Large files

Files of 10 MB or more are not stored in git (the signed report is the exception and is included). That covers some experiment checkpoints, a few reference papers, the Tesseract language data and the meeting recording. They live in the project's shared Google Drive folder. [`docs/LARGE_FILES.md`](docs/LARGE_FILES.md) lists each one with its path and where to put it.

---

## Working on the project

- Read [`Context/README.md`](Context/README.md) → [`PROJECT.md`](Context/PROJECT.md) → [`STATUS.md`](Context/STATUS.md) → [`DECISIONS.md`](Context/DECISIONS.md) before starting.
- After meaningful work, add a dated entry to `Context/STATUS.md`. Record scope or design decisions in `Context/DECISIONS.md`.
- Keep raw datasets, ground truth, review history, signed documents and older deliverables intact. Keep synthetic and real evaluation data separate.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `data:`, `chore:`).

## Acknowledgements and licences

Third-party datasets keep their own licences (CC-BY-4.0, MIT and Apache-2.0 notices are stored beside the data). Literature PDFs in `research/literature/` belong to their authors and are kept for reference only.

No licence has been chosen for the project's own code and documents yet. Until one is added, all rights are reserved by the authors.
