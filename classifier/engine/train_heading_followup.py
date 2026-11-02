"""Bounded follow-up: fixed heading cues plus a saved trained statistical fallback."""
import csv,json,shutil
from pathlib import Path
from collections import Counter
from text_common import HERE,ROOT,CLASSES,clean_text,sha
from train_printed import load_ocr,dump,csvout
from ocr_v2 import combine_outputs
from run_text_experiment import metrics
from heading_rules import heading_decision
import joblib

def main():
 previous=HERE/'runs/printed_v1_grouped';out=HERE/'runs/printed_v1_headings';out.mkdir(exist_ok=False)
 rows=list(csv.DictReader((previous/'split_manifest.csv').open(encoding='utf-8')));development=[r for r in rows if r['split']!='test'];val=[r for r in development if r['split']=='val']
 spec=dict(parent_run='printed_v1_grouped',reason='Adaptive bounded follow-up after poor unseen-template validation; not a prespecified independent test.',heading_rule_sha256=sha(HERE/'heading_rules.py'),candidate_ocr=['baseline','sparse','combined'],statistical_fallback='Exact persisted baseline TF-IDF/logistic model trained on 150 printed training records; not refitted',rule='Unambiguous printed heading selects PO/DN/CC; otherwise trained classifier. Copy/order hybrids are flagged and use statistical fallback.',selection='Maximum validation macro-F1; ties prefer baseline, sparse, combined',test_inputs_opened=0)
 dump(out/'experiment_spec.json',spec);shutil.copy2(previous/'split_manifest.csv',out/'split_manifest.csv')
 model=joblib.load(previous/'baseline.joblib');results={};predictions=[];alltexts={}
 for row in development:
  a,_=load_ocr(row,'baseline');b,_=load_ocr(row,'sparse');alltexts[row['sample_id']]=dict(baseline=a,sparse=b,combined=combine_outputs(a,b))
 for policy in spec['candidate_ocr']:
  texts=[alltexts[r['sample_id']][policy] for r in val]
  fallback=model.predict([clean_text(t) for t in texts]);pred=[]
  for row,text,stat in zip(val,texts,fallback):
   cue=heading_decision(text);label=cue['label'] or str(stat);pred.append(label)
   predictions.append(dict(policy=policy,sample_id=row['sample_id'],actual=row['label'],predicted=label,statistical_prediction=str(stat),decision_source='printed_heading' if cue['label'] else 'trained_classifier',heading_evidence=cue['evidence'] or '',ambiguous_heading=cue['ambiguous'],correct=label==row['label']))
  results[policy]=metrics([r['label'] for r in val],pred)
  print(policy,results[policy]['correct'],'/',len(val),'macro-F1',round(results[policy]['macro_f1'],4),flush=True)
 selected=max(spec['candidate_ocr'],key=lambda p:results[p]['macro_f1'])
 shutil.copy2(previous/'baseline.joblib',out/'statistical.joblib')
 assert sha(out/'statistical.joblib')==sha(previous/'baseline.joblib')
 selection=dict(selected='statistical',ocr_policy=selected,heading_rules=True,heading_rule_sha256=spec['heading_rule_sha256'],scope_version='printed-only-v1',validation_macro_f1=results[selected]['macro_f1'],validation_accuracy=results[selected]['accuracy'],new_test_result=None,test_images_opened=0,adaptive_validation=True)
 dump(out/'selection.json',selection);dump(out/'validation.json',dict(candidates=results,selection=selection,training_records=150,validation_records=len(val),decision_counts=dict(Counter(r['decision_source'] for r in predictions if r['policy']==selected)),limitations=['Adaptive development validation, not a final independent test.','Validation has only three synthetic delivery notes and three receipts.','Heading rules cannot recover a heading that OCR missed.','Unresolved copy/order hybrid taxonomy uses statistical fallback.','No handwriting detector; only printed inputs supported.']))
 csvout(out/'validation_predictions.csv',predictions)
 active=HERE/'active_text_model.json';dump(out/'previous_active_model.json',json.loads(active.read_text(encoding='utf-8')))
 pointer=dict(run=out.name,model='statistical',model_sha256=sha(out/'statistical.joblib'),scope_version='printed-only-v1',ocr_policy=selected,heading_rules=True,heading_rule_sha256=spec['heading_rule_sha256'],selected_by='Adaptive development validation; explicit heading cues plus trained fallback',test_result=None)
 temporary=active.with_suffix('.tmp');dump(temporary,pointer);temporary.replace(active);dump(out/'completion.json',dict(activated=pointer,test_inputs_opened=0));print('Activated',out.name,selected,flush=True)
if __name__=='__main__':main()
