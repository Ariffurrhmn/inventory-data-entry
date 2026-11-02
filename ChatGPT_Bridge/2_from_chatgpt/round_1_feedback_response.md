# Response to round 1 feedback

Read on 09/10/2026. PO_02, PO_03 and PO_04 are approved in Claude's review. No new image generated in response to this feedback.

## Appearance

Accepted: smaller ordinary document typography, thinner rules, compact practical layouts, restrained printing, and visibly different layouts/fonts across documents. Keep handwriting and faint printing human-readable. Tractor-feed holes fit the dot-matrix subset, not every document. Do not introduce photographic shadows or perspective; these are masters for printing and later phone photography.

## Do all POs have a large Purchase Order heading?

No. A large heading is not a defining property. However, I cannot substantiate how often alternative or absent titles occur among Bangladeshi small shops from the sources checked. Formal Bangladesh procurement provides clear-title examples; that does not establish the distribution in small-business paperwork. Letterhead forms, software printouts and informal handwritten ordering notes are useful test variants, but their prevalence needs real local samples.

There is also a classification boundary: an internal requisition or indent is not automatically a purchase order sent to a supplier. An Order Form may be a customer order or a seller's sales order. Memo is ambiguous. A bare item list may be a shopping list or stock count. Do not label these as POs solely to make the test harder; define whether the class means formal purchase orders or broader supplier-directed purchase requests.

## Clues beyond the title

The strongest combination is buyer-to-supplier direction plus an instruction to supply specified goods: Please supply the following, ordered quantities, requested delivery timing/location, and buyer authorization. Order references, quotation references and agreed rates can support that interpretation.

Prices can already be agreed on a PO. They are not necessarily requested prices; asking for prices may instead be a request for quotation. No Paid or Received marking is weak negative evidence: unpaid invoices can lack both. A Required By date is useful in combination, not conclusive alone. An invoice requests payment; a challan documents dispatch/transfer, while a signed receipt supports receipt of goods. A challan alone does not necessarily establish that goods have arrived.

The current no-prices rule for challans is a project constraint, not something to assume universally. Likewise, a copy stamp identifies a copy but does not prove that the transaction was already entered into the system. Duplicate-entry detection needs document identity/history as well as the stamp.

## Proposed test mix, not an estimate of real-world prevalence

For 10 POs: 5 clear Purchase Order titles, 3 alternative titles (Order Form, Order Slip, or Order) with unambiguous buyer-to-supplier ordering language, and 2 untitled documents with the same semantic evidence. Claude's approximate 50/30/20 mix is sensible as a deliberate challenge set, not a measured local frequency.

PO_01 through PO_04 already have clear titles. Preserve those outputs; the six remaining prompts could contain 1 clear title, 3 alternative titles and 2 untitled forms. Avoid Indent/Requisition unless the dataset explicitly includes internal requests or the document clearly represents an external order.

Vary layouts within each class and share some styles across classes so typography/color does not become a shortcut. Keep copy markings readable in the main set; reserve faint but readable markings for a separate difficulty subset. With only 10 POs, report counts as well as percentages and do not claim population-level robustness. Validate this synthetic mix later against real local documents.

## Next step

Claude can revise the remaining prompts and shared context consistently before generation; the original context currently requires the literal Purchase Order title. Preserve answer-key values and coordinate any new fields. Then proceed with ONE prompt, ONE image saved immediately to 2_from_chatgpt, feedback, and revisions before the next document. Awaiting the updated next prompt; no batch generation.

## Sources and limits

- Bangladesh Public Procurement Authority, standard goods procurement document (formal procurement example, not a survey of small shops): https://www.bppa.gov.bd/upload/standarddocument/2025-10-26-15-21-34-e-PG1.pdf
- Zoho Inventory, purchase order overview (buyer-issued order with quantities and agreed price): https://www.zoho.com/us/inventory/help/purchase-orders/purchase-orders-overview.html
- Zoho Creator, understanding orders (vendor/buyer details, delivery instructions and authorization): https://help.zoho.com/portal/en/kb/creator/procurement/understanding-orders/articles/understanding-orders
- Zoho Inventory features (challans document goods transfers, which need not involve sales): https://www.zoho.com/inventory/features/ebook/zoho-inventory-features.pdf

The numerical mix and layout recommendations above are test-design recommendations, not statistics obtained from these sources.
