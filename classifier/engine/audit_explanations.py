"""Explanation evidence for existing validation errors, without changing predictions."""
import csv,json,shutil
from text_common import HERE,sha
from train_printed import dump,csvout,load_ocr
from inference import Predictor
from explain import explain_prediction

out=HERE/'runs/printed_v2_explainability';out.mkdir(exist_ok=False)
predictor=Predictor();parent=HERE/'runs'/predictor.run
rows={r['sample_id']:r for r in csv.DictReader((parent/'split_manifest.csv').open(encoding='utf8'))}
pred=list(csv.DictReader((parent/'validation_predictions.csv').open(encoding='utf8')))
chosen=[r for r in pred if r['correct']=='False']+[pred[0]]
dump(out/'experiment_spec.json',dict(model_run=predictor.run,method='Fixed-model token-block omission with exact score differences, plus deterministic heading trace',model_fitted=False,samples='All five previously recorded validation errors plus first heading-selected validation record',explain_code_sha256=sha(HERE/'explain.py'),historical_test_inputs_opened=0))
shutil.copy2(HERE/'explain.py',out/'explain.py')
summary=[]
for expected in chosen:
 row=rows[expected['sample_id']];assert row['split']=='val'
 text=load_ocr(row,'sparse')[0];edge=json.loads((parent/'ocr_edges'/(row['sample_id']+'.json')).read_text(encoding='utf8'))['full_text'];context=text+'\n'+edge
 result=predictor.predict_text(text,heading_text=context);assert result['label']==expected['predicted']
 explanation=explain_prediction(predictor,text,heading_text=context,result=result,max_blocks=16)
 dump(out/(row['sample_id']+'.json'),dict(sample_id=row['sample_id'],actual_existing_label=row['label'],prediction=result['label'],explanation=explanation))
 support=explanation.get('supporting_blocks',[])
 summary.append(dict(sample_id=row['sample_id'],actual=row['label'],predicted=result['label'],method=explanation['method'],strongest_support=support[0]['text'][:250] if support else explanation.get('normalized_matched_text'),score_drop=support[0]['target_score_drop'] if support else None))
 print(row['sample_id'],result['label'],explanation['method'],flush=True)
csvout(out/'summary.csv',summary);dump(out/'completion.json',dict(records=len(chosen),model_changed=False,historical_test_inputs_opened=0))

