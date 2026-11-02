# CSE 498B capstone plan — v1, 2026-10-30

Living plan. When progress is reported, update this file (mark task IDs done, move dates) instead of starting over. Facts come from Context/ (PROJECT, STATUS, DECISIONS) and docs/design/capstone_readiness_roadmap_2026-10-20.md. Anything marked ASSUMPTION is a guess to confirm.

## A. Summary and success criteria

"Automated Inventory Data Entry through Intelligent Character and Document Structure Recognition" (BUBT CSE, supervisor Md. Mijanur Rahman). CSE 498A is done: proposal and Ch. 1–3 report are signed. In CSE 498B the project is in the building stage. The explainable four-class printed-document classifier is finished (23/25 on adaptive development validation, local demo and supervisor showcase working). A local downstream gateway exists (OCR → classifier → extraction JSON handoff → Decimal arithmetic verification → idempotent submissions), but extraction is not unattended (no free local LLM backend fits this PC), there is no independent real-document test set (holdout manifest has 0 rows), and the final report chapters for implementation and results are not written.

The remaining work is mostly evidence and writing. No new features are planned.

Success means:
1. The supervisor confirms that the as-built scope (printed English only, local gateway, semi-automated extraction) is acceptable, or names what must be added.
2. The system is frozen and runs from cold on the defense laptop, with a backup video.
3. The classifier is evaluated once on at least 40 new real printed documents, collected and labeled without looking at predictions, with a confusion matrix and error analysis.
4. The final report is submitted on time: Ch. 1–3 revised to match what was built, plus implementation, results, discussion and conclusion.
5. The defense is rehearsed twice and shows a clean case, a flagged case, an honest failure and a duplicate submission.

## B. Assumptions and open questions

| # | Item | Status |
|---|---|---|
| 1 | Final report submission **Tue 15 Dec 2026**, defense **Tue 22 Dec 2026** | ASSUMPTION — confirm in A1 |
| 2 | Mid-review / progress presentation around **Thu 19 Nov 2026** | ASSUMPTION — confirm in A1 |
| 3 | Proposal deadline: already met (signed proposal and Ch. 1–3 report in deliverables/Signed) | From files |
| 4 | You have 5–8 h/week (about 6.5 planned). Teammates can give about 2–3 h/week for document collection, labeling and slide formatting | Hours: you said. Teammate hours: ASSUMPTION |
| 5 | A local demo is acceptable (phone photo or upload → local gateway). No native mobile app or cloud deployment | ASSUMPTION — confirm in A2. This is the biggest scope risk because the Ch. 1–3 report promised mobile-to-cloud |
| 6 | No paid APIs (existing decision, 2026-10-24). Final extraction stays the recorded semi-automated handoff unless the supervisor requires unattended extraction | From DECISIONS + ASSUMPTION |
| 7 | Final report = revised Ch. 1–3 plus Ch. 4 Implementation, Ch. 5 Results and Evaluation, Ch. 6 Conclusion, in the BUBT template | ASSUMPTION — confirm template/rubric in A1 |
| 8 | Rubric / marking scheme | Unknown — ask in A1 |
| 9 | Holdout target lowered from 80 to 40 documents (10 per class), with 20 as the minimum to still report | Proposal — confirm in A2 |

Questions to bring to the supervisor (A2): exact dates and format of the mid-review and defense; is a local demo enough, or is cloud/mobile required; is semi-automated extraction acceptable; is 40 real documents enough for the final evaluation; which report template and chapter structure to use.

## C. Phases, milestones and target dates (worked backwards from 15 Dec)

