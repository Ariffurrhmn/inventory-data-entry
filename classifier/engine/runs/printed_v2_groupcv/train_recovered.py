"""Select a recovered-OCR classifier by training-only grouped CV, then report validation."""
import csv,json,shutil
import joblib,numpy as np
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import ComplementNB
from transformers import AutoTokenizer,AutoModel
from text_common import HERE,CLASSES,clean_text
from train_printed import dump,csvout,load_ocr
from run_text_experiment import pipeline,metrics
from transformer_models import minilm_features
from heading_rules import heading_decision
import torch

def build(name):
 if name=='wordchar_lr':return pipeline()
 if name=='char_lr':return Pipeline([('features',TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),sublinear_tf=True,max_features=50000)),('classifier',LogisticRegression(C=1,class_weight='balanced',max_iter=1000,random_state=42))])
 if name=='complement_nb':return Pipeline([('features',TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,max_features=30000)),('classifier',ComplementNB(alpha=.1))])
 return LogisticRegression(C=1,class_weight='balanced',max_iter=1000,random_state=42)
def main():
 torch.set_num_threads(4);source=HERE/'runs/printed_v2_illumination'
 assert (source/'completion.json').exists(),'OCR experiment must finish first'
 out=HERE/'runs/printed_v2_groupcv';out.mkdir(exist_ok=False)
 rows=list(csv.DictReader((source/'split_manifest.csv').open(encoding='utf8')))
 train=[r for r in rows if r['split']=='train'];val=[r for r in rows if r['split']=='val'];assert len(train)==150 and len(val)==25
 names=['wordchar_lr','char_lr','complement_nb','minilm_lr']
 dump(out/'experiment_spec.json',dict(adaptive_after_previous_validation=True,training_input='Uniform illumination-normalized full-page PSM6 OCR, no reference annotations',selection='Highest aggregated training-only 3-fold StratifiedGroupKFold macro-F1; candidate order breaks ties. Four candidates, no validation-based hyperparameter selection.',names=names,folds=3,seed=42,training=150,validation=25,historical_test_inputs_opened=0,feature_fit_within_each_training_fold=True))
 shutil.copy2(source/'split_manifest.csv',out/'split_manifest.csv');shutil.copy2(HERE/'train_recovered.py',out/'train_recovered.py')
 texts=[]
 for r in train+val:
  raw=json.loads((source/'ocr'/(r['sample_id']+'.json')).read_text(encoding='utf8'));assert raw['image_sha256']==r['image_sha256'];texts.append(clean_text(raw['views']['full']))
 y=np.array([r['label'] for r in train]);groups=np.array([r['development_group'] for r in train])
 folds=list(StratifiedGroupKFold(n_splits=3,shuffle=True,random_state=42).split(texts[:150],y,groups))
 fold_rows=[]
 for fold,(a,b) in enumerate(folds):
  assert not set(groups[a])&set(groups[b]);assert set(y[a])==set(CLASSES)
  fold_rows.extend(dict(sample_id=train[i]['sample_id'],held_out_fold=fold,group=groups[i],label=y[i]) for i in b)
 csvout(out/'training_folds.csv',fold_rows)
 info=json.loads((HERE/'runs/printed_v1_minilm/public_weights.json').read_text(encoding='utf8'))
 tok=AutoTokenizer.from_pretrained(info['local_path'],local_files_only=True);encoder=AutoModel.from_pretrained(info['local_path'],local_files_only=True)
 x=minilm_features(tok,encoder,texts);np.save(out/'minilm_features.npy',x);del encoder
 cv={};valresults={};records=[]
 for name in names:
  oof=np.empty(150,dtype=object)
  for a,b in folds:
   model=build(name)
   inputs=x if name=='minilm_lr' else texts
   ta=inputs[a] if name=='minilm_lr' else [inputs[i] for i in a]
   tb=inputs[b] if name=='minilm_lr' else [inputs[i] for i in b]
   model.fit(ta,y[a]);oof[b]=model.predict(tb)
  cv[name]=metrics(y,oof);print('GroupCV',name,cv[name]['correct'],'/150',round(cv[name]['macro_f1'],4),flush=True)
  model=build(name);model.fit(x[:150] if name=='minilm_lr' else texts[:150],y);joblib.dump(model,out/(name+'.joblib'))
  pred=model.predict(x[150:] if name=='minilm_lr' else texts[150:])
  for hybrid in [False,True]:
   output=[]
   for r,label in zip(val,pred):
    if hybrid:
     sparse=load_ocr(r,'sparse')[0];views=json.loads((source/'ocr'/(r['sample_id']+'.json')).read_text(encoding='utf8'))['views']
     oldedge=json.loads((HERE/'runs/printed_v1_edges/ocr_edges'/(r['sample_id']+'.json')).read_text(encoding='utf8'))['full_text']
     cue=heading_decision('\n'.join([sparse,oldedge]+list(views.values())));label=cue['label'] or str(label)
    output.append(str(label))
   key=name+('_headings' if hybrid else '');valresults[key]=metrics([r['label'] for r in val],output)
   records.extend(dict(candidate=key,sample_id=r['sample_id'],actual=r['label'],predicted=p,correct=p==r['label']) for r,p in zip(val,output))
   print('Validation',key,valresults[key]['correct'],'/25',round(valresults[key]['macro_f1'],4),flush=True)
 selected=max(names,key=lambda n:cv[n]['macro_f1'])
 dump(out/'validation.json',dict(training_group_cv=cv,validation_candidates=valresults,selected_by_training_cv=selected,adaptive_validation=True,historical_test_inputs_opened=0));csvout(out/'validation_predictions.csv',records)
 dump(out/'completion.json',dict(selected_by_training_cv=selected,selected_validation=valresults[selected+'_headings'],historical_test_inputs_opened=0,activated=False))
if __name__=='__main__':main()

