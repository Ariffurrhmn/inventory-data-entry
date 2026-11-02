# Independent review of the dataset scout findings

Reviewed 2026-10-19. Scope: assess the 11 sources in sources.csv against the existing four-class corpus. This review supplements DATASET_SEARCH.md rather than replacing the scout's evidence.

**Two dataset families are already represented: ExpressExpense SRD and CORD.** This does not disqualify their entire releases. Exclude existing documents and derivatives from new-data counts, and group any retained relatives with the existing document before splitting.

## Confirmed overlap flags

| Source | Existing files | Evidence |
|---|---|---|
| ExpressExpense SRD | Customer_Copy/express_srd_1085-receipt.jpg; 1057-receipt.jpg; 1073-receipt.jpg; 1164-receipt.jpg; 1176-receipt.jpg | Five SHA-256 identities, independently rechecked against original local bytes |
| CORD v2 train row 8 | Receipt/cord-train-0008.jpg | Same receipt, redaction, item text and capture; compression derivative rather than identical bytes |

The current corpus contains six confirmed corresponding documents across these two sources. Filenames or matching layout alone are insufficient evidence for other provenance claims. Dataset-2 remains photographs of printed synthetic/generated documents, as confirmed by the user; this audit found no additional public-source attribution for those photographs.

Independent audit: 145 manifest rows checked for byte identity and all 140 included prepared images used for perceptual screening. Compared 74 retained candidate image files plus the cached 200-image SRD archive, totaling 274 entries and 266 unique byte streams. Five exact matches and two perceptual candidates resulted. CORD was visually confirmed; SRD 1016-receipt.jpg versus the handwritten CoCo receipt was visually rejected as a false positive. No other overlap was detected within that bounded comparison. This is not proof that unexamined full datasets are disjoint, nor an exhaustive crop/rotation-resistant duplicate search.

Artifacts: overlap_recheck_exact.csv; overlap_recheck_near_candidates.csv (algorithm output, NOT identity findings); overlap_recheck_visual_decisions.csv; overlap_recheck_validation.json; overlap_recheck_pairs.jpg. The original scout's overlap_matches.csv remains intact. The new SRD 1016 sample is retained in external_candidates solely to reproduce the rejected similarity, with provenance in overlap_recheck_visual_decisions.csv.

## Usability assessment

| Source | Already represented? | Decision for our classifier | What it contributes / remaining work |
|---|---|---|---|
| Company Documents v2 | No overlap detected in retained samples | Best immediate synthetic supplement | Select English purchase_order and packing_slip; latter maps to delivery_note. Review receipt examples separately. Apache-2.0 generated documents with retained source notices. Four layout families limit independence; group parent/variant/template relationships. Do not count generated words as measured OCR. |
| ExpressExpense SRD | YES: five exact documents | Best immediate photo source, after review | English receipt/copy candidates; explicit publisher MIT permission. Entire cached archive checked for exact overlap. 195 members are not exact matches, but that is NOT a yield of 195 eligible new documents. Review copy cues, language, payment status and near duplicates. No ready OCR transcriptions. |
| DocILE | No match established | Conditional, potentially useful real PO source | Research access and full dataset terms need review. The inspected public fixture is a tax invoice, not a verified PO. Filter actual document_type metadata and inspect downloaded pages before claiming PO yield. |
| SROIE | No match detected in two retained samples | Conditional receipt/OCR source | English-oriented scanned receipts with text/box annotations. Good OCR-reference potential. Establish original image terms and exact release; mirror code license is insufficient. Relabel copy-marked documents and check full release for duplicates. |
| CORD v2 | YES: one compression derivative | Provenance reference; low priority for English expansion | Indonesian receipt collection with text/boxes and explicit CC-BY notice. Some English text does not make the release English-first. Versions are related releases, not independent datasets. |
| WildReceipt | No match detected in retained samples | Technically promising; hold intake pending dataset terms | English photo receipts and transcription annotations. Copy-cue candidates are leads, not verified four-class labels. OpenMMLab metadata lists dataset license N/A. Its code license does not resolve image permission. |
| Roboflow PURCHSE ORDER_SET2 | No match established | Conditional PO candidate | Uploader declares CC-BY-4.0. Current thumbnails do not establish full text, provenance or layout diversity. Obtain authorized full-resolution export, inspect actual PO pages, preserve augmentation/parent families. The .rf filenames in our corpus do not establish this project as their source. |
| Senga header-dataset-10-03 | Unknown | Access-dependent lead only | Scout recorded live HTTP 401; this review's browser also could not retrieve the page. No local images or validated license. Indexed document-type text is not enough to recommend intake. |
| CHIC | Unknown; no local images | Low priority | Multilingual corporate VQA with inherited source relationships. No verified release terms or usable target-class yields in this assessment. Much manual screening for uncertain benefit. |
| FATURA | Unknown; no local images | Unsuitable for initial four-class intake | Generated invoices/extraction categories do not automatically map to PO, paid receipt, delivery note or explicit copy. May help later downstream invoice extraction, outside this classifier task. |
| RVL-CDIP | Unknown; no local images | Skip bulk acquisition | Broad archival categories rather than our four classes. Large download and manual mining cost; inherited source relationships and rights require care. |

