"""Class-balanced, cross-group contrastive MiniLM adaptation on training OCR only."""
import csv,json,random,shutil
from collections import defaultdict
import torch,numpy as np,joblib
from transformers import AutoModel,AutoTokenizer
from sklearn.linear_model import LogisticRegression
from text_common import HERE,ROOT,CLASSES,sha
from train_printed import dump,csvout,load_ocr
from transformer_models import head_tail_tokens,minilm_features
from heading_rules import heading_decision
from run_text_experiment import metrics

def main():
 torch.set_num_threads(4);torch.manual_seed(42);np.random.seed(42);rng=random.Random(42)
 out=HERE/'runs/printed_v2_contrastive';out.mkdir(exist_ok=False)
 parent=HERE/'runs/printed_v1_minilm';rows=list(csv.DictReader((parent/'split_manifest.csv').open(encoding='utf8')))
 train=[r for r in rows if r['split']=='train'];val=[r for r in rows if r['split']=='val'];assert len(train)==150 and len(val)==25
 info=json.loads((parent/'public_weights.json').read_text(encoding='utf8'))
 dump(out/'experiment_spec.json',dict(adaptive_validation=True,seed=42,train=150,val=25,historical_test_inputs_opened=0,method='Supervised contrastive loss with class-balanced batches; two distinct training groups per class per step. Only final two encoder layers trained; rest frozen.',steps=40,checkpoints=[20,40],batch=8,temperature=.1,lr=2e-5,weight_decay=.01,classifier='Balanced LR C1 on training embeddings only',input='Sparse OCR; training first/last256-token sequence, evaluation same first/last254-token separate views as parent',source_revision=info['revision'],selection='Validation macro-F1; no automatic activation'))
 shutil.copy2(parent/'split_manifest.csv',out/'split_manifest.csv');shutil.copy2(HERE/'train_contrastive.py',out/'train_contrastive.py')
 texts=[load_ocr(r,'sparse')[0] for r in train+val];groups={c:defaultdict(list) for c in CLASSES}
 for i,r in enumerate(train):groups[r['label']][r['development_group']].append(i)
 assert all(len(g)>=2 for g in groups.values())
 tok=AutoTokenizer.from_pretrained(info['local_path'],local_files_only=True);model=AutoModel.from_pretrained(info['local_path'],local_files_only=True)
 for name,param in model.named_parameters():param.requires_grad=name.startswith(('encoder.layer.4.','encoder.layer.5.'))
 opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=2e-5,weight_decay=.01)
 enc=[head_tail_tokens(tok,t) for t in texts[:150]];labels=torch.arange(4).repeat_interleave(2)
 positive=(labels[:,None]==labels[None,:])&~torch.eye(8,dtype=torch.bool)
 cues=[]
 for row,text in zip(val,texts[150:]):
  edge=json.loads((parent/'ocr_edges'/(row['sample_id']+'.json')).read_text(encoding='utf8'))['full_text']
  cues.append(heading_decision(text+'\n'+edge)['label'])
 results={};records=[];losses=[]
 for step in range(1,41):
  model.train();indices=[]
  for c in CLASSES:
   for group in rng.sample(list(groups[c]),2):indices.append(rng.choice(groups[c][group]))
  batch=tok.pad([enc[i] for i in indices],padding=True,return_tensors='pt')
  h=model(**batch).last_hidden_state;mask=batch['attention_mask'].unsqueeze(-1)
  pooled=torch.nn.functional.normalize((h*mask).sum(1)/mask.sum(1).clamp(min=1),p=2,dim=1)
  logits=(pooled@pooled.T)/.1;logits=logits.masked_fill(torch.eye(8,dtype=torch.bool),-1e9)
  logp=logits-torch.logsumexp(logits,dim=1,keepdim=True);loss=-logp[positive].mean()
  opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1);opt.step();losses.append(float(loss.detach()))
  if step%10==0:print('Contrastive step',step,'loss',round(losses[-1],4),flush=True)
  if step in [20,40]:
   name='step'+str(step);model.eval();x=minilm_features(tok,model,texts)
   clf=LogisticRegression(C=1,class_weight='balanced',max_iter=1000,random_state=42).fit(x[:150],[r['label'] for r in train])
   model.save_pretrained(out/name);tok.save_pretrained(out/name);joblib.dump(clf,out/(name+'.joblib'));np.save(out/(name+'_features.npy'),x)
   pred=clf.predict(x[150:])
   for hybrid in [False,True]:
    key=name+('_headings' if hybrid else '');p=[cue or str(a) for cue,a in zip(cues,pred)] if hybrid else list(map(str,pred))
    results[key]=metrics([r['label'] for r in val],p);print(key,results[key]['correct'],'/25',round(results[key]['macro_f1'],4),flush=True)
    records.extend(dict(candidate=key,sample_id=r['sample_id'],actual=r['label'],predicted=a,correct=a==r['label']) for r,a in zip(val,p))
   dump(out/'validation.json',dict(candidates=results,adaptive=True,historical_test_inputs_opened=0));csvout(out/'validation_predictions.csv',records)
 dump(out/'losses.json',losses);dump(out/'completion.json',dict(best=max(results,key=lambda k:results[k]['macro_f1']),historical_test_inputs_opened=0,activated=False))
if __name__=='__main__':main()

