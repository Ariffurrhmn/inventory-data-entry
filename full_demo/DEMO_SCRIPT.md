# Demo script: showing the full system to your supervisor

**Goal of the meeting:** leave with a decision to continue, and with answers to three specific questions (at the end). About 15 minutes, plus questions.

**The one-sentence pitch:** *A shop owner photographs a printed delivery note, receipt, purchase order or customer copy with their phone. The system reads it, works out what kind of document it is, pulls out the numbers, checks the arithmetic, and sends a clean record to the owner's existing ERP. If it is not sure, it says so instead of guessing.*

## Before you go (10 minutes)

- [ ] Run `Open Demo (phone).cmd` (or `./full_demo/run.sh --lan`). Keep that window open.
- [ ] On the dashboard, **Phone app** tab: confirm the QR and pairing code show.
- [ ] Pair your own phone once (scan the QR) and take one test photo. Confirm it appears in the dashboard.
- [ ] On the **ERP inbox** tab press **Reset demo data**.
- [ ] Send one document first, so Tesseract is warm and the first live run is fast.
- [ ] Bring a **printed** document (a real receipt or delivery note) for the live moment. Thermal receipts that are faded or crumpled will fail, and that is fine, but try it beforehand.
- [ ] Check the wifi. Phone and laptop must be on the same network. Some venues (university Wi-Fi in particular) block device-to-device traffic. If the phone cannot open the address, use the phone frame in the dashboard. It runs the same app.
- [ ] Have `Evidence` tab numbers in mind (below). Do not improvise numbers.

## The walkthrough

### 1. The problem (1 min). No screen needed
Small businesses receive paper: delivery notes, purchase orders, receipts, customer copies. Someone retypes these into an inventory system. It is slow and mistakes creep in. The project reads the paper and **only trusts what it can check**.

### 2. The whole path on one screen (1 min): *Live demo* tab
Point at the five boxes at the top. Say which are **real** and which are **stand-ins**, before anyone asks:
*Capture, reading, classification and verification are real. Field extraction is a rule-based stand-in for the language-model step we have not provisioned yet. The ERP is a stand-in inbox.*

### 3. Happy path (2 min)
Click **Purchase order - clean print**.
- Step 2: the type and *why* ("decided by a printed heading").
- Step 2 (extracted data): every ✓ means the value is quoted word-for-word from the page. Nothing is guessed.
- Step 3: it passes. Explain: *each row's quantity × price equals its total, and the totals add up.*
- Click **Send the same photo again**. The toast shows the same idempotency key returned the existing result. *A flaky mobile connection can retry without creating duplicates.*

### 4. A document that is wrong (2 min)
Click **Purchase order - printed total is wrong**. The document itself contains an error. The system reads it correctly and **flags** it: "Row 3: quantity × unit price does not equal the line total". Say: *the system's job is to notice, not to silently fix.*

Then **Try to break it** → *Inflate a quantity ×10*. *This simulates an AI extraction making a mistake. Verification catches it two ways: the number is not in the quoted text, and the arithmetic fails.*

### 5. The phone (3 min): *Phone app* tab
- Show the phone app, either on the real phone or in the frame. Take a photo of your printed document.
- Watch it arrive in the dashboard feed. Tap it to open the result.
- Optional, strongest moment (rehearse it first on your own phone): switch the phone to airplane mode, take a photo ("Offline queue"), switch back, and watch it upload and process. Photos are stored on the phone and use the same idempotency key.

### 6. The ERP end (1 min): *ERP inbox* tab
One JSON record per document. Passed records are *eligible*, flagged ones are *blocked for review*. **Nothing changes stock** (`inventory_updated` is always false). Open the JSON from any result to show what the ERP receives.

### 7. Honesty slide (3 min): *Evidence* tab
This is where you earn trust. Walk through, in this order:
1. **Real vs stand-in table.**
2. **Recorded classifier results: 23 / 25** on the development validation set. *We tuned against this set, so it is a development number, not final accuracy.*
3. **Measured now on 86 synthetic documents**: 65 / 86 routed correctly. When a printed heading decides: 56 / 56. **Receipts: 9 / 30**, which is the classifier's weak spot (no heading rule for "RECEIPT").
4. **The verification trade-off** (the stacked bars): all 17 documents with a printed arithmetic error were flagged; but with the lenient policy 21 wrong records pass unflagged, mostly OCR slips in item names (`5kg` → `S5kg`) that arithmetic cannot see.
5. **Known gaps**, especially: no real-document test yet, extraction is a stand-in.

## Questions you will probably get

| Question | Honest answer |
|---|---|
| *Does the AI extraction work?* | We do not have an LLM extraction step running yet, and we make no claim about one. The rule-based stand-in reads clean tables and refuses messy rows. The verification layer is built to check whatever extractor we plug in (there is a hook for it), and the next step is to measure one. |
| *How accurate is it?* | On clean synthetic documents: 76% routed correctly, 27 of 86 read with every field exact. Those are the numbers we trust, and they are lower than the 92% development figure because that one is on a small tuned set. We have **no number on real documents yet**; collecting them is the next step. |
| *Why is it unsure about the phone photos?* | They are noisy. The system leaves cells empty rather than guessing, and flags them. That behaviour is deliberate. |
| *Why does the demo option exist?* | Under the strict contract almost everything is flagged, because most documents print only a grand total. The demo option compares the total with the sum of the rows, assuming there is no tax or discount. It is clearly labelled, switchable, and a decision for you. |
| *Is it safe to deploy?* | Not yet. It is a local demo: pairing code, no accounts, no cloud, no real ERP connection. |
| *Would it work on a real phone?* | The PWA is tested in an emulated browser. Installing it needs https. We have not yet tested on a physical phone for long sessions or different camera hardware. |
| *Is the dataset real?* | The 86 test documents are fabricated and cleanly rendered. The classifier development set mixes some public receipt photos with synthetic documents photographed from print. Real business documents are still to be collected. |

## Decisions to ask for

1. **Totals policy:** do we require printed subtotal/tax/discount (safer, more flagged), or accept "lines add up to the grand total" with a stated no-tax assumption (more automatic, 21 silent errors in our test)?
2. **Real data:** can we collect 40+ real printed documents from a few shops, and how should we protect the owners' privacy?
3. **Extraction step:** which model are we allowed to use (local only, or an API), given there is no paid-API budget today?

Then, if the supervisor agrees, the next steps are listed on the Evidence tab.

## If something goes wrong

| Problem | Do this |
|---|---|
| Phone cannot reach the laptop | Use the phone frame on the *Phone app* tab. Same app. Say so honestly. |
| Live photo gives a poor result | Say "this is what a noisy photo does". Show that it was flagged. That is the point of the system. Then switch to a shelf document. |
| First run is slow (up to 30 s on a cold start) | Always send one document before the meeting begins. |
| The page shows a connection error | Restart `Open Demo.cmd`. The dashboard must be opened on the same computer at `http://127.0.0.1:8790`. |
| Anything else | `full_demo/docs/screenshots/` has pictures of every screen from a working run. |
