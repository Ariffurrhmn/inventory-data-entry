# Large files (hosted on Google Drive)

Files of 10 MB or more are not stored in this repository. They sit at the same relative paths in the project's shared Google Drive folder:

**Drive folder:** <https://drive.google.com/drive/folders/1yOBXNuSORBcOSWDhEg-YF1MEWIDvc8J2>

To restore one, download it from Drive and place it at the path in the "Repository path" column. These paths are listed in `.gitignore`, so git will not try to track them.

| Repository path | Size | What it is | Needed for |
|---|---|---|---|
| `classifier/engine/runs/printed_v2_contrastive/step20/model.safetensors` | 86.7 MB | Contrastive fine-tuning checkpoint (step 20) | Reproducing a rejected experiment only |
| `classifier/engine/runs/printed_v2_contrastive/step40/model.safetensors` | 86.7 MB | Contrastive fine-tuning checkpoint (step 40) | Reproducing a rejected experiment only |
| `classifier/engine/runs/printed_v1_transformers/bert_epoch4/model.safetensors` | 16.7 MB | BERT fine-tuning checkpoint, epoch 4 | Reproducing a rejected experiment only |
| `classifier/engine/runs/printed_v1_transformers/bert_epoch8/model.safetensors` | 16.7 MB | BERT fine-tuning checkpoint, epoch 8 | Reproducing a rejected experiment only |
| `classifier/engine/runs/printed_v1_transformers/bert_epoch12/model.safetensors` | 16.7 MB | BERT fine-tuning checkpoint, epoch 12 | Reproducing a rejected experiment only |
| `classifier/engine/.cache/tessdata/eng.traineddata` | 14.7 MB | Tesseract English language data | Local OCR (`classifier/` and `services/document_pipeline/`). Also downloadable from <https://github.com/tesseract-ocr/tessdata>. |
| `ChatGPT_Bridge/print/1_MUST_PRINT.pdf` | 10.4 MB | Print sheet for the synthetic document set | Re-printing only |
| `research/literature/On-Device _ Quantized LLM Deployment/AWQ ACTIVATION-AWARE WEIGHT QUANTIZATION FOR.pdf` | 18.9 MB | Reference paper | Reading only |
| `research/literature/Multilingual  or Handwritten OCR/Enhancement of Bengali OCR by Specialized Models and Advanced Techniques.pdf` | 12.2 MB | Reference paper | Reading only |
| `docs/meetings/WhatsApp Audio 2026-07-24 at 12.39.00 PM.mp4` | 16.0 MB | Supervisor-meeting recording | Reference only; not published because it contains a third party's voice |

The selected classifier (`printed_v3_explainable`) and its demo do not depend on the experiment checkpoints above.

## Exception: signed deliverables

`deliverables/Signed/Capstone_Report_Ch1_3.pdf` is 24.6 MB. It is the signed copy of the submitted report and the project's source of truth, so it is kept in git, byte-for-byte, even though it is over the threshold.

## Adding more large files

Put the file in the Drive folder, add its path to the "Large files" block of `.gitignore`, and add a row to the table above.