| Phase | Window | Milestone (date) |
|---|---|---|
| A. Align scope and dates | 31 Oct – 6 Nov | **M0 Fri 6 Nov**: dates, template and scope confirmed; teammates collecting documents |
| B. Real data and ground truth | 2 Nov – 27 Nov | **M2 Fri 27 Nov**: holdout closed (≥40 docs), duplicates checked, blind labels done |
| C. System freeze | 2 Nov – 20 Nov | **M1 Thu 19 Nov**: end-to-end demo frozen, hashes recorded, mid-review given |
| D. Evaluation (run once) | 28 Nov – 4 Dec | **M3 Fri 4 Dec**: holdout results, confusion matrix, error analysis, figures |
| E. Thesis writing | 7 Nov – 15 Dec | **Fri 4 Dec**: Ch. 1–4 to supervisor. **Wed 9 Dec**: full draft to supervisor. **M5 Tue 15 Dec**: submit |
| F. Defense prep | 10 Dec – 22 Dec | **M6 Tue 22 Dec**: defense |

Literature review and requirements/design were done in 498A (Ch. 2–3). In 498B they only need revising (E1, E1b), not redoing.

## D. Task table

Est. min is your own time unless the task says (teammate).

| ID | Phase | Task | Done when | Est. min | Priority | Depends on |
|---|---|---|---|---|---|---|
| A1 | A | Ask supervisor/department for 498B dates, mid-review format, report template and rubric | Dates and template written into Context/DECISIONS.md | 30 | 1 | — |
| A2 | A | Hold supervisor meeting with supervisor_showcase; ask the five scope questions in B | Meeting-notes file saved; scope decisions copied into DECISIONS.md | 60 | 1 | A1 |
| A3 | A | Brief teammates; assign document collection, blind labeling, slide formatting | Each teammate has a written list with due dates | 30 | 1 | — |
| A4 | A | Re-date this plan once real deadlines are known | Section C uses confirmed dates | 30 | 1 | A1 |
| B1 | B | Lower holdout target to 40 (10/class) and add consent/permission note in docs/data-collection/FRESH_HOLDOUT.md | Guide updated; teammates have it | 30 | 1 | A2 |
| B2 | B | (teammate) Collect first 20 real printed documents from ≥3 businesses | 20 rows in Dataset/holdout_real_pending/manifest.csv with source and permission | 120 | 1 | B1 |
| B3 | B | (teammate) Collect next 20, focused on customer copies and real delivery notes | 40 rows, ≥8 per class | 120 | 1 | B2 |
| B4 | B | Check holdout for duplicates/overlap with training and intake data | Audit file shows 0 hash/near duplicates, or the duplicates are removed | 45 | 1 | B3 |
| B5 | B | (teammate) Blind-label holdout classes without running the classifier; you spot-check 10 | Manifest has a label and labeler for every row | 60 | 1 | B3 |
| B6 | B | Create independent field truth for 10 holdout documents with field_review.py | 10 attested human reviews saved in .runtime/field_reviews.sqlite3 | 120 | 2 | B5, C3 |
| B7 | B | Field truth for 10 more documents | 20 attested reviews | 120 | 3 | B6 |
| C1 | C | Decide final extraction mode (default: semi-automated handoff; free-tier API only if required) | Decision and reason in DECISIONS.md | 45 | 1 | A2 |
| C2 | C | Run one end-to-end walkthrough on 4 docs (clean, flagged, failure, duplicate) on the D: runtime; fix only blocking bugs | Walkthrough record saved under services/document_pipeline/validation/ | 120 | 1 | C1 |
| C3 | C | Freeze model, OCR, rules, schema and verification settings | Freeze manifest with file hashes saved; code changes stop | 45 | 1 | C2 |
| C4 | C | Write a one-page setup guide and start the demo from cold on the defense laptop | Showcase and pipeline both run on that laptop | 90 | 1 | C3 |
| C5 | C | Spike free-tier hosted LLM for unattended extraction | 5 docs extracted automatically and verified | 120 | 3 | C1 |
| C6 | C | Cloud deploy or native mobile capture | Only if supervisor makes it mandatory | 600+ | 3 | A2 |
| S1 | A | Prepare and give mid-review (showcase + 3 status slides: done, frozen, evaluation plan) | Mid-review delivered; feedback noted in meeting-notes/ | 90 | 1 | C2 |
| S2 | E | Send supervisor a results summary with Ch. 1–4 | Email sent; reply logged | 30 | 1 | D5, E4 |
| D1 | D | Write the evaluation protocol before running anything (metrics, denominators, what will be reported) | Dated protocol file saved next to the freeze manifest | 60 | 1 | C3 |
| D2 | D | Run the frozen classifier once on the holdout | Predictions, accuracy, macro-F1 and confusion matrix saved | 60 | 1 | B4, B5, D1 |
| D3 | D | Run extraction and verification on the field-truth subset | Field accuracy and flagged/unflagged wrong-field counts with denominators | 120 | 2 | B6, D1 |
| D4 | D | Error analysis: categorize every holdout miss (OCR, heading, copy-stamp, class overlap) | Table of misses with causes | 60 | 1 | D2 |
| D5 | D | Make result figures: confusion matrix, development-vs-holdout, model history, latency | PNGs in figures/ | 90 | 1 | D2 |
| D6 | D | Ablation on holdout: rules-only vs learned-only vs hybrid | Three-row table | 60 | 3 | D2 |
| E0 | E | Set up final report file in the BUBT template with chapter skeleton | Document with all headings exists | 60 | 1 | A1 |
| E1 | E | Revise Ch. 1–3 to the as-built scope (printed-only, local hybrid, mobile/cloud wording); verify the flagged LayoutLM/Donut citations | Ch. 1–3 text matches DECISIONS.md; citation note removed | 120 | 1 | A2, E0 |
| E1b | E | Add 3–5 papers on document classification and explainability to the literature review | New subsection with citations | 90 | 2 | E1 |
| E2 | E | Write Ch. 4 part 1: OCR and explainable classifier (from EXPLAINABLE_CLASSIFIER.md) | Section drafted with architecture figure | 120 | 1 | E0 |
| E3 | E | Write Ch. 4 part 2: gateway, schema, verification, table localization | Section drafted | 120 | 1 | C2, E0 |
| E4 | E | Write Ch. 5 part 1: data, splits and development results with their caveats | Section drafted | 90 | 1 | E0 |
| E5 | E | Write Ch. 5 part 2: holdout results and error analysis | Section drafted with D5 figures | 120 | 1 | D4, D5 |
| E6 | E | Write discussion, limitations, future work and conclusion | Ch. 6 drafted | 90 | 1 | E5 |
| E7 | E | Abstract, Gantt chart, appendix, references and format pass | Report compiles to PDF with no placeholders | 120 | 1 | E6 |
| E8 | E | Send full draft to supervisor; apply feedback; submit | Final PDF submitted | 120 | 1 | E7 |
| F1 | F | Build defense slides (reuse showcase pages and D5 figures) | Deck complete, about 15 slides | 120 | 1 | D5, E5 |
| F2 | F | Record a backup demo video of the four-case walkthrough | MP4 saved locally and on Drive | 60 | 1 | C4 |
| F3 | F | Update Viva_Prep with likely questions (scope change, 92% caveat, no LLM backend) | Q&A list with answers | 60 | 2 | E6 |
| F4 | F | Two timed rehearsals with the team | Both done, under the time limit | 120 | 1 | F1 |
| F5 | F | Defense-day checklist (laptop, offline run, runtime path, video, adapters) | Checklist ticked the day before | 30 | 1 | F2 |

