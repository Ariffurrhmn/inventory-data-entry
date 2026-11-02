# Public dataset assessment for the four-class OCR-text classifier

Research date: 2026-10-19 (Asia/Dhaka). Scope: document photograph/scan -> OCR text -> exactly one of `purchase_order`, `receipt`, `delivery_note`, `customer_copy`. No training, corpus merge, split change, or downstream extraction was performed.

## Findings and acquisition handoff

**Ready for a bounded acquisition after this assessment:** Company Documents v2 English purchase orders and packing slips, as explicitly synthetic supplementary data; ExpressExpense SRD, as a small permissively licensed photograph collection requiring copy-aware manual classification. These do not yet provide a balanced, independent real-document corpus. Five checked ExpressExpense customer-copy images already exist locally and must not be counted as new acquisitions.

**Conditional:** DocILE for real purchase orders after the project obtains authorized access and checks dataset terms; SROIE after original dataset terms are established; Roboflow PURCHSE ORDER_SET2 after full-resolution sample/annotation export and source-rights review. **Do not acquire for training yet:** WildReceipt (dataset license unresolved); Senga header dataset (currently HTTP 401, terms unavailable). CORD is useful for tracing current provenance and optional multilingual diagnostics, not the initial English collection.

The highest-priority gap is real, rights-cleared delivery notes/challans with varied suppliers and phone captures. Copy-marked documents need further collection too. No inspected source supplies a ready-made version of all four project labels. Search results are evidence of leads, not proof that a dataset is currently downloadable.

## Evidence and interpretation rules

Read project AGENTS.md, Context/{README,PROJECT,STATUS,CLASSIFIER,ORGANIZATION,DECISIONS}.md, and services/document_classifier/REVIEW.md before assessment. Current authoritative review: 145 inspected, 140 included (35 PO, 28 receipt, 50 delivery, 27 customer copy); 54 photographs of printed synthetic originals and 91 curated images with incomplete provenance. These historical experiment counts were not remeasured here.

- **Publisher-reported** means verified against a publisher page/file, not a recount of the full release.
- **Locally verified** means actual downloaded files/annotations were checked. Small samples are deliberately chosen for inspection, not statistically representative estimates of the release.
- **Usable** requires rights, English content, document semantics, copy-cue review, and overlap checks. Unknown class yield is not zero and is not an estimate.
- `sample_review.csv` records actual visual decisions. `sample_provenance.csv` records local sample SHA-256 values, original URLs/archive members, and derivations. `sources.csv` is the source-level register. Samples remain under Dataset/external_candidates/.

### Mapping to the project taxonomy

| Source label or visible evidence | Project mapping | Rule |
|---|---|---|
| Actual buyer-issued purchase order | purchase_order | Verify the document itself; a PO-number field on an invoice is insufficient. |
| Paid transaction receipt / paid sales invoice | receipt | Inspect payment evidence and copy markings. An unpaid invoice, quotation, proforma, or cancelled sale is not automatically eligible. |
| Packing slip / delivery challan / delivery note | delivery_note | Verify that the document describes goods dispatched/delivered; a shipping instruction or carrier release order is not automatically equivalent. |
| Customer Copy, Guest Copy, Office Copy, explicit Duplicate marking | customer_copy | Existing project taxonomy accepts these cues, including Office Copy (REVIEW.md; figures/fig5_doctype_taxonomy.svg). Do not replace it with a narrower everyday interpretation. |
| Merchant Copy; customer name/receipt without explicit copy marking; ambiguous invoice/copy hybrid | hold for review | Preserve existing exclusions. Mention of an order or customer is not a copy label. |
| Goods received note; combined INVOICE/DELIVERY NOTE | pending mapping | Semantically related but not already settled by the existing review. Do not silently add them to delivery_note. |

For copy-marked purchase orders or delivery notes, precedence across the four classes remains unresolved. Keep these outside the initial acquisition until the team specifies a single-label rule. The existing review establishes receipt/copy examples, not every possible cross-type conflict. This is a data-review hold, not a change to the four-class public output.

## Candidate comparison

