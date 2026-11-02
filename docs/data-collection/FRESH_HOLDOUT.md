# Fresh independent holdout collection

Prepared 2026-10-19. This is a collection specification, not a claim that new real documents have been collected.

## Target

Collect 80 distinct English business documents: 20 purchase orders, 20 paid receipts, 20 delivery notes/challans and 20 explicitly copy-marked documents. Target at least five independent business/layout families per class, with no more than four documents from a family. These are planning targets, not statistical guarantees. More supplier/layout families are preferable to repeat photos of one form.

Prioritize real purchase orders and delivery notes/challans, which remain underrepresented. Photographs of printed synthetic documents remain synthetic and cannot fill this real-document target.

## Keep it independent

Use new suppliers/merchants/layouts absent from the current training, validation, staged intake and exposed test sets. Check the existing manifests, hashes and known public-source matches before admitting a family. A different crop, photograph, compression, date or transaction from the same template does not by itself establish independence.

Each business document gets one document_id. Additional photos/pages of that document share its family_id and count as one independent document, not new examples. Keep original and photographed versions together. Record aliases so branches, merchant names and POS/template families are not accidentally split.

Place new source files in Dataset/holdout_real_pending/images/ and record them in manifest.csv. Preserve originals. Do not copy them into Dataset class folders or the current training set. Do not use their OCR text, class balance, errors or model predictions to tune a model. Freeze the candidate and admission rules before running a final evaluation.

## Class rules

| Class | Required evidence |
|---|---|
| purchase_order | Buyer-issued order for goods/services; a PO-number field on an invoice alone is insufficient |
| receipt | Paid transaction or paid sales invoice with payment evidence under the current conservative intake rule |
| delivery_note | Goods dispatch/delivery note, challan or packing slip; restaurant home-delivery text alone is insufficient |
| customer_copy | Explicit Customer Copy, Guest Copy, Office Copy or Duplicate under the existing project taxonomy |

Hold unpaid bills, merchant copies, unclear recipient copies, goods received notes and invoice/delivery hybrids pending a documented taxonomy decision. Copy-marked purchase orders or delivery notes also need an explicit single-label precedence rule; do not silently assign these.

Keep foreign business/food names within otherwise English documents. Record mixed-language pages for review rather than pretending all publisher receipt images are English.

## Capture and review

Keep the whole page and its header/footer in frame. Include normal phone variation in lighting, perspective and folds; retain the unmodified photo. Record printed/handwritten/mixed text and whether the image is complete. Extra challenge captures may be retained under the same document_id.

Record the source and permission/collection basis alongside each document. Have a person verify its class and source family without seeing the model prediction. Record the reviewer and date; do not mark assistant-reviewed labels human_verified.

Create reference transcriptions independently from the evaluated OCR output if OCR accuracy will be measured. Preserve literal text and clearly identify unreadable regions. Do not use an LLM's reconstruction of missing fields as observed truth.

## Manifest

manifest.csv is a blank intake template. One row per image/page; repeated document_id values do not increase the distinct-document count. Fields cover class, document/family ID, origin, image hash, capture information, review status and overlap findings. Empty rows are not collected data.

When collection is complete, audit duplicate/family overlap, freeze the manifest hash and record the model hash before evaluation. Count genuine documents and families per class separately from image count. Report uncertainty and subgroup coverage with final metrics; do not call a small holdout definitive deployment validation.

Existing reference: services/document_classifier/TEXT_EXPERIMENT.md and Context/OCR_TEXT.md. The old 28-image test has already been exposed and must not be described as fresh.

## Scope correction — 2026-10-20

Collect printed/typeset/thermal content only. Handwritten slips, handwritten transaction fields on printed forms, and handwriting-style synthetic bodies are excluded even when photographed from printed copies. Printed pages with handwritten notes/tips/values require a reviewed printed-only derivative before admission. Ignore incidental signatures. The current inherited validation subset has no eligible delivery notes; development validation additions must remain separate from this untouched final holdout.
