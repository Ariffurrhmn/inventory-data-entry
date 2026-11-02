"""Bounded local transformer comparison on the frozen printed development split."""
import os
os.environ['HF_HUB_DISABLE_XET']='1'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING']='1'
import csv,json,shutil,time,random,platform
from pathlib import Path
import numpy as np,torch,joblib
from transformers import AutoTokenizer,AutoModel,AutoModelForSequenceClassification
from huggingface_hub import HfApi,snapshot_download
from sklearn.linear_model import LogisticRegression
from text_common import HERE,ROOT,CLASSES,sha,clean_text
from train_printed import dump,csvout,load_ocr
from run_text_experiment import metrics
from heading_rules import heading_decision

def download(repo,cache,out):
 info=HfApi().model_info(repo)
 patterns=['config.json','tokenizer.json','tokenizer_config.json','special_tokens_map.json','vocab.txt','README.md']
 patterns+=['model.safetensors'] if any(f.rfilename=='model.safetensors' for f in info.siblings) else ['pytorch_model.bin']
 path=Path(snapshot_download(repo,revision=info.sha,cache_dir=str(cache),allow_patterns=patterns))
 dump(out/(repo.split('/')[-1]+'_source.json'),dict(repo=repo,revision=info.sha,local_path=str(path),files={p.name:sha(p) for p in path.iterdir() if p.is_file()},license=getattr(info.card_data,'license',None)))
 return path

def tokens(tokenizer,text,maxlen=256):
 ids=tokenizer.encode(clean_text(text),add_special_tokens=False)
 if len(ids)>maxlen-2:
  half=(maxlen-2)//2;ids=ids[:half]+ids[-(maxlen-2-half):]
 return tokenizer.prepare_for_model(ids,add_special_tokens=True,truncation=False,return_attention_mask=True)

def embeddings(tokenizer,model,texts):
 # Separate start/end vectors preserve printed titles and customer-copy footers.
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

