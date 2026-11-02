"""One bounded OCR edge-recovery comparison; the trained model is unchanged."""
import csv,json,shutil
from concurrent.futures import ThreadPoolExecutor,as_completed
from text_common import HERE,ROOT,sha
from train_printed import dump,csvout,load_ocr
from inference import Predictor
from heading_rules import heading_decision
from run_text_experiment import metrics

def main():
 parent=HERE/'runs/printed_v1_headings';out=HERE/'runs/printed_v1_edges';out.mkdir(exist_ok=False)
 rows=list(csv.DictReader((parent/'split_manifest.csv').open(encoding='utf-8')));val=[r for r in rows if r['split']=='val']
 spec=dict(parent_run=parent.name,reason='Adaptive, bounded OCR follow-up for missed printed copy markings; no independent test claim.',ocr='PSM11 full-page text for statistical features, plus autocontrasted top/bottom 35% PSM6 for heading cues only',selection='Promote only if validation macro-F1 improves over parent; no other parameter search.',model_fitted=False,test_inputs_opened=0,edge_code_sha256=sha(HERE/'edge_ocr.py'))
 dump(out/'experiment_spec.json',spec);cache=out/'ocr_edges';cache.mkdir()
 from edge_ocr import edge_ocr
 def extract(row):
  assert row['split']=='val';assert sha(ROOT/row['image_path'])==row['image_sha256']
  text=edge_ocr(ROOT/row['image_path']);dump(cache/(row['sample_id']+'.json'),dict(sample_id=row['sample_id'],image_sha256=row['image_sha256'],full_text=text,status='unreviewed_OCR_output'));return row['sample_id'],text
 texts={}
 with ThreadPoolExecutor(max_workers=4) as executor:
  futures=[executor.submit(extract,row) for row in val]
  for future in as_completed(futures):sid,text=future.result();texts[sid]=text
 predictor=Predictor(parent.name);pred=[];records=[]
 for row in val:
  base,_=load_ocr(row,'sparse');statistical=predictor.predict_text(base);cue=heading_decision(base+'\n'+texts[row['sample_id']]);label=cue['label'] or statistical['statistical_label'];pred.append(label)
  records.append(dict(sample_id=row['sample_id'],actual=row['label'],predicted=label,previous=statistical['label'],decision_source='printed_heading' if cue['label'] else 'trained_classifier',evidence=cue['evidence'] or '',correct=label==row['label']))
 result=metrics([r['label'] for r in val],pred);promote=result['macro_f1']>predictor.selection['validation_macro_f1']
 dump(out/'validation.json',dict(metrics=result,promoted=promote,parent_accuracy=predictor.selection['validation_accuracy'],parent_macro_f1=predictor.selection['validation_macro_f1'],validation_adaptive=True,test_inputs_opened=0));csvout(out/'validation_predictions.csv',records)
 print('Edge recovery',result['correct'],'/',len(val),'macro-F1',result['macro_f1'],'promote',promote,flush=True)
 if promote:
  shutil.copy2(parent/'statistical.joblib',out/'statistical.joblib');shutil.copy2(parent/'split_manifest.csv',out/'split_manifest.csv');shutil.copy2(HERE/'heading_rules.py',out/'heading_rules.py');shutil.copy2(HERE/'edge_ocr.py',out/'edge_ocr.py')
  selected=dict(predictor.selection,edge_recovery=True,edge_code_sha256=spec['edge_code_sha256'],validation_accuracy=result['accuracy'],validation_macro_f1=result['macro_f1']);dump(out/'selection.json',selected)
  active=HERE/'active_text_model.json';old=json.loads(active.read_text(encoding='utf-8'));dump(out/'previous_active_model.json',old);pointer=dict(old,run=out.name,edge_recovery=True,edge_code_sha256=spec['edge_code_sha256'],selected_by='Adaptive development validation; heading edge recovery plus trained fallback')
  temporary=active.with_suffix('.tmp');dump(temporary,pointer);temporary.replace(active);dump(out/'completion.json',dict(activated=pointer,test_inputs_opened=0))
if __name__=='__main__':main()
