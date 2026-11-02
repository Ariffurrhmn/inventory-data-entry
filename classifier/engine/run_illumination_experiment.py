"""Uniform OCR comparison against the saved MiniLM hybrid; test excluded."""
import csv,json,shutil,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from text_common import HERE,ROOT,sha
from train_printed import dump,csvout,load_ocr
from illumination_ocr import illumination_ocr,POLICY
from inference import Predictor
from heading_rules import heading_decision
from ocr_v2 import combine_outputs
from run_text_experiment import metrics

def main():
 out=HERE/'runs/printed_v2_illumination';out.mkdir(exist_ok=False);(out/'ocr').mkdir()
 parent=HERE/'runs/printed_v1_minilm';rows=list(csv.DictReader((parent/'split_manifest.csv').open(encoding='utf8')))
 dev=[r for r in rows if r['split']!='test'];val=[r for r in dev if r['split']=='val'];assert len(dev)==175 and len(val)==25
 dump(out/'experiment_spec.json',dict(parent=parent.name,adaptive=True,policy=POLICY,all_development_images_same_policy=True,historical_test_inputs_opened=0,selection='Compare fixed learned fallback sparse/full/combined OCR with new recovered heading context; do not fit on validation',reason='Uniform local illumination correction and rotated title views for faint/angled printed headings',code_sha256=sha(HERE/'illumination_ocr.py')))
 shutil.copy2(parent/'split_manifest.csv',out/'split_manifest.csv');shutil.copy2(HERE/'illumination_ocr.py',out/'illumination_ocr.py')
 protected=json.loads((HERE/'runs/printed_v1_grouped/protected_before.json').read_text(encoding='utf8'));protected[str((HERE/'active_text_model.json').relative_to(ROOT))]=sha(HERE/'active_text_model.json')
 dump(out/'protected_before.json',protected)
 def extract(row):
  assert row['split'] in ['train','val'];assert sha(ROOT/row['image_path'])==row['image_sha256']
  views=illumination_ocr(ROOT/row['image_path']);record=dict(sample_id=row['sample_id'],image_sha256=row['image_sha256'],views=views,policy=POLICY,status='unreviewed_OCR_output')
  dump(out/'ocr'/(row['sample_id']+'.json'),record);return record
 n=0
 with ThreadPoolExecutor(max_workers=4) as pool:
  for f in as_completed([pool.submit(extract,row) for row in dev]):
   f.result();n+=1
   if n%10==0 or n==175:print('OCR',n,'/175',flush=True)
 predictor=Predictor();results={};records=[]
 for policy in ['sparse','full','combined']:
  pred=[]
  for row in val:
   sparse=load_ocr(row,'sparse')[0];views=json.loads((out/'ocr'/(row['sample_id']+'.json')).read_text(encoding='utf8'))['views']
   oldedge=json.loads((parent/'ocr_edges'/(row['sample_id']+'.json')).read_text(encoding='utf8'))['full_text']
   context='\n'.join([sparse,oldedge]+list(views.values()))
   text=sparse if policy=='sparse' else views['full'] if policy=='full' else combine_outputs(sparse,views['full'])
   result=predictor.predict_text(text,heading_text=context);pred.append(result['label'])
   records.append(dict(candidate=policy,sample_id=row['sample_id'],actual=row['label'],predicted=result['label'],source=result['decision_source'],evidence=result['heading_evidence'],correct=result['label']==row['label']))
  results[policy]=metrics([r['label'] for r in val],pred);print(policy,results[policy]['correct'],'/25',results[policy]['macro_f1'],flush=True)
 dump(out/'validation.json',dict(candidates=results,adaptive=True,historical_test_inputs_opened=0));csvout(out/'validation_predictions.csv',records)
 for path,digest in protected.items():assert sha(ROOT/path)==digest,path
 dump(out/'completion.json',dict(best=max(results,key=lambda n:results[n]['macro_f1']),protected_files_unchanged=len(protected),historical_test_inputs_opened=0,activated=False))
if __name__=='__main__':main()