def main():
 random.seed(42);np.random.seed(42);torch.manual_seed(42);torch.set_num_threads(4)
 out=HERE/'runs/printed_v1_transformers';out.mkdir(exist_ok=False)
 parent=HERE/'runs/printed_v1_edges'
 rows=list(csv.DictReader((parent/'split_manifest.csv').open(encoding='utf-8')))
 train=[r for r in rows if r['split']=='train'];val=[r for r in rows if r['split']=='val']
 assert len(train)==150 and len(val)==25
 assert not ({r['development_group'] for r in train}&{r['development_group'] for r in val})
 spec=dict(parent_run=parent.name,validation_adaptive=True,train=150,val=25,historical_test_inputs_opened=0,seed=42,ocr_policy='sparse',models=['sentence-transformers/all-MiniLM-L6-v2','google/bert_uncased_L-2_H-128_A-2'],minilm='Frozen normalized mean-pooled first/last 254 token vectors concatenated, balanced LR C=1 and C=10; no encoder training',bert='End-to-end four-class classification, first/last tokens within256, balanced cross entropy, AdamW lr5e-5 weight_decay0.01 batch8 12epochs, evaluate/save epochs4,8,12',hybrid='Each candidate also evaluated with unchanged parent heading rules and cached validation edge OCR; no edge text enters learned features',selection='Compare validation macro-F1 against active parent .765688; no automatic activation',environment=dict(python=platform.python_version(),torch=torch.__version__,cuda=False))
 dump(out/'experiment_spec.json',spec);shutil.copy2(parent/'split_manifest.csv',out/'split_manifest.csv')
 protected=json.loads((HERE/'runs/printed_v1_grouped/protected_before.json').read_text(encoding='utf-8'))
 protected.update({str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [HERE/'active_text_model.json',parent/'statistical.joblib',HERE/'heading_rules.py',HERE/'edge_ocr.py']})
 dump(out/'protected_before.json',protected)
 texts=[];audit=[]
 for row in train+val:
  t,a=load_ocr(row,'sparse');texts.append(t);audit.append(a)
 dump(out/'ocr_input_audit.json',audit)
 cues=[]
 for r,t in zip(val,texts[len(train):]):
  edgepath=parent/'ocr_edges'/(r['sample_id']+'.json')
  e=json.loads(edgepath.read_text(encoding='utf-8'));assert e['image_sha256']==r['image_sha256']
  cues.append(heading_decision(t+'\n'+e['full_text'])['label'])
 results={};records=[]
 def evaluate(name,pred):
  pred=list(map(str,pred))
  for hybrid in [False,True]:
   labels=[cue or p for cue,p in zip(cues,pred)] if hybrid else pred
   key=name+('_headings' if hybrid else '')
   results[key]=metrics([r['label'] for r in val],labels)
   for r,p in zip(val,labels):records.append(dict(candidate=key,sample_id=r['sample_id'],actual=r['label'],predicted=p,correct=p==r['label']))
   print(key,results[key]['correct'],'/25',round(results[key]['macro_f1'],4),flush=True)
  dump(out/'validation.json',dict(candidates=results,adaptive=True,historical_test_inputs_opened=0))
  csvout(out/'validation_predictions.csv',records)
 cache=Path(json.loads((HERE/'runtime.local.json').read_text(encoding='utf-8'))['python']).parent.parent.parent/'hf-cache'
 mini=download(spec['models'][0],cache,out)
 tok=AutoTokenizer.from_pretrained(mini,local_files_only=True)
 encoder=AutoModel.from_pretrained(mini,local_files_only=True)
 start=time.time();x=embeddings(tok,encoder,texts);np.save(out/'minilm_features.npy',x)
 print('MiniLM encoded',len(texts),'documents in',round(time.time()-start,1),'seconds',flush=True)
 for c in [1,10]:
  model=LogisticRegression(C=c,class_weight='balanced',max_iter=1000,random_state=42).fit(x[:150],[r['label'] for r in train])
  joblib.dump(model,out/('minilm_c'+str(c)+'.joblib'))
  evaluate('minilm_c'+str(c),model.predict(x[150:]))
 del encoder
 tiny=download(spec['models'][1],cache,out)
 tok=AutoTokenizer.from_pretrained(tiny,local_files_only=True)
 model=AutoModelForSequenceClassification.from_pretrained(tiny,num_labels=4,local_files_only=True,id2label=dict(enumerate(CLASSES)),label2id={s:i for i,s in enumerate(CLASSES)})
 enc=[tokens(tok,t) for t in texts];y=torch.tensor([CLASSES.index(r['label']) for r in train])
 weights=150/(4*torch.bincount(y,minlength=4).float())
 lossfn=torch.nn.CrossEntropyLoss(weight=weights)
 opt=torch.optim.AdamW(model.parameters(),lr=5e-5,weight_decay=.01)
 for epoch in range(1,13):
  model.train();losses=[];order=torch.randperm(150)
  for indices in order.split(8):
   batch=tok.pad([enc[i] for i in indices.tolist()],padding=True,return_tensors='pt')
   opt.zero_grad();logits=model(**batch).logits;loss=lossfn(logits,y[indices]);loss.backward()
   torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);opt.step();losses.append(float(loss.detach()))
  print('BERT epoch',epoch,'loss',round(float(np.mean(losses)),4),flush=True)
  if epoch in [4,8,12]:
   model.eval();pred=[]
   with torch.inference_mode():
    for i in range(150,175,8):
     batch=tok.pad(enc[i:i+8],padding=True,return_tensors='pt')
     pred.extend(CLASSES[j] for j in model(**batch).logits.argmax(-1).tolist())
   name='bert_epoch'+str(epoch);model.save_pretrained(out/name);tok.save_pretrained(out/name)
   evaluate(name,pred)
 for path,h in protected.items():assert sha(ROOT/path)==h,path
 best=max(results,key=lambda n:results[n]['macro_f1'])
 dump(out/'completion.json',dict(best=best,metrics=results[best],parent_macro_f1=.7656882591093117,improved=results[best]['macro_f1']>.7656882591093117,activated=False,protected_files_unchanged=len(protected),historical_test_inputs_opened=0))
 print('BEST',best,results[best]['correct'],'/25',flush=True)

if __name__=='__main__':main()

