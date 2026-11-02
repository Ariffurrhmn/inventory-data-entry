# Initial dataset review — 2026-10-19

All 145 converted images were inspected on the generated contact sheets. Labels are recorded explicitly in labels.csv. This is a visual project review, not independent double annotation. The initial contact sheets retain the original folder labels; use labels.csv and manifest.csv for corrected labels.

- 54 HEIC photos converted successfully, alongside 91 curated JPEG/PNG images; zero decoding errors and zero byte-identical source files.
- Six folder-label corrections: purchase-order photos IMG_0966 through IMG_0970 are packing slips, and IMG_0977 is a delivery challan. Their manifest label is delivery_note. Original folders/files are preserved.
- Five ambiguous inputs excluded pending team review: invoice-only receipt 6161..., cancelled sales invoice IMG_20251024_205811..., merchant copy image_0311.jpg, customer receipt without explicit copy marking image_1065.jpg, and image_1687.jpg without an unambiguous copy marking. Reasons are in labels.csv.
- Office-copy photos IMG_1006/1007 remain customer_copy because the existing proposal taxonomy explicitly lists Office Copy as a copy cue (figures/fig5_doctype_taxonomy.svg). Guest Copy and Duplicate markings are also accepted. Paid sales invoices remain receipt per existing folder usage; invoice-only/cancelled cases are deferred.
- All ABC generated delivery-challan forms and their photographed versions share one family. All Shopify packing slips and their photos share another. HGT purchase-order forms/photos and personal purchase-order forms/photos are similarly grouped. Bridge photographs are grouped conservatively by layout family. Chick-fil-A copies share one family; repeated handwritten/paid-sales-invoice receipt layouts are grouped.
- Perceptual hashing produced 142 candidates. Many are false positives from sparse white pages; it was used to support visual review, not to merge every candidate automatically.
- Labels.csv is the editable authority; seed_review.py only records how this initial reviewed mapping was populated and refuses to overwrite it. Do not use it as an automatic label reviewer for new data.

Usable counts: purchase_order 35, receipt 28, delivery_note 50, customer_copy 27 (140 total).
Train 86, validation 26, test 28. Frozen assignments are in data/splits.csv. Both generated/curated originals and phone photographs may occur in held-out sets, but known related families do not cross sets. The corpus has too few independent template families for a strong generalization claim; supplier identities are not fully annotated.

Model choice: MobileNetV3 Small with ImageNet pretrained features; classification head trained on this corpus. Input is the full letterboxed page at 224 pixels. No document text, boxes, tables, or numerical annotations are used. A baseline at this resolution may miss small copy markings; evaluation should expose that limitation rather than conceal it.