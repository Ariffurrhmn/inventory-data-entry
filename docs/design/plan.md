# Pre-Defence Presentation Plan

Audience: university panel/faculty. Goal: show what we're building and why. No implementation exists yet — this is a design defence, not a demo of working software.

---

## Slide list

1. **Title** — project name, team, supervisor.
2. **Problem statement** — paper documents, manual entry, the bottleneck. Plain language, one core example (e.g. "Coke" vs "Coca-Cola" is NOT our problem — see slide on scope).
3. **Motivation** — why this, why now (OCR + LLMs are mature enough; manual entry is still the norm).
4. **Objectives** — the 5 objectives from the report, one line each.
5. **Related work / gap** — 2-3 bullets on existing tools (cloud OCR platforms, invoice-extraction APIs, ERP platforms) and why none of them do this combination.
6. **System architecture** — Figure 2, walked through live.
7. **Pipeline detail** — Figure 4, the 6 modules.
8. **Worked example (clean case)** — fake invoice → JSON output. See `demo_worked_example.md`.
9. **Worked example (flagged case)** — same invoice, one misread field → `review_required: true`. This is the key "trust" moment — show the system catches its own mistakes without a human queue.
10. **What's explicitly out of scope** — no catalog matching, no human-in-the-loop, no on-device processing, no inventory ownership. State this before anyone asks.
11. **Data model** — Figure 7. One entity (`Submission`). Emphasize what's *not* there.
12. **Methodology** — 5-phase iterative lifecycle, Figure 1.
13. **Evaluation plan** — how we'll measure success once built (Chapter 4 framework: CER/WER, classification accuracy, schema-validity rate, silent-error rate).
14. **Open decisions** — the 6 decisions, and current defaults (cheapest OCR, cheapest top-10 LLM, provider JSON mode, log-probs-first confidence).
15. **Closing / Q&A** — contributions recap, thank you.

---

## What we have ready

- Full written report content (Ch. 1–3) to pull slide text from.
- All diagrams already built: Figures 1, 2, 4, 5, 6, 7, 8 (SVG + PNG, in `figures/`).
- A worked example with fake but schema-accurate input/output (`demo_worked_example.md`).
- Complex Engineering (WK/WP/EA) mapping, if the panel expects it.
- Clear list of open decisions with current defaults — no "we haven't thought about it" gaps.

## What we're still missing

- **Slide deck itself** — content exists in the report, but nothing is in presentation form yet (see UI/demo plan below for the visual work involved).
- **Rehearsed answers for scope-cut questions** — someone on the panel may have seen an earlier version of this project (it used to include item-standardization and a human-confirmation loop). Have a one-line answer ready: *"we scoped that out to keep the core recognition problem tight — reconciling item names is the consuming ERP's job."*

## Explicitly not doing (per team decision)

- No risk/limitations slide — decided this is more of a full-defence concern, skipped for pre-defence.
- No working prototype or live demo — nothing is implemented yet; the worked example replaces this.

---

## Next steps

1. Turn this outline into actual slides (see `ui_demo_plan.md` for how the visual/demo pieces get built).
2. Rehearse the worked-example walkthrough — it's the most concrete part of the talk and needs to feel smooth.