| Candidate | Relevant class coverage | Counts and inspection | Acquisition decision |
|---|---|---|---|
| Company Documents v2 | PO; delivery via packing_slip; receipt | Publisher: PO 50,313, packing slip 47,740, receipt 16,456; 7 English PDFs inspected (2 PO, 2 packing, 1 receipt, 2 GRN) | Acquire small English synthetic subset; GRN held |
| ExpressExpense SRD | receipt; customer_copy after review | 200 archive members verified; 6 photos inspected; 5 copy-marked samples are exact existing matches | Ready; review whole small release before asserting class yields |
| DocILE | PO/receipt candidates in metadata | Publisher: 6,680 annotated documents, 1,152 layout clusters; 1 public sample inspected, tax_invoice | Access and terms required; no verified usable PO sample yet |
| SROIE | receipt, possible copy-marked subset | Paper: 1,000; some repackagings: 987; 2 mirrored images and OCR CSVs inspected | Terms/version reconciliation required |
| CORD v2 | receipt; not English-first | Publisher: 1,000 public (800/100/100); 2 images + JSON inspected | Provenance audit / optional multilingual only |
| WildReceipt | receipt; potential customer_copy subset | Paper: 1,740; actual downloaded train.txt: 1,267 rows; 46 images retained, 8 visually inspected | Dataset rights unresolved; copy cues are a screening lead |
| PURCHSE ORDER_SET2 | PO candidates | Uploader: 882 images, 43 extraction categories; 2 public thumbnails inspected | Conditional, not verified 882 usable POs |
| Senga header-dataset-10-03 | PO and delivery-note lead | Indexed preview: 530 train rows, mixed document-type fields; live access 401 | Access/terms blocked; no sample recommendation |
| CHIC | possible PO mining | Paper reports 774 corporate documents; data not acquired | Low priority lead; release/rights unverified |
| FATURA | invoices, no automatic target mapping | Publisher: 10,000 images, 50 templates; no local image sample | Reject for initial four-class acquisition |
| RVL-CDIP | broad forms/invoices; possible manual mining | Publisher: 400,000 pages, 16 classes; no target classes directly | Reject bulk acquisition; large archive and indirect match |

### Company Documents v2 — synthetic PO and packing-slip supplement

