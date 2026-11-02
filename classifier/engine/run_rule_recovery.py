"""Compare fixed, versioned rule recovery and report training-only OOF hybrid results."""
import csv,json,shutil
import joblib,numpy as np
from text_common import HERE,ROOT,sha,clean_text
from train_printed import dump,csvout,load_ocr
from heading_rules_v2 import heading_decision
from run_text_experiment import metrics
from train_recovered import build
from sklearn.model_selection import StratifiedGroupKFold

def main():
 source=HERE/'runs/printed_v2_groupcv';assert (source/'completion.json').exists()
 out=HERE/'runs/printed_v2_rules';out.mkdir(exist_ok=False)
 selection=json.loads((source/'completion.json').read_text(encoding='utf8'))['selected_by_training_cv']
 spec=dict(parent=source.name,selection=selection,selection_basis='Retain training-group-CV selected classifier, do not reselect on validation',adaptive_validation=True,changes=['Three explicit printed field groups jointly identify a future purchase request: order number/date, required-by/date, please supply/request goods/items.','One edit allowed only for the distinctive 9-letter duplicate copy marker.','Preserve ambiguous cross-class cues as fallback, not arbitrary precedence.'],rule_code_sha256=sha(HERE/'heading_rules_v2.py'),historical_test_inputs_opened=0,training_oof='Three grouped folds; vocabulary/IDF/classifier refitted within training folds. Heading context uses sparse+new corrected views only; old edge cache was available only for validation and is omitted from training OOF.')
 dump(out/'experiment_spec.json',spec);shutil.copy2(HERE/'heading_rules_v2.py',out/'heading_rules_v2.py');shutil.copy2(source/'split_manifest.csv',out/'split_manifest.csv')
 rows=list(csv.DictReader((source/'split_manifest.csv').open(encoding='utf8')));train=[r for r in rows if r['split']=='train'];val=[r for r in rows if r['split']=='val']
 texts=[];cues=[]
 for r in train+val:
  views=json.loads((HERE/'runs/printed_v2_illumination/ocr'/(r['sample_id']+'.json')).read_text(encoding='utf8'))['views']
  raw=load_ocr(r,'sparse')[0];parts=[raw]+list(views.values())
  if r['split']=='val':parts.insert(1,json.loads((HERE/'runs/printed_v1_edges/ocr_edges'/(r['sample_id']+'.json')).read_text(encoding='utf8'))['full_text'])
  texts.append(clean_text(views['full']));cues.append(heading_decision('\n'.join(parts)))
 model=joblib.load(source/(selection+'.joblib'));assert selection!='minilm_lr','This version expects a text model selected by CV'
 fallback=model.predict(texts[150:]);pred=[cue['label'] or str(p) for cue,p in zip(cues[150:],fallback)]
 result=metrics([r['label'] for r in val],pred);records=[]
 for r,p,cue,f in zip(val,pred,cues[150:],fallback):
  records.append(dict(sample_id=r['sample_id'],actual=r['label'],predicted=p,fallback=str(f),rule_kind=cue.get('rule',{}).get('kind','') if cue.get('rule') else '',evidence=cue['evidence'] or '',ambiguous=cue['ambiguous'],correct=p==r['label']))
 csvout(out/'validation_predictions.csv',records);dump(out/'validation.json',dict(metrics=result,adaptive=True,historical_test_inputs_opened=0))
 print('Selected',selection,'with rule recovery',result['correct'],'/25',round(result['macro_f1'],4),flush=True)
 y=np.array([r['label'] for r in train]);groups=np.array([r['development_group'] for r in train]);oof=np.empty(150,dtype=object);learned=np.empty(150,dtype=object)
 for a,b in StratifiedGroupKFold(n_splits=3,shuffle=True,random_state=42).split(texts[:150],y,groups):
  assert not set(groups[a])&set(groups[b]);est=build(selection);est.fit([texts[i] for i in a],y[a]);p=est.predict([texts[i] for i in b]);learned[b]=p
  oof[b]=[cues[i]['label'] or str(label) for i,label in zip(b,p)]
 oofresult=metrics(y,oof);dump(out/'training_oof.json',dict(learned_only=metrics(y,learned),hybrid=oofresult,adaptive_rule_design=True,historical_test_inputs_opened=0,context='Training-only sparse+corrected OCR; no legacy edge views'))
 csvout(out/'training_oof_predictions.csv',[dict(sample_id=r['sample_id'],actual=r['label'],predicted=str(p),fallback=str(f),rule_kind=cue.get('rule',{}).get('kind','') if cue.get('rule') else '',correct=str(p)==r['label']) for r,p,f,cue in zip(train,oof,learned,cues[:150])])
 print('Training grouped OOF hybrid',oofresult['correct'],'/150',round(oofresult['macro_f1'],4),flush=True)
 before=json.loads((HERE/'runs/printed_v1_grouped/protected_before.json').read_text(encoding='utf8'))
 for path,digest in before.items():assert sha(ROOT/path)==digest,path
 dump(out/'completion.json',dict(selected=selection,validation=result,training_oof_hybrid=oofresult,activated=False,protected_files_unchanged=len(before),historical_test_inputs_opened=0))
if __name__=='__main__':main()

