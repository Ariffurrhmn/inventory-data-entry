# Reviewed external intake — 2026-10-19

This is a separate staging area. None of these files has been merged into the existing classifier corpus, and no train/validation/test assignments have been created.

## Results

Reviewed 240 documents: all 200 images in the ExpressExpense SRD archive, plus 20 English synthetic purchase orders and 20 English synthetic packing slips from Company Documents v2.

| Outcome | Count |
|---|---:|
| Accepted as staged receipt candidates | 49 |
| Accepted as staged customer-copy candidates | 2 |
| Accepted synthetic purchase orders | 20 |
| Accepted synthetic delivery notes (packing slips) | 20 |
| Held pending language/payment/type/quality clarification | 140 |
| Excluded: exact duplicates of existing corpus images | 5 |
| Excluded: repeated documents within this intake | 4 |
| Total reviewed | 240 |

The 91 accepted additions have assistant visual labels, not independent human verification. This is a deliberately conservative intake, not an estimate of how many source documents are truly paid transactions.

## Files to use

- [review.html](review.html): images, decisions, reasons, filters and optional raw OCR screening.
- [accepted_manifest.csv](accepted_manifest.csv): 91 accepted staged records, with image paths and class labels.
- [held_manifest.csv](held_manifest.csv): unresolved examples; do not use them as negative labels.
- [excluded_manifest.csv](excluded_manifest.csv): five existing duplicates and four within-release derivatives.
- [review_manifest.csv](review_manifest.csv): all 240 review decisions.
- [reviewed_records.jsonl](reviewed_records.jsonl): complete source, hash, grouping, label and review metadata.
- [summary.json](summary.json): final counts and validation results.
- records.json: initial acquisition metadata and pinned source revision.
- review_actions.json: editable review authority keyed to immutable number 1–240.
- protected_before.json: hashes of the existing labels, manifest, splits, results and 140 reference JSONs before staging.
- existing_similarity_candidates.csv and within_srd_similarity_candidates.csv: similarity screening, not automatic identity findings.

Raw SRD images remain under expressexpense_srd/images/. Synthetic source PDFs, rendered images, publisher metadata and embedded PDF text are separated under company_documents_v2/. All source PDFs are retained unchanged. The 40 final images were rendered with Poppler; an apparent preview omission in four pages prompted a second rendering check. Stored-image comparisons did not establish source corruption.

## Label rules and holds

Accept receipt where visible tender, payment, authorization, settled/closed-sale evidence supports the label. A total alone, restaurant menu holder, card-brand sticker, tip suggestion or payment policy does not establish payment. A positive balance due, explicit Unpaid, or Please Pay prompt is held. These documents may still be called receipts by their publisher; they need a project taxonomy decision before intake.

Accept customer_copy for the established explicit Customer Copy, Guest Copy or Duplicate cues. Merchant copies, recipient-unspecified Copy of Receipt, Guest Check and Reprint alone are not silently mapped to that class. SRD 1100 is explicitly Duplicate and SRD 1117 explicitly Customer Copy: these are the two accepted new copy candidates.

Preserve foreign food/merchant names within otherwise English documents. Predominantly French, Italian or Spanish documents are held for this English-first intake. Incomplete or multi-document captures are held when the missing content prevents a sound decision. The Micros Demo System sample is held because real transaction authenticity is unclear.

Packing Slip maps to delivery_note, consistent with existing class usage. Goods received notes and mixed invoice/delivery documents were not added.

## Duplicate handling

Existing SRD matches: 1057, 1073, 1085, 1164 and 1176. They link to the existing sample/group IDs in reviewed_records.jsonl and are not new data.

Within SRD: 1041 and 1114 repeat the La Source document retained as 1034; 1063 and 1186 repeat the Primo check retained as 1053. These are visual document matches, not claims of identical source bytes. Only the canonical accepted Primo document contributes to accepted counts. The canonical La Source example remains held for language/type review.

Perceptual hashes are screening aids. They can miss crops/rotations and falsely match sparse receipts. Consult the prior independent audit for the visually rejected Chef Wang/CoCo similarity. No assertion of exhaustive dataset independence is made.

## Grouping and future use

No split is assigned. SRD records carry conservative merchant keys; review actual layout families and any existing-corpus merchant/source relatives before a future grouped merge. Exact duplicates link to current sample/group IDs. Do not randomly split source images.

All synthetic examples use one generator-family group, with layout recorded separately. There are four layouts, five documents per class per layout. Treat these as training supplements only; they cannot establish real-photo generalization. Keep any parent/document variants together, and preserve publisher doc_id, variant, source-data family and revision.

SRD synthetic status is unknown, with capture_type indicating publisher receipt photography; realworld_transaction_verified=false. Company Documents is explicitly synthetic. Photo appearance does not independently establish a genuine business transaction.

OCR screening drafts are unreviewed intake aids, not ground-truth transcriptions. Synthetic embedded PDF text and publisher words/boxes are source-provided content, not measured project OCR. No new transcription gold set or classifier experiment was created.

## Source and licensing records

- ExpressExpense SRD: https://expressexpense.com/blog/free-receipt-images-ocr-machine-learning-dataset/
- Publisher archive: https://expressexpense.com/large-receipt-image-dataset-SRD.zip
- Verified archive MD5: c8eb0f2d286da5ab742e7a5b59f15147. Publisher permits MIT use and requests citation to ExpressExpense.com.
- Company Documents v2: https://huggingface.co/datasets/AyoubChLin/Company-document-dataset-v2
- Pinned revision: 0e9f5198e7e09f858834e544f96ec12436fdbb5e.
- Generated documents: Apache-2.0 with source database MIT/BSD notices. Publisher card, Apache license text and four source notices are retained in licenses/. Rendered JPEGs are project-derived conversions; source PDFs remain intact.

## Maintenance

The user authorized this bounded intake after the independent assessment. Other improvement tasks remain paused in Context/PENDING.md.

research/datasets/prepare_intake.py records acquisition; screen_intake_ocr.py creates screening drafts; finalize_intake.py validates and exports review decisions. Preserve all source bytes and review history. Do not rerun acquisition to change the selected set implicitly. Correct review_actions.json and rerun finalization for label changes; do not edit exported CSVs alone.
