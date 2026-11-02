# ChatGPT Bridge

Claude writes prompts → ChatGPT makes images → Claude reviews → print and photograph.

## Folders

| Folder | Who writes it | What's in it |
|---|---|---|
| `1_prompts/` | Claude | One prompt per document (`PO_01.txt` …) |
| `2_from_chatgpt/` | You | ChatGPT's image, **same name as the prompt** (`PO_01.png`) |
| `3_reviews/` | Claude | Pass or fail notes, plus a fixed prompt if needed |
| `4_approved/` | Claude | Images that passed, ready to print |
| `answers.csv` | Claude | The correct items, quantities and totals for each document (needed for testing) |

## Your loop

0. **Once per chat:** paste (or upload) `0_CONTEXT_for_ChatGPT.md` into ChatGPT first. Best option: make a ChatGPT **Project** and put it in the project instructions, so every chat gets it automatically.
1. Open a prompt in `1_prompts/`, paste it into ChatGPT.
2. Save the image into `2_from_chatgpt/` with the same name.
3. Tell Claude **"review the bridge"**.
4. Redo any that fail, using the new prompt in `3_reviews/`.
5. Print everything in `4_approved/`, photograph it with your phone, and put the photos in `Dataset/`.

## What to make (29 total)

- `PO_01`–`PO_10`: Purchase Orders
- `DN_01`–`DN_10`: Delivery Challans (+ 5 packing slips from the Shopify PDF)
- `CC_01`–`CC_09`: Customer Copies

To regenerate prompts: `python tools/make_prompts.py`. This overwrites `1_prompts/` and `answers.csv`.