Original publisher: [AyoubChLin dataset card](https://huggingface.co/datasets/AyoubChLin/Company-document-dataset-v2), [statistics](https://huggingface.co/datasets/AyoubChLin/Company-document-dataset-v2/blob/main/stats.json), [licenses](https://huggingface.co/datasets/AyoubChLin/Company-document-dataset-v2/tree/main/licenses). Pinned observed revision: `0e9f5198e7e09f858834e544f96ec12436fdbb5e`.

Public Parquet subsets and bounded Hugging Face viewer rows worked without login. Publisher specifies Apache-2.0 for generated documents/code and MIT/BSD source-database notices; notices are retained locally. Research use is permitted subject to those conditions. Publisher totals above include French: English per-target counts were not verified. Four layout families, five themes; generated print and simulated scan/photo profiles, not actual handwriting or camera captures. JSON fields include `document_type`, `locale`, `doc_id`, `company`, `layout`, `words`, `boxes`, `file_content`, `extracted_data`. Text is generated/PDF-derived, not noisy OCR ground truth.

Local PDFs visibly contain clear PO and PACKING SLIP titles, distinct letterhead/modern arrangements, and a narrow receipt. GRN samples show receipt/inspection quantities and remain pending. Convert PDF pages to images, retain parent `doc_id`, filter `locale=en`, and run the project's OCR for comparable input. Company-held-out publisher splits still share layout families; use stricter family grouping locally. Same-generator words/themes and related Northwind/CompanyDocuments releases create overlap risk, even without identical images. No confirmed match to our current corpus.

### ExpressExpense SRD — strongest checked source for customer-copy examples

Original [publisher page and download](https://expressexpense.com/blog/free-receipt-images-ocr-machine-learning-dataset/). It explicitly grants MIT use with attribution. Publisher archive: [large-receipt-image-dataset-SRD.zip](https://expressexpense.com/large-receipt-image-dataset-SRD.zip), approximately 19.2 MB; verified MD5 `c8eb0f2d286da5ab742e7a5b59f15147`. Its 200 members are receipt images; only six were retained locally, with original filenames. The small archive was downloaded to temporary storage; no large collection was fetched.

Inspected English restaurant/retail receipt photos show hands, backgrounds, shadows, perspective, creases and differing merchant layouts; printed text with tip/signature areas. Do not infer all 200 have the same language/capture type. The archive supplies images, not document-class labels or OCR transcripts. Manually assign receipt versus customer_copy, exclude merchant-only/ambiguous cases, and OCR the photographs. Five inspected samples have Customer/Guest Copy cues; they are all already present locally. `1078-receipt.jpg` is an additional receipt candidate, not a measured class-yield estimate. Repeated chains/layouts require grouping. Check against WildReceipt and all receipt mirrors before treating sources as independent.

### DocILE — real business documents, access-dependent PO candidate

Original [benchmark](https://docile.rossum.ai/), [paper](https://arxiv.org/html/2302.05658), [official repository](https://github.com/rossumai/docile). Full download requires an access-request token; no form was submitted. The site offers research access, but full dataset rights/redistribution terms were not established here. Repository MIT must not be substituted for dataset permission.

Publisher annotated totals: 6,680 English business documents, 1,152 layout clusters; predominantly printed PDF/scanned business material. PO/receipt target counts remain unknown. The inspected public test fixture `516f2d61ea404b30a9192a72` is an invoice, not a PO or payment receipt. Its JSON **does** include image-level `metadata.document_type=tax_invoice`, `source=ucsf`, `original_filename=nkvc0055`, and `cluster_id=554`, alongside field/line-item annotations. Companion OCR JSON contains predicted DocTR text, not human transcript ground truth.

After authorized access, filter metadata for genuine POs then visually confirm semantics/copy cues. Render PDFs and preserve multi-page/cluster/source identity. Public sample alone verifies zero eligible PO documents. Shared UCSF ancestry creates possible overlap with RVL-CDIP, IIT-CDIP, DocVQA, FUNSD, CHIC and INV-CDIP; compare original identifiers, not just filenames. No match to our existing images was confirmed.

### SROIE — useful English receipts, release and terms need checking

Original [competition page](https://rrc.cvc.uab.es/?ch=13) and [competition paper](https://arxiv.org/abs/2103.10213). Live downloads page failed in this session. Small samples came from [zzzDavid's implementation repository](https://github.com/zzzDavid/ICDAR-2019-SROIE), an implementation/mirror rather than proof of original licensing. Its MIT file names implementation authors; a secondary repackaging's CC-BY assertion is not enough to establish original image rights. Mark dataset terms **unclear** pending original-release confirmation.

Paper reports 1,000 scanned receipt images; the 987 count in repackagings must not be called a verified usable release count. Downloaded `data/img/000.jpg`, `001.jpg` and matching `data/box/*.csv` show printed Malaysian cash receipts, faint printing and handwritten payment marks. CSV rows contain quadrilateral coordinates followed by recognized text (including commas); not image-level four-class labels. Other tasks annotate company/date/address/total, which are extraction fields.

Both inspected images are receipt candidates without visible copy cues. Confirm English, copy status and version before conversion. Do not equate cash-bill/invoice labels with paid receipts universally. Compare SROIE mirrors by image content/IDs; their alternate filenames and corrected annotations are not independent data. No existing-image match confirmed.

### CORD v2 — confirmed provenance clue, language mismatch

Original [NAVER repository](https://github.com/clovaai/cord), [official release](https://huggingface.co/datasets/naver-clova-ix/cord-v2). CC-BY-4.0 is explicit; attribution and modification notices are required. Public release is 1,000 Indonesian receipts, split 800/100/100, not the entire larger collection described in the paper. v0/v1/v2 substantially reuse images; do not pool as independent releases.

Direct rows requests returned 500; the public `first-rows` endpoint worked (26 returned rows). Retained viewer images for train IDs 0 and 8, source-served basename `image.jpg`, and full JSON `ground_truth` strings. Upstream original filenames are not exposed by the viewer; parent split/row and `meta.image_id` preserve identity. JSON includes `valid_line`, `words.text`, word quadrilaterals and semantic categories such as `menu.nm`; these are extraction labels, not document classes. Samples are printed receipts photographed with backgrounds, blur and redactions; Indonesian content with some English words is not automatically an English document.

Train ID 8 visually matches existing `cord-train-0008.jpg`, same 864 x 1296 pixels, RGB mean absolute difference 1.87979/255 after decoding. This confirms the same visual document/derivative with recompression differences; **not a byte-identical match**. Other `cord-train-*` filenames remain hypotheses until paired review. Keep this source out of the English-first addition unless explicitly approved as a separate language slice.

### WildReceipt — actual OCR annotations, unresolved dataset license

Original [paper](https://arxiv.org/html/2103.14470), [OpenMMLab metadata](https://github.com/open-mmlab/mmocr/blob/main/dataset_zoo/wildreceipt/metafile.yml), [publisher-hosted archive](https://download.openmmlab.com/mmocr/data/wildreceipt.tar). OpenMMLab lists dataset license N/A; code Apache licenses do not establish image rights. Research use remains unconfirmed.

Paper section IV reports 1,740 images and 1,268/472 train/test, but another table says 1,768. Actual retained `train.txt` has **1,267** JSONL records; do not silently reconcile these versions. Full archive size observed by HTTP headers: 185,323,520 bytes. Supported HTTP ranges retrieved only the first 10 MiB (after an initial 4 MiB probe); 46 complete image members and the complete training annotation file were retained, preserving member paths. Eight initial images were visually checked, not all 46.

Samples show printed English receipts in varied folds/perspective/backgrounds and some handwriting. JSONL contains `file_name`, dimensions, and `annotations[{box,text,label}]`; numeric labels are text-region extraction categories, not document types. A literal phrase screen across the 1,267 rows found 21 copy-cue candidates. These are **not 21 verified customer_copy images**; spacing errors, context and image review remain. Keep in research quarantine until rights are clarified. Shared receipts across web collections are possible; no local source match confirmed.

### PURCHSE ORDER_SET2 — uploader-labelled PO source, full samples pending

Original uploader [Roboflow project](https://universe.roboflow.com/purchase-order/purchse-order_set2). The page reports 882 images, CC-BY-4.0 and 43 object categories (e.g., BillToAddress_Data, CompanyName_Data). These are field boxes, not 43 document classes and not verified OCR transcripts. Public thumbnails downloaded without authentication; full-resolution export/annotations were not obtained and no account terms accepted.

One 156 x 200 preview visibly says PURCHASE ORDER; the other is too degraded to assign confidently. Predominantly printed monochrome form previews; full language, handwritten fraction, capture conditions and independent template count unknown. Retained the served filename `thumb.jpg` under distinct publisher image-ID directories. Thumbnail evidence is insufficient for OCR training. Obtain authorized full-resolution examples and inspect exports before acquisition; confirm underlying rights/source history despite uploader CC-BY declaration. No existing match confirmed. `.rf.` filenames elsewhere locally suggest Roboflow processing, not this particular project.

## Leads not recommended for initial acquisition

- **Senga header-dataset-10-03:** [indexed publisher page](https://huggingface.co/datasets/senga-ml/header-dataset-10-03) showed a 530-row training split with JSON `gt_parse.header.document_type` values such as Delivery Note, PURCHASE ORDER and INVOICE/DELIVERY NOTE. Live page, API, card and rows all returned HTTP 401. No image/annotation file downloaded, license or current release count verified, or actual sample visually inspected. Language/capture/handwriting/layout proportions and target yields unknown. Could be an unusually relevant real PO/delivery source if access and rights are granted; request clarification through the user, not automated signup or circumvention. No match claims.
- **CHIC:** [original paper](https://arxiv.org/html/2305.01054) describes 774 multilingual corporate documents, OCR and question-answer annotations drawn from RVL-CDIP/XFUND; a paragraph sums to 770. No authoritative usable PO/delivery/copy counts, available release package or dataset license verified. Paper license is not a dataset license. No local sample inspection; do not recommend acquisition yet. English filtering and manual labels needed; overlap with source collections is inherent.
- **FATURA:** [publisher record v1](https://zenodo.org/records/8261508), [paper](https://arxiv.org/abs/2311.11856). Publisher: 10,000 generated English invoice images from 50 templates, text/boxes and 24 field categories, three annotation formats. Zenodo API verifies CC-BY-4.0 and a 363,504,027-byte archive. A newer record exists; version was not silently changed. No archive downloaded or local sample inspected because invoice is outside our direct mapping. Not a PO dataset; no evidence to call invoices receipts or customer copies. Reject initial acquisition; shared template variants would require grouping if later used for another task.
- **RVL-CDIP:** [original publisher](https://adamharley.com/rvl-cdip/) provides 400,000 grayscale pages in 16 classes and a 37 GB archive, plus label files. Form/invoice labels do not map directly to our four classes. English archival printed/handwritten mix, scans rather than a modern phone-capture benchmark. OCR is referenced through IIT-CDIP rather than supplied as the four-class task. Rights point to UCSF source terms; not resolved as a blanket reuse license here. No bulk download/local sample inspection; reject initial acquisition. Potential UCSF overlap with DocILE/CHIC/DocVQA is substantial at source-family level, not a measured duplicate rate.
- Public procurement tables such as [California Purchase Order Data](https://lab.data.ca.gov/dataset/purchase-order-data) are transaction CSVs, not photographs/scans; not a document-image solution. Do not render these rows and claim measured public document diversity.

## Confirmed and possible overlap with the current corpus

| Existing path under Dataset/ | External reference | Evidence and status |
|---|---|---|
| Customer_Copy/express_srd_1085-receipt.jpg | SRD/1085-receipt.jpg | Confirmed SHA-256 equality; visible Guest Copy |
| Customer_Copy/1057-receipt.jpg | SRD/1057-receipt.jpg | Confirmed SHA-256 equality; Customer Copy |
| Customer_Copy/1073-receipt.jpg | SRD/1073-receipt.jpg | Confirmed SHA-256 equality; Customer Copy |
| Customer_Copy/1164-receipt.jpg | SRD/1164-receipt.jpg | Confirmed SHA-256 equality; Customer Copy |
| Customer_Copy/1176-receipt.jpg | SRD/1176-receipt.jpg | Confirmed SHA-256 equality; Customer Copy |
| Receipt/cord-train-0008.jpg | Official CORD v2 train row 8 | Confirmed visual derivative; dimensions equal, slight decoded pixel differences; not byte-identical |
| Other cord-train-* | CORD | Filename clue only; not individually matched |
| Customer_Copy/image_*.jpg | Possible receipt collections, including WildReceipt | Generic filename is insufficient; unknown |
| Receipt/*_jpg.rf.* | Some Roboflow export | Naming convention only; source project unknown |
| Shopify/ABC/HGT originals and phone variants | Existing template families | Previously documented project families; this research did not attribute ownership or public-dataset origin |

`overlap_matches.csv` records file hashes, paired paths and CORD comparison metric. No existing provenance/label files were rewritten. The five SRD matches establish immediate contamination risk if SRD is added blindly. Potential dataset-to-dataset overlap is not confirmed duplication unless paired evidence is available.

## Practical initial collection (proposal, not acquired counts)

Start with an intake goal of **40 reviewed documents per class** (160 total), and at least 8 independent layout/supplier families per class where feasible. The numbers are collection targets, not measured public yields. If fewer independent families are found, report the shortfall; do not fill quotas with many regenerated pages from the same template.

| Class | Initial route | Balance and independence constraint |
|---|---|---|
| purchase_order | Up to 20 English Company Documents v2 examples across its four layout families; seek at least 20 real POs through authorized DocILE/verified Roboflow access or permission-based collection | Synthetic layouts cannot satisfy the real-family quota. Real PO yield not yet known. |
| delivery_note | Up to 20 English synthetic packing slips; seek at least 20 real delivery notes/challans from independent suppliers | Keep GRN and hybrid invoice/delivery pages out until mapping resolved. Real public source remains unverified. |
| receipt | Review SRD first, cap additions at 40 with varied merchants and no explicit accepted copy cue; supplement SROIE only after rights/version review | Do not borrow an arbitrary receipt label from extraction datasets. |
| customer_copy | Review SRD for additional explicit markings, subtract the five known existing matches; permission-based collection if yield is insufficient | No measured 40-document public yield established. WildReceipt screening is not permission to train. |

Do not pool this intake with current training yet. Add provenance IDs, source version, original filename/member, rights, language, capture type, synthetic flag, OCR text/engine/version, document label, copy cue, reviewer, vendor and family before any future merge. Separate source-provided transcript from project OCR output; evaluate on OCR text so perfect synthetic/PDF transcripts do not inflate performance relative to phone captures.

Build a cross-source duplicate graph using SHA-256, decoded pixels, perceptual similarity and OCR text plus manual review. Group original/photo/scan/crop/degradation variants, multipage documents, repeated merchant layouts, shared generator families and related order/delivery documents. Resolve graph components before assigning any future split. A common business logo alone is not proof of identical layout. Keep the immutable existing splits intact. Reserve a new real-document holdout from families/sources absent from development; no strong final performance claim from the already-inspected old test set. This session created neither new splits nor a model.

## Remaining decisions and validation limits

1. Specify copy precedence when PO/delivery documents carry accepted copy cues; decide whether goods received notes and invoice/delivery hybrids are eligible.
2. Obtain DocILE access terms; clarify SROIE and WildReceipt dataset rights; verify Roboflow full-resolution exports and original provenance; determine whether Senga access can be granted. No messages or applications were sent.
3. Audit remaining curated filenames and all SRD members for overlap; only six direct source correspondences were established here.
4. Collect real English PO/delivery/copy photos across suppliers and actual capture conditions; current synthetic options cannot replace that evidence.

Scripts under this directory are inspection records, not project corpus generators. They write only candidate/derived outputs, but some repeat downloads; do not rerun them merely to read this report. No project generator, bridge prompt builder, OCR service, training, or evaluation command was run. Protected label/manifest/split/results hashes were taken before final report writing and rechecked afterward; that check covers report finalization, not a claimed pre-session snapshot of every original image. All image reads were non-mutating.
