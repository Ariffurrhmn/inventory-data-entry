"""Adaptive semantic/lexical feature fusion follow-up; no historical test inputs."""
import csv,json,shutil
import joblib,numpy as np
from scipy.sparse import hstack,csr_matrix
from sklearn.preprocessing import normalize
from sklearn.linear_model import LogisticRegression
from text_common import HERE,ROOT,sha,clean_text
from train_printed import dump,csvout,load_ocr
from run_text_experiment import pipeline,metrics
from heading_rules import heading_decision

def main():
 parent=HERE/'runs/printed_v1_transformers';out=HERE/'runs/printed_v1_fusion';out.mkdir(exist_ok=False)
 spec=dict(parent=parent.name,adaptive_validation=True,selection='Best validation macro-F1, keep earlier candidate on ties',candidates=[dict(C=c,features='Training-fitted word/char TF-IDF normalized to unit norm concatenated with frozen first/last MiniLM vectors normalized jointly to unit norm') for c in [1,10]],headings='Same fixed edge/heading policy as printed_v1_edges',training_only_feature_fit=True,historical_test_inputs_opened=0)
 dump(out/'experiment_spec.json',spec)
 rows=list(csv.DictReader((parent/'split_manifest.csv').open(encoding='utf-8')))
 train=[r for r in rows if r['split']=='train'];val=[r for r in rows if r['split']=='val'];assert len(train)==150 and len(val)==25
 shutil.copy2(parent/'split_manifest.csv',out/'split_manifest.csv')
 texts=[clean_text(load_ocr(r,'sparse')[0]) for r in train+val]
 semantic=normalize(np.load(parent/'minilm_features.npy'))
 lexical=pipeline().named_steps['features'];lexical.fit(texts[:150])
 joblib.dump(lexical,out/'lexical_features.joblib')
 features=hstack([normalize(lexical.transform(texts)),csr_matrix(semantic)],format='csr')
 cues=[]
 for r in val:
  text=load_ocr(r,'sparse')[0];edge=json.loads((HERE/'runs/printed_v1_edges/ocr_edges'/(r['sample_id']+'.json')).read_text(encoding='utf-8'))
  assert edge['image_sha256']==r['image_sha256'];cues.append(heading_decision(text+'\n'+edge['full_text'])['label'])
 results={};records=[]
 for c in [1,10]:
  clf=LogisticRegression(C=c,class_weight='balanced',max_iter=1000,random_state=42).fit(features[:150],[r['label'] for r in train])
  name='fusion_c'+str(c);joblib.dump(clf,out/(name+'.joblib'))
  pred=clf.predict(features[150:])
  for hybrid in [False,True]:
   key=name+('_headings' if hybrid else '')
   labels=[cue or p for cue,p in zip(cues,pred)] if hybrid else pred
   results[key]=metrics([r['label'] for r in val],labels)
   records.extend(dict(candidate=key,sample_id=r['sample_id'],actual=r['label'],predicted=str(p),correct=p==r['label']) for r,p in zip(val,labels))
   print(key,results[key]['correct'],'/25',round(results[key]['macro_f1'],4),flush=True)
 dump(out/'validation.json',dict(candidates=results,adaptive=True,historical_test_inputs_opened=0))
 csvout(out/'validation_predictions.csv',records)
 protected=json.loads((parent/'protected_before.json').read_text(encoding='utf-8'))
 for path,digest in protected.items():assert sha(ROOT/path)==digest,path
 dump(out/'completion.json',dict(best=max(results,key=lambda n:results[n]['macro_f1']),protected_files_unchanged=len(protected),historical_test_inputs_opened=0,activated=False))
if __name__=='__main__':main()

