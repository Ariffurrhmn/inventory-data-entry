import csv,json,sys,platform
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'services/document_classifier'))
import numpy as np,torch,transformers,joblib
from transformers import AutoTokenizer,AutoModelForSequenceClassification
from text_common import HERE,CLASSES
from train_printed import dump,load_ocr
from transformer_models import head_tail_tokens
torch.set_num_threads(4)
run=HERE/'runs/printed_v1_transformers'
rows=list(csv.DictReader((run/'split_manifest.csv').open(encoding='utf-8')))
train=[r for r in rows if r['split']=='train'];texts=[load_ocr(r,'sparse')[0] for r in train]
result={}
for epoch in [4,8,12]:
 path=run/('bert_epoch'+str(epoch));tok=AutoTokenizer.from_pretrained(path,local_files_only=True);model=AutoModelForSequenceClassification.from_pretrained(path,local_files_only=True).eval()
 pred=[]
 with torch.inference_mode():
  for i in range(0,150,8):
   batch=tok.pad([head_tail_tokens(tok,t) for t in texts[i:i+8]],padding=True,return_tensors='pt')
   pred.extend(CLASSES[j] for j in model(**batch).logits.argmax(-1).tolist())
 result[str(epoch)]={'training_correct':sum(p==r['label'] for p,r in zip(pred,train)),'training_n':150,'parameters':model.num_parameters()}
 print(epoch,result[str(epoch)],flush=True)
dump(run/'training_diagnostic.json',dict(bert=result,versions=dict(python=platform.python_version(),torch=torch.__version__,transformers=transformers.__version__),historical_test_inputs_opened=0))

