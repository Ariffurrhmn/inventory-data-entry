# Round 2: reply to ChatGPT's feedback response

**PO_01: approved.** All numbers match `answers.csv`.

ChatGPT's answer was solid. Here's what we adopted:
- PO_05–10 use 1 clear title, 3 other titles (Order Form, Order Slip, Order) and 2 with no title. No Indent or Requisition.
- Every non-standard PO has "Please supply the following goods:", a "Required By" date and "Authorized by". The order numbers use `ORD-` instead of `PO-`.
- Challans: DN_06–10 use other titles (Challan, Delivery Note), and DN_10 has no title.
- A dot-matrix style is now shared across all three types.
- A "compact, normal-size text" instruction was added to all new prompts.
- Context file updated. Answer key gained a `title` column. PO_01–04 values are unchanged.

## Paste into ChatGPT

```
Thanks, your analysis was useful and I've adopted your proposed mix: for PO_05–PO_10, 1 clear
"Purchase Order" title, 3 alternative titles (Order Form / Order Slip / Order), 2 untitled, all with
"Please supply the following goods", a Required By date and buyer authorization. No Indent/Requisition.
Challans get the same treatment (some "Challan" / "Delivery Note", one untitled).

The project context has been updated. I'll paste the new version below; please use it from now on.
Then I'll send PO_05. One prompt, one image at a time, as you suggested.
```

Then paste the updated `0_CONTEXT_for_ChatGPT.md` (or update it in the ChatGPT Project instructions).
