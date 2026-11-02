# Context: read this before making any image

## Who you're working for

I'm a university student in Bangladesh doing a capstone project. You'll get a series of prompts, one document each. For each one, make **one image** of the paper document it describes.

## What the project is

We're building a system that reads a **phone photo of a paper business document** and turns it into structured data (items, quantities, prices, totals). It also has to work out **what kind of document it is**, which is the hardest part.

Your images are test data. I'll print each one, photograph it with my phone, and feed the photo into our system. Then I compare what the system reads against the correct answers. **So every word and number you put in the image has to be exactly what the prompt says.** If you change a number, my answer key is wrong and the test is useless.

## The document types and how to tell them apart

The system tells these apart from small details, so get those details right.

| Type | What it means | Must have | Must NOT have |
|---|---|---|---|
| **Purchase Order** | A shop *orders* goods from a supplier. Nothing has arrived yet. | Buyer-to-supplier direction, an instruction to supply goods ("Please supply the following"), order no., order date, often a "Required By" date, Qty + Rate + Amount, total, buyer's authorization | "Paid", "Received", "Copy" |
| **Delivery Challan** | Goods were dispatched and signed for at the shop. | Challan No., Qty column, "Received By" + signature, "Delivered By" | **Any prices or totals.** In this project, that's the key difference from an invoice. Also no "Copy", "Duplicate" or "Original" marking. |

**Titles vary on purpose.** Real documents don't always announce their type, so some prompts use a different title ("Order Form", "Order Slip", "Challan", "Delivery Note") and some say **no title at all**. Use exactly the title the prompt gives. If it says no title, put no heading of any kind, and let the other clues (listed above) show what the document is. Don't add words like "Purchase Order" or "PO" anywhere the prompt doesn't.

**Don't let style give the type away.** Styles like dot-matrix, letterhead, or handwritten-on-a-form are used across all three types, so make each document look different from the last one, even within the same type. The same goes for **handwriting**: each handwritten document should look like a different person wrote it (blue or black ink, neat or rushed, upright or slanted, print or joined-up).
| **Customer Copy** | A *duplicate* of an invoice that was already recorded. | A visible copy marking ("CUSTOMER COPY", "DUPLICATE" or "OFFICE COPY") placed where the prompt says, plus items, rates, amounts and total | Anything that hides or shrinks the copy marking. **That marking is the whole point.** |

## Make it look like Bangladesh

- Bangladeshi shops and suppliers, mostly in Dhaka and nearby. Currency is **Tk** (Taka), written like `Tk 1,850`.
- Dates are written **DD/MM/YYYY**.
- English text. Shop names and addresses can be Bengali names written in English letters.
- Real local documents are plain and practical, not designer templates:
  - challan and cash-memo books with carbon copies
  - pre-printed forms filled in with a blue ballpoint
  - rubber stamps
  - dot-matrix printouts
  - cheap office printing

## Rules for every image

1. **Copy every word and number exactly.** Don't invent items, change quantities, recalculate, round, or add tax or discount lines that weren't asked for.
2. **Only the document.** Show it flat, straight and filling the frame: no desk, hands, phone, shadows, or 3D angle. I'll add the "real photo" look myself when I photograph the print.
3. **Everything readable.** Handwriting can be messy, but every number must be legible to a human.
4. **Follow the style in the prompt** (handwritten, thermal, letterhead, and so on). Different prompts should look clearly different from each other, not like one template.
5. **One document per image.** Portrait orientation, except for thermal receipts, which are a narrow tall strip.
6. **No watermarks, no "sample" text, no logos of real brands or companies.** All names are fictional.

## If you can't do something

If you can't fit everything, or a number might come out wrong, **say so in your reply** instead of guessing. A clearly stated problem is better than a quietly wrong image.

## Fixes

Sometimes I'll send a correction like "PO_03: total says 4,850, must be 4,580". Change only what the correction asks for and keep everything else the same.
