# UI & Demo Build Plan

No working software. Everything below is presentation material — mockups and illustrations, not code.

---

## What we're building for the demo

### 1. Sample document image
- Either a real (anonymized) invoice/receipt from a shop, or a stock/sample image found online.
- Pick one clean printed example (purchase order) as the primary walkthrough.
- Optional second image: a thermal receipt or handwritten note, to acknowledge the harder cases live if there's time.

### 2. Pipeline walkthrough slides
- Take Figure 4 (the module diagram, already built in `figures/fig4_pipeline.png`) and turn it into a **build sequence** — same diagram shown 6 times, each time highlighting the next module box.
- Under each highlighted box, show the fake intermediate output for that stage (OCR tokens, document-type label, extracted fields, etc.) — pulled from `demo_worked_example.md`.
- This can be done as PowerPoint animation (fade-in highlight) or as 6 separate static slides — simplest is 6 static slides, less can go wrong live.

### 3. Mock JSON output slide(s)
- Two side-by-side JSON blocks from `demo_worked_example.md`: clean case vs. flagged case.
- Highlight (color/box) the `arithmetic_check` and `review_required` fields — that's the one thing worth making visually loud.

### 4. Mobile app wireframe (optional, if time allows)
- Not a working app — 2-3 static mockup screens:
  - Camera/capture screen
  - "Retake — image too blurry" prompt screen
  - Upload confirmation screen
- Build these as simple boxes/text in PowerPoint or Figma. No need for polish — a rough wireframe communicates "this is the plan," not "this is built."
- Skip if time is tight — this is the lowest-priority visual since the JSON/pipeline slides carry more weight for a panel evaluating the *system design*, not the *app UI*.

---

## Tools

- **Slides:** PowerPoint or Google Slides — whatever the team already uses for BUBT submissions.
- **Diagrams:** already built (SVG in `figures/`, PNG versions ready to paste directly into slides).
- **Mockup screens (if built):** Figma, or just PowerPoint shapes — doesn't need a real design tool.
- **JSON snippets:** copy directly from `demo_worked_example.md`, format with a monospace font on the slide, syntax-color manually if desired (green for `"passed"`/`false`, red/orange for `"failed"`/`true`).

---

## Build order

1. Pick/prepare the sample document image.
2. Build the 6-step pipeline walkthrough slides using the existing Figure 4 diagram + fake intermediate data.
3. Build the two JSON output slides (clean vs. flagged).
4. (Optional, lowest priority) mobile wireframe screens.
5. Assemble into the full deck per `plan.md`'s slide list.
6. Rehearse the walkthrough end-to-end — this is the part most likely to get questions.

---

## Option: interactive version instead of static slides

The pipeline walkthrough and JSON reveal (items 2-3 above) could be built as a **clickable interactive page** instead of static slides — step through the 6 modules live, watch the fake data populate at each stage, animate the clean-vs-flagged JSON diff.

**Tradeoffs:**
- More engaging live than flipping static images.
- Runs in a browser, not as a `.pptx` — still want static PNG exports as a fallback in case of projector/wifi issues on the day.
- Wouldn't replace the whole deck — title, problem statement, literature, etc. stay as normal slides. This would only cover the pipeline-walkthrough + JSON-reveal portion.

**Status:** not built. Decide closer to the presentation date whether it's worth it.

## What NOT to build

- No working code, no running app, no live API calls.
- No real user data — everything is a hand-built, clearly-labeled illustrative example.
- No attempt to fake a "real" demo — if asked, the honest answer is "this is a mockup; the report's evaluation plan (Chapter 4 framework) is how we'll measure the real thing once built."
