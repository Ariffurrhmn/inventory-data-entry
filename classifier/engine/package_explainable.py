"""Package the selected explainable pipeline; no UI launch or repeated image OCR."""
import csv,json,shutil
from collections import Counter
import joblib
from text_common import HERE,ROOT,sha
from train_printed import dump,csvout,load_ocr
from inference import Predictor
from explain import explain_prediction
from run_text_experiment import metrics

def main():
 source=HERE/'runs/printed_v3_sections';summary=json.loads((source/'completion.json').read_text(encoding='utf8'));assert summary['metrics']['validation']['accuracy']>=.9
 out=HERE/'runs/printed_v3_explainable';out.mkdir(exist_ok=False);(out/'explanations').mkdir()
 chosen=json.loads((HERE/'runs/printed_v2_groupcv/completion.json').read_text(encoding='utf8'))['selected_by_training_cv'];assert chosen=='complement_nb'
 shutil.copy2(HERE/'runs/printed_v2_groupcv'/(chosen+'.joblib'),out/'classifier.joblib')
 for filename in ['heading_rules.py','heading_rules_v2.py','heading_rules_v3.py','illumination_ocr.py','edge_ocr.py','explain.py','inference.py']:shutil.copy2(HERE/filename,out/filename)
 for filename in ['split_manifest.csv','validation_predictions.csv','validation.json','training_oof_predictions.csv']:shutil.copy2(source/filename,out/filename)
 current=summary['metrics']['validation']
 selection=dict(selected='classifier',backend='complement_nb',ocr_policy='illumination',illumination_recovery=True,illumination_code_sha256=sha(HERE/'illumination_ocr.py'),heading_rules=True,heading_module='heading_rules_v3',heading_rule_sha256=sha(HERE/'heading_rules_v3.py'),rule_dependencies={n:sha(HERE/n) for n in ['heading_rules.py','heading_rules_v2.py']},edge_recovery=True,edge_code_sha256=sha(HERE/'edge_ocr.py'),scope_version='printed-only-v1',validation_accuracy=current['accuracy'],validation_macro_f1=current['macro_f1'],adaptive_validation=True,new_test_result=None,historical_test_inputs_opened=0,source_run=source.name,training_group_cv_run='printed_v2_groupcv',explanation_code_sha256=sha(HERE/'explain.py'))
 dump(out/'selection.json',selection);predictor=Predictor(out.name)
 rows={r['sample_id']:r for r in csv.DictReader((out/'split_manifest.csv').open(encoding='utf8'))}
 expected=list(csv.DictReader((out/'validation_predictions.csv').open(encoding='utf8')));pred=[];kinds=Counter();max_error=0
 for item in expected:
  r=rows[item['sample_id']];assert r['split']=='val'
  record=json.loads((HERE/'runs/printed_v2_illumination/ocr'/(r['sample_id']+'.json')).read_text(encoding='utf8'));assert record['image_sha256']==r['image_sha256'];views=record['views']
  sparse=load_ocr(r,'sparse')[0];edge=json.loads((HERE/'runs/printed_v1_edges/ocr_edges'/(r['sample_id']+'.json')).read_text(encoding='utf8'))['full_text'];context='\f'.join([sparse,edge]+list(views.values()))
  result=predictor.predict_text(views['full'],heading_text=context);assert result['label']==item['predicted'],r['sample_id'];pred.append(result['label'])
  explanation=explain_prediction(predictor,views['full'],heading_text=context,result=result);kinds[explanation['method']]+=1;max_error=max(max_error,explanation.get('reconstruction_error',0))
  dump(out/'explanations'/(r['sample_id']+'.json'),dict(sample_id=r['sample_id'],actual_existing_label=r['label'],result=result,explanation=explanation))
 measured=metrics([item['actual'] for item in expected],pred);assert measured['accuracy']==current['accuracy']
 protected=json.loads((HERE/'runs/printed_v1_grouped/protected_before.json').read_text(encoding='utf8'))
 for path,digest in protected.items():assert sha(ROOT/path)==digest,path
 active=HERE/'active_text_model.json';dump(out/'previous_active_model.json',json.loads(active.read_text(encoding='utf8')))
 pointer=dict(run=out.name,model='classifier',backend='complement_nb',model_sha256=sha(out/'classifier.joblib'),scope_version='printed-only-v1',ocr_policy='illumination',heading_rules=True,heading_module='heading_rules_v3',edge_recovery=True,illumination_recovery=True,selected_by='Training-only grouped-CV selected fallback; adaptive corrected-OCR/rule follow-ups',test_result=None)
 temporary=active.with_suffix('.tmp');dump(temporary,pointer);temporary.replace(active)
 dump(out/'completion.json',dict(selected=pointer,validation=measured,training_oof=summary['metrics']['training_oof'],persisted_validation_predictions_reproduced=25,explanations=dict(kinds),max_explanation_reconstruction_error=max_error,protected_source_files_unchanged=len(protected),historical_test_inputs_opened=0,server_restarted=False,ui_rerun=False))
 print('Saved selected explainable classifier:',measured['correct'],'/25; grouped OOF',summary['metrics']['training_oof']['correct'],'/150; explanations',dict(kinds),'max algebra error',max_error,flush=True)
if __name__=='__main__':main()