Totals for your own time: priority 1 ≈ 2,205 min (37 h); priority 2 ≈ 390 min (6.5 h); priority 3 is optional. Teammates: about 300 min (5 h) of collection and labeling, split between them.

**Critical path:** A1 → A2 → B1 → B2 → B3 → B5/B4 → D2 → D4 → E5 → E6 → E7 → E8 (submit) → F1 → F4 (defense). C2 → C3 → D1 must also finish before D2. Real-document collection is the longest step and depends on outside businesses, so it starts in week 1.

**Riskiest unknowns:** real deadlines; whether the supervisor expects the mobile/cloud/unattended-LLM system from the 498A report; how fast teammates can get real documents; whether the classifier holds up on real data (it may score well below 92%, and that result is still reportable).

**Cut order if behind:** (1) all priority 3 work: C5, C6, D6, B7. (2) D3/B6 field-level extraction accuracy: present extraction as 3–4 worked case studies instead. (3) E1b literature additions and F3 (fold Q&A into rehearsal). (4) Shrink holdout to 20 documents (5/class) and state the wide uncertainty. Never cut: freeze before evaluating, running the holdout only once, the backup video, or the Ch. 1–3 scope revision.

## E. Top 3 risks

1. **Scope mismatch with the signed 498A report** (it promised a mobile app, a cloud LLM and confidence scoring). *Reduce:* confirm in A2 this week; add an "as proposed vs as built, and why" table to Ch. 3/4; present the change as an evidence-based engineering decision (no paid APIs, local hardware limits, printed-only scope). If the supervisor insists on cloud/mobile, cut P2 items and re-plan right away.
2. **Real holdout documents arrive late or not at all** (0 collected today). *Reduce:* teammates start this week with a lowered target (40), go/no-go on Fri 20 Nov (≥20 in hand), hard close Fri 27 Nov. Fallback: report development results plus whatever real documents exist, with honest denominators. Never tune on holdout documents.
3. **Too little writing time, and a fragile demo runtime** (≈37 h of must-do work at 5–8 h/week; the venv was already wiped once on 29 Oct and C: is low on space). *Reduce:* start writing in week 2 from the existing handoff docs (EXPLAINABLE_CLASSIFIER.md, document_pipeline README, the 24 Oct progress report already hold most of Ch. 4); stop changing code on 20 Nov; test on the defense laptop (C4); record the backup video (F2); keep 2 GB+ free on the demo drive.

