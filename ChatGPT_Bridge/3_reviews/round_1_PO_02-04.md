# Review: round 1 (PO_02, PO_03, PO_04)

**Verdict: all 3 approved.** Every item, quantity, price and total matches `answers.csv`.

## Feedback prompt (paste into ChatGPT)

```
Feedback on PO_02, PO_03, PO_04: all numbers are exactly right, thank you. Keep that up.

Things to improve for the next ones:

1. Too clean and "designer". Real Bangladeshi shop paperwork is cheaper-looking: smaller text
   (normal 10–11pt document size, not huge headings), thinner lines, less empty space, plain fonts,
   cheap printer output. The document should fill the page the way a real form does.
2. PO_02 and PO_03 look like the same template (navy serif, same boxes). Each new one must look
   clearly different: different layout, font, header position and table style.
3. PO_04 (dot-matrix) was the best match for real life. Make it even more real next time: faint
   uneven ink, slightly misaligned columns, tractor-feed paper holes on the sides.

A question before you continue. Please answer it honestly, don't just agree with me:
In real life, would every purchase order have "Purchase Order" printed in big letters at the top?
I think many real ones are more ambiguous. They might be titled "Order Form", "Order Slip",
"Indent", "Requisition", or "Memo", have no title at all, or just be a handwritten list on a pad
with "Order" scribbled at the top. Our system has to work out the document type, so if every PO
shouts its type in the title, the test is too easy.
- How do real POs from small/medium businesses (especially in South Asia) usually look?
- Which clues, other than the title, still tell you it's an order and not an invoice or challan?
  (e.g. "Required by" / delivery date, no "paid" or "received", prices are requested not charged)
- Suggest a realistic mix: what share should have a clear title, a different title, or no title?
```

## Claude's own view

The user is right: a big "Purchase Order" title on every one makes classification too easy. Proposed mix, to be confirmed after ChatGPT answers:

- **About half:** clear "Purchase Order" title
- **About a third:** other titles ("Order Form", "Indent", "Order Slip")
- **The rest:** no title. The type has to come from clues like "Order Date", "Required By", and prices without "Paid"/"Received".

The same applies to challans ("Delivery Note", "Goods Dispatch", "Chalan", or no title) and customer copies (a small or faint stamp). I'll update the remaining prompts once ChatGPT replies.
