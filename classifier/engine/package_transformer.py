"""Package and verify the winning transformer before changing the active pointer."""
import csv,json,shutil
import joblib,numpy as np
from text_common import HERE,ROOT,sha
from train_printed import dump,csvout,load_ocr
from transformer_models import TransformerClassifier
from inference import Predictor

def main():
 source=HERE/'runs/printed_v1_transformers';out=HERE/'runs/printed_v1_minilm';out.mkdir(exist_ok=False)
 outcome=json.loads((source/'completion.json').read_text(encoding='utf-8'));assert outcome['best']=='minilm_c1_headings' and outcome['improved']
 parent=HERE/'runs/printed_v1_edges';active=HERE/'active_text_model.json';old=json.loads(active.read_text(encoding='utf-8'));assert old['run']==parent.name
 info=json.loads((source/'all-MiniLM-L6-v2_source.json').read_text(encoding='utf-8'))
 lr=joblib.load(source/'minilm_c1.joblib')
 wrapper=TransformerClassifier('minilm',info['local_path'],info['files'],lr.classes_,lr)
 joblib.dump(wrapper,out/'minilm.joblib')
 selected=dict(json.loads((parent/'selection.json').read_text(encoding='utf-8')),selected='minilm',backend='minilm',transformer_code_sha256=sha(HERE/'transformer_models.py'),validation_accuracy=outcome['metrics']['accuracy'],validation_macro_f1=outcome['metrics']['macro_f1'],source_run=source.name,validation_adaptive=True)
 dump(out/'selection.json',selected);dump(out/'previous_active_model.json',old);dump(out/'public_weights.json',info)
 for name in ['split_manifest.csv','heading_rules.py','edge_ocr.py']:shutil.copy2(parent/name,out/name)
 shutil.copy2(HERE/'transformer_models.py',out/'transformer_models.py')
 shutil.copytree(parent/'ocr_edges',out/'ocr_edges')
 expected=[r for r in csv.DictReader((source/'validation_predictions.csv').open(encoding='utf-8')) if r['candidate']==outcome['best']]
 csvout(out/'validation_predictions.csv',expected)
 dump(out/'validation.json',dict(metrics=outcome['metrics'],validation_adaptive=True,historical_test_inputs_opened=0,source_run=source.name))
 predictor=Predictor(out.name)
 rows=list(csv.DictReader((out/'split_manifest.csv').open(encoding='utf-8')));val=[r for r in rows if r['split']=='val']
 texts=[load_ocr(r,'sparse')[0] for r in val]
 expected_by_id={r['sample_id']:r['predicted'] for r in expected}
 from transformer_models import minilm_features
 feature=minilm_features(predictor.model._tokenizer,predictor.model._encoder,texts)
 np.testing.assert_allclose(feature,np.load(source/'minilm_features.npy')[150:],atol=1e-6,rtol=1e-6)
 for row,t in zip(val,texts):
  edge=json.loads((out/'ocr_edges'/(row['sample_id']+'.json')).read_text(encoding='utf-8'))['full_text']
  result=predictor.predict_text(t,heading_text=t+'\n'+edge)
  assert result['label']==expected_by_id[row['sample_id']],row['sample_id']
 before=json.loads((source/'protected_before.json').read_text(encoding='utf-8'))
 for path,digest in before.items():assert sha(ROOT/path)==digest,path
 for run in [source,HERE/'runs/printed_v1_fusion']:
  dump(run/'code_provenance.json',dict(files={p.name:sha(p) for p in [HERE/'train_transformers.py',HERE/'train_transformer_fusion.py',HERE/'transformer_models.py']}))
 pointer=dict(old,run=out.name,model='minilm',model_sha256=sha(out/'minilm.joblib'),backend='minilm',selected_by='Adaptive development validation: frozen MiniLM start/end embeddings and trained LR, with unchanged heading/edge rules')
 temporary=active.with_suffix('.tmp');dump(temporary,pointer);temporary.replace(active)
 dump(out/'completion.json',dict(activated=pointer,validation_predictions_reproduced=25,encoder_features_reproduced=True,protected_before_activation=len(before),historical_test_inputs_opened=0))
 print('Activated',out.name,'20/25; persisted encoder features and predictions verified',flush=True)
if __name__=='__main__':main()