I inspected the scout's retained contact sheet, including Company Documents PO/packing-slip/GRN samples, SROIE samples and ExpressExpense copy photos; separately inspected both overlap comparison pairs. Small purposive samples cannot establish full-release class yield.

One correction to watch in the scout shortlist: ExpressExpense 1078-receipt.jpg visibly shows Order Balance due. Its source label alone is insufficient to classify it as a paid receipt. Keep it pending payment/eligibility review. Similarly, a PO-number field on an invoice is not a purchase order, and generic invoice datasets must not fill the receipt class automatically.

## Recommended order

1. Prepare a small English Company Documents v2 PO/packing-slip supplement, explicitly synthetic; preserve generator/parent IDs.
2. Review unique SRD photos for receipt versus accepted customer-copy cues, excluding the five duplicates and holding unpaid bills/ambiguous cases.
3. Obtain/check DocILE access and SROIE/WildReceipt terms if more real examples are needed.
4. Prioritize collecting varied real English delivery-note/challan photographs and independent copy-marked layouts. The current shortlist does not close those gaps.

Existing customer_copy handling includes Office Copy, Guest Copy and explicit Duplicate under the current project taxonomy. Copy-marked POs/delivery notes, goods received notes and hybrid invoice/delivery pages still need a single-label rule before inclusion. No labels were changed here.

## Sources checked

Publisher pages and repositories rechecked in this session:
- Company Documents: https://huggingface.co/datasets/AyoubChLin/Company-document-dataset-v2
- ExpressExpense: https://expressexpense.com/blog/free-receipt-images-ocr-machine-learning-dataset/
- CORD: https://github.com/clovaai/cord
- DocILE: https://docile.rossum.ai/
- SROIE mirror/version evidence: https://github.com/zzzDavid/ICDAR-2019-SROIE
- WildReceipt dataset metadata: https://github.com/open-mmlab/mmocr/blob/main/dataset_zoo/wildreceipt/metafile.yml
- Roboflow uploader: https://universe.roboflow.com/purchase-order/purchse-order_set2
- Senga unavailable: https://huggingface.co/datasets/senga-ml/header-dataset-10-03
- CHIC: https://arxiv.org/abs/2305.01054
- FATURA: https://zenodo.org/records/8261508
- RVL-CDIP: https://adamharley.com/rvl-cdip/

Existing images, annotations, class labels, frozen splits and models were preserved. No data was merged and no training/OCR experiment was run. Assessment is authorized by the latest user request; the five paused implementation tasks remain paused.
