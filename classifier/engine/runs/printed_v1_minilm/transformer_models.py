"""Offline transformer inference adapter; public weights remain outside Drive sync."""
from pathlib import Path
import numpy as np
from text_common import clean_text,sha

def head_tail_tokens(tokenizer,text,maxlen=256):
 ids=tokenizer.encode(clean_text(text),add_special_tokens=False)
 if len(ids)>maxlen-2:
  half=(maxlen-2)//2;ids=ids[:half]+ids[-(maxlen-2-half):]
 return tokenizer.prepare_for_model(ids,add_special_tokens=True,truncation=False,return_attention_mask=True)

def minilm_features(tokenizer,model,texts):
 import torch
 result=[];model.eval()
 with torch.inference_mode():
  for text in texts:
   ids=tokenizer.encode(clean_text(text),add_special_tokens=False)
   ends=[ids[:254],ids[-254:]]
   batch=tokenizer.pad([tokenizer.prepare_for_model(x,return_attention_mask=True) for x in ends],padding=True,return_tensors='pt')
   h=model(**batch).last_hidden_state;mask=batch['attention_mask'].unsqueeze(-1)
   pooled=(h*mask).sum(1)/mask.sum(1).clamp(min=1)
   pooled=torch.nn.functional.normalize(pooled,p=2,dim=1)
   result.append(pooled.numpy().reshape(-1))
 return np.array(result)

class TransformerClassifier:
 def __init__(self,backend,weights_path,files,classes,classifier=None,lexical=None):
  self.backend=backend;self.weights_path=str(weights_path);self.files=files
  self.classes_=np.array(classes);self.classifier=classifier;self.lexical=lexical
  self._tokenizer=None;self._encoder=None
 def __getstate__(self):
  state=self.__dict__.copy();state['_tokenizer']=None;state['_encoder']=None
  return state
 def load(self):
  if self._encoder is not None:return
  import torch
  from transformers import AutoTokenizer,AutoModel,AutoModelForSequenceClassification
  torch.set_num_threads(4)
  directory=Path(self.weights_path)
  for filename,digest in self.files.items():
   if sha(directory/filename)!=digest:raise ValueError('Transformer weight/tokenizer hash mismatch: '+filename)
  self._tokenizer=AutoTokenizer.from_pretrained(directory,local_files_only=True)
  factory=AutoModel if self.backend=='minilm' else AutoModelForSequenceClassification
  self._encoder=factory.from_pretrained(directory,local_files_only=True).eval()
 def predict_proba(self,texts):
  import torch
  self.load()
  if self.backend=='minilm':
   features=minilm_features(self._tokenizer,self._encoder,texts)
   if self.lexical is not None:
    from scipy.sparse import hstack,csr_matrix
    from sklearn.preprocessing import normalize
    features=hstack([normalize(self.lexical.transform(texts)),csr_matrix(normalize(features))],format='csr')
   return self.classifier.predict_proba(features)
  batch=self._tokenizer.pad([head_tail_tokens(self._tokenizer,t) for t in texts],padding=True,return_tensors='pt')
  with torch.inference_mode():return self._encoder(**batch).logits.softmax(-1).numpy()


