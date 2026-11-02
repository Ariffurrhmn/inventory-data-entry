# File organization

See ../README.md for the folder-purpose table.

## Placement rules

- Shared project memory and session handoffs → Context/.
- Editable report, slide scripts, planning, worked examples, branding assets → docs/design/.
- Editable research logs → docs/research-logs/.
- Collection instructions → docs/data-collection/; meeting recordings → docs/meetings/.
- Prepared submission files → deliverables/; keep Report, Proposal, Signed, Deprecated distinctions.
- Reference papers and literature-review draft → research/literature/, retaining topic folders.
- Shared diagram sources and exports → figures/.
- Corpus and curated source documents → Dataset/; rejected examples remain in _excluded/.
- Entirely fabricated HTML/image/JSON corpus → synthetic_dataset/.
- Prompt/image/review/approval/print exchange → ChatGPT_Bridge/.
- Future application implementation → a clearly named app/ or services/ folder with its own setup instructions.

## Moves on 2026-10-19

| Old location | New location |
|---|---|
| Context/ (previous writing and supporting assets) | docs/design/ |
| Capstone Papers/ | research/literature/ |
| DOC's/ | docs/research-logs/ |
| complete files/ | deliverables/ |
| Document_Collection_Guide.pdf | docs/data-collection/Document_Collection_Guide.pdf |
| WhatsApp Audio 2026-07-24 at 12.39.00 PM.mp4 | docs/meetings/WhatsApp Audio 2026-07-24 at 12.39.00 PM.mp4 |

The common Context/ was then created with the shared notes. Empty existing supporting directories moved with docs/design/. Assistant-specific .claude/ was retained.

The CSV move map and original byte-size inventory support tracing and reversal. No originals were deleted or deduplicated. Text references using former root folder paths were updated where found; historical prose may still mention old names. Binary Office/PDF embedded links and external Google Drive links were not audited or rewritten. Retained figures/ remains the canonical shared asset folder; figure paths in prose are generally project-root references.

Image-linked reference transcriptions and their review artifacts belong in Dataset/annotations/. Keep unreviewed OCR drafts separate from reviewed reference JSONs there. Annotation tooling belongs in services/document_classifier/; shared handoff is Context/TRANSCRIPTIONS.md.

Authorized reviewed additions awaiting a future grouped merge belong in Dataset/intake/<date>/. Keep accepted, held and excluded manifests alongside unmodified source images/PDFs and licenses; maintain the original classifier corpus separately.

Versioned OCR/classifier experiments belong in services/document_classifier/runs/<run-name>/, with an adjacent service report and shared Context handoff. Fresh real documents awaiting independent final evaluation belong in Dataset/holdout_real_pending/ with manifest.csv; collection instructions belong in docs/data-collection/FRESH_HOLDOUT.md. Keep holdout material outside training and intake augmentation.

Versioned annotation editions belong in Dataset/annotations/versions/<version>/; correction audits and before/after records belong in Dataset/annotations/audits/<audit-name>/. Preserve the original references used for historical results. Current UTF-8 corrected edition: versions/utf8-v2/.

Annotation portal code, launcher, tests and preview belong in services/annotation_portal/. Real saved review revisions belong in Dataset/annotations/human_review/; server runtime logs and isolated browser QA data belong in services/annotation_portal/.runtime/. Portal saves must not overwrite canonical reference editions or frozen classifier labels/splits.

Versioned content-scope admission decisions, full/eligible manifests, screening sheets and validation readiness belong in Dataset/annotations/scope/<version>/. Dataset/annotations/scope/active.json selects the portal scope. Preserve historical corpus/splits and annotation versions. Current edition: printed-only-v1/.

The running classifier UI, shared inference code and launcher belong in services/document_classifier/. Trained printed models and immutable experiment evidence belong in its runs/printed_v1_* directories; active_text_model.json points to the selected pipeline. Local runtime logs remain in .runtime/. Current usage and model limitations: PRINTED_CLASSIFIER.md.

## Canonical classifier application — user-requested organization 2026-10-20

The top-level classifier/ folder supersedes services/document_classifier/ for new classifier work:
- classifier/app/: supervisor demo server and frontend.
- classifier/engine/: existing classifier source, derived data, all old/current models and versioned runs, retained OCR weights and historical reports.
- classifier/demo/: curated copies of existing validation images and recorded analyses; not a new benchmark.
- classifier/exports/: explicitly saved demo reports; not annotation truth/training data.
- classifier/docs/: setup/presentation guide, relocation inventories and demo QA.
- classifier/tests/: demo API checks.
- classifier/Open Demo.cmd: user-facing launcher (port8770).

Original Dataset/, annotation history and deliverables were not moved. Historical services/document_classifier/data/ is retained as immutable prepared-image compatibility assets so old annotation HTML/JSON continue resolving; engine/data/ is the canonical derived copy. Other old services/document_classifier paths map to classifier/engine. The old command launchers forward. Do not rerun generators to repair historical references. Shared Context/ remains the single source of assistant project memory.


Compatibility follow-up for the supervisor demo: also retained immutable legacy PSM3/sparse OCR JSON caches under services/document_classifier/runs/ so the already-running annotation portal can continue reading its cached paths without a forced restart. Canonical copies remain in classifier/engine/runs/. Migration evidence is organized in classifier/docs/migration/; QA reports in classifier/docs/qa/. Presentation guide and final preview/validation remain directly in classifier/docs/.


## Downstream prototype — 2026-10-24

services/document_pipeline/ contains the downstream local gateway, schema/verifier, capture page, launchers, tests and reproduction scripts. experiments/2026-10-24/ preserves actual sub-agent inputs/outputs/prompts/provenance and ocr_regions/ derived diagnostic crops/OCR. validation/2026-10-24/ holds software/live/browser/policy evidence. .runtime/ holds local SQLite submissions and owned-server logs/PID; not training data. Shared handoffs remain in Context/; canonical classifier, annotations and raw corpus stay unchanged.

Downstream localization/evaluation follow-up: reusable localization, region-evidence adapter, backend probe, separate field review CLI/tests and FIELD_REVIEW.md live directly in services/document_pipeline/. experiments/2026-10-24/automatic_localization/ preserves all method attempts and authoritative run6 image/OCR/source audits; downstream_followup/ preserves actual blinded prompts/responses/comparison, hardware probe, isolated live smoke and review-preparation/ AI candidates plus blank forms. Actual future field-review revisions belong in a separate services/document_pipeline/.runtime/field_reviews.sqlite3; do not write them into the annotation portal database. Opt-in runtime derived region audits live beside the selected submissions database under regions/. No automatic adoption into Dataset/annotations/ or training.

## Supervisor Showcase — 2026-10-29

supervisor_showcase/ holds the supervisor-facing presentation app and its meeting records: server.py (reads classifier/engine, never copies models), web/, data/showcase.json (all displayed facts with sources), launchers, tests/, .runtime/ logs and meeting-notes/ (saved supervisor decisions; not training data or ground truth). classifier/app remains the earlier Document Lab demo. Copy scope-changing supervisor decisions into Context/DECISIONS.md.
