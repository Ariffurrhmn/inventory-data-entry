# Staged dataset intake — 2026-10-19

User authorized reviewing the full ExpressExpense SRD release and a bounded English synthetic supplement. This scoped authorization resumes staged external intake only; other classifier/OCR experiments remain paused.

Completed: 200 SRD photographs and 40 Company Documents v2 PDFs, all individually reviewed for class eligibility on source-image contact pages. Accepted for staging: 49 receipt, 2 customer_copy, 20 purchase_order and 20 delivery_note (91 total). Held: 140 unresolved payment/language/copy/type cases. Excluded: 5 exact matches to the old corpus and 4 within-release visual derivatives. AI labels are not independently human verified.

Primary files: Dataset/intake/2026-10-19/README.md, accepted_manifest.csv, reviewed_records.jsonl, review.html and summary.json. Review actions and reasons cover all 240. Sources, hashes, synthetic status, license notices and pinned publisher revision are preserved. Raw OCR screening remains explicitly unreviewed; source embedded PDF text is separate. No new reference gold transcriptions were made for these additions.

Validation: all 240 source hashes and image decoding passed; 91 accepted image hashes are unique. The 144 protected files (existing labels/manifest/splits/results plus 140 reference JSONs) matched their before-intake hashes. No existing model was run or modified. Existing training corpus remains 140, with no new split assignments or merge.

Duplicate families: SRD 1041/1114 repeat 1034 (French La Source, held); 1063/1186 repeat accepted 1053 (Primo). Existing exact matches remain 1057,1073,1085,1164,1176. Perceptual comparison also returned the already visually rejected Chef Wang/CoCo similarity, which is not a duplicate. New customer-copy candidates are SRD 1100 (Duplicate) and 1117 (Customer Copy).

The 40 synthetic pages span four layouts (five per class/layout), but share one generator-family group and are training supplements only. Do not count their diversity as real supplier/photo holdout coverage. All final synthetic images use Poppler. An apparent omission in four overview previews prompted alternate rendering checks; stored-image comparisons did not establish source corruption.

Next meaningful work: human label/transcription audit, collect real English PO/delivery/challan and copy-marked layout diversity, then authorize/implement grouped merge and OCR/text experiments separately. No random image splitting; retain merchant/template/document-family relationships and old-corpus overlap links.
