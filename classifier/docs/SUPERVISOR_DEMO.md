# Supervisor demonstration script

## Before the meeting

Double-click classifier/Open Demo.cmd. Confirm the top-right “Model ready · Local” status. Use Workspace for the walkthrough. Recorded examples are the reliable default; run one live image only if time allows. Open the app before losing internet/Drive connectivity so the local folder and dependencies are available.

## Opening explanation

“Our prototype classifies English printed business documents into purchase orders, receipts, delivery notes and customer copies. It combines local OCR, explicit document evidence and a trained text classifier. It also exposes how a decision was made. It does not extract the line-item tables or update an inventory system.”

## Walkthrough

1. **Purchase request:** show the image. Its title is not the only cue: the recognized order number, required-by date and request to supply goods jointly support a purchase request. Point to the three actual matched strings.
2. **Retail receipt:** show a learned decision and its supporting/opposing words. The numbers are log-score contributions, not confidence percentages.
3. **Delivery challan:** show the printed document-type marker.
4. **Office copy:** explain that photographs of printed synthetic documents are development data, not real business transactions. A copy marker distinguishes the document's role.
5. **Faint copy stamp:** show a failure deliberately. The existing annotation says customer_copy; the model says purchase_order. Its features include location words that should not independently establish document type. Better OCR/copy data is needed. Explainability reveals that weakness.
6. **Model & evidence:** present23/25 validation and146/150 grouped training check. Say both are adaptive development evidence; a fresh real holdout is still required.
7. **Live mode:** click Run live classification on a known example or choose a new printed image. The badge changes to Live analysis. OCR may take several seconds; no artificial progress percentage is shown. Recorded mode never pretends to perform live OCR.
8. Export JSON or save it in classifier/exports/ to show a machine-readable record containing the decision, OCR and evidence.

## Likely questions

**Is it BERT?** Earlier experiments tried frozen MiniLM, small BERT fine-tuning, contrastive adaptation and lexical/semantic fusion. The selected fallback is TF-IDF word/bigram features and Complement Naive Bayes, selected using grouped folds within training. OCR and conservative rules account for much of the final hybrid improvement. It is not a claim of92% standalone BERT accuracy.

**What was trained?** The fallback vocabulary, IDF and classifier were fitted on150 training documents. Four recovered-OCR candidates were compared within three grouped training folds. The25-document validation set was reused for adaptive development. Historical test27 stayed excluded.

**Why the large improvement?** Local illumination correction recovers clearer text. Separating OCR views gives each its own title window; previously later recovered headings could be excluded by a single30-line budget. Conservative purchase-intent and OCR-tolerant copy rules provide explicit evidence. This is a hybrid design.

**How faithful is the explanation?** Rule explanations expose actual normalized matches and any explicit one-character OCR correction. Learned n-gram contributions reconstruct the target-versus-alternative score difference, including the intercept. Saved validation explanations had maximum reconstruction error2.27e-14. They describe associations and may show the wrong reason; they are not generated justifications.

**Does92% prove deployment readiness?** No. It is23/25 reused development validation. Only eight customer copies are in training; all three validation delivery notes are printed synthetic examples. Rules were adapted during development, even when model folds held out groups. Independent human-verified real documents are still needed.

**What happens to documents?** Processing is local. Uploaded images live temporarily during analysis and are removed afterward. Reports are saved only when requested and do not automatically become annotation truth or training data.

**What is next?** Collect independent printed customer-copy families and a fresh real holdout; improve recovery of faint/angled stamps. Keep classification separate from future table/number extraction.