## F. This week (Sat 31 Oct – Fri 6 Nov, ≈6.5 h)

1. A1 — ask for dates, template and rubric (30)
2. A3 — brief teammates; they start collecting documents now (30)
3. A2 — supervisor meeting with the showcase and the five scope questions (60)
4. B1 — lower the holdout target and add the consent note (30)
5. C1 — decide the final extraction mode (45)
6. E0 — set up the report skeleton in the BUBT template (60)
7. C2 — end-to-end four-case walkthrough on the current runtime (120)
8. A4 — if dates arrive, re-date this plan (30)

## G. Weekly hours and feasibility

| Week | Dates | Your planned work | ≈ hours |
|---|---|---|---|
| 1 | 31 Oct – 6 Nov | A1, A2, A3, B1, C1, E0, C2 | 6.3 |
| 2 | 7 – 13 Nov | C3, C4, E1, A4 | 4.8 (+E2 start if time) |
| 3 | 14 – 20 Nov | S1 mid-review, E2, D1, E3 | 6.5 |
| 4 | 21 – 27 Nov | B4, E4, E1b, B6 | 5.8 |
| 5 | 28 Nov – 4 Dec | D2, D4, D5, E5, S2 (+D3 if time) | 6.0 |
| 6 | 5 – 11 Dec | E6, E7, F2, E8 part 1 (draft out Wed 9 Dec) | 5.5 |
| 7 | 12 – 15 Dec | E8 part 2 (feedback, submit Tue 15 Dec); F1 start | 2 (+ buffer) |
| 8 | 16 – 22 Dec | F1, F3, F4, F5, defense | 4.5 |

**Verdict:** Realistic but tight at about 6.5 h/week, only if all of these hold: (a) the deadline is no earlier than mid-December, (b) the supervisor accepts a local demo with semi-automated extraction, (c) teammates bring in real documents by 27 Nov, and (d) no new features are built. At 5 h/week, priority 2 work must be cut. If the supervisor requires a native app or cloud deployment, or the deadline is early December, the plan is **not** realistic as written; then cut to the classifier evaluation plus gateway case studies and re-plan immediately.

## Progress log

- 2026-10-30: v1 created. Nothing started yet.
