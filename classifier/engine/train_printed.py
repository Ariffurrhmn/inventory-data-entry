"""Train a printed-only OCR classifier without opening historical test inputs."""
import argparse,csv,json,platform,warnings
from pathlib import Path
from collections import Counter,defaultdict
import joblib,numpy as np,sklearn
from sklearn.exceptions import ConvergenceWarning
from text_common import HERE,ROOT,CLASSES,sha,clean_text
from run_text_experiment import pipeline,metrics
from ocr_v2 import combine_outputs

SCOPE=ROOT/'Dataset/annotations/scope/printed-only-v1/eligible_manifest.csv'

def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def csvout(path,rows):
 with path.open('w',encoding='utf-8',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def development_split(rows):
 result=[]
 for source in rows:
  row=dict(source);row['historical_split']=row['split']
  row['development_group']='bridge:printed-generator' if ':bridge-' in row['group_id'] else row['group_id']
  # Keep the related Bridge document styles across all classes together.
  row['split']='test' if source['split']=='test' else 'val' if source['split']=='val' or row['development_group']=='bridge:printed-generator' else 'train'
  result.append(row)
 groups=defaultdict(set)
 for row in result:
  if row['split']!='test':groups[row['development_group']].add(row['split'])
 assert all(len(splits)==1 for splits in groups.values()),'Family crosses development train/validation'
 for split in ['train','val']:
  assert {r['label'] for r in result if r['split']==split}==set(CLASSES),'Every class required in train/validation'
 assert {r['sample_id'] for r in rows if r['split']=='test'}=={r['sample_id'] for r in result if r['split']=='test'}
 return result

def load_ocr(row,policy):
 directory=HERE/'runs'/('text_preliminary/ocr' if policy=='baseline' else 'text_delivery_v2/ocr_sparse')
 path=directory/(row['sample_id']+'.json');raw=json.loads(path.read_text(encoding='utf-8'))
 assert raw['sample_id']==row['sample_id'] and raw['image_sha256']==row['image_sha256']
 assert raw['policy']['psm']==(3 if policy=='baseline' else 11)
 return raw['full_text'],dict(sample_id=row['sample_id'],policy=policy,cache=path.relative_to(ROOT).as_posix(),cache_sha256=sha(path),image_sha256=raw['image_sha256'])

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--run',default='printed_v1_grouped');args=parser.parse_args()
 out=HERE/'runs'/args.run;out.mkdir(exist_ok=False)
 original=list(csv.DictReader(SCOPE.open(encoding='utf-8')));rows=development_split(original)
 protected=[SCOPE,HERE/'data/splits.csv',HERE/'data/manifest.csv',HERE/'labels.csv',HERE/'runs/text_preliminary/evaluation.json',HERE/'runs/text_preliminary/original_ocr.joblib']
 before={p.relative_to(ROOT).as_posix():sha(p) for p in protected}
 counts={split:dict(Counter(r['label'] for r in rows if r['split']==split)) for split in ['train','val','test']}
 spec=dict(scope_version='printed-only-v1',scope_manifest_sha256=sha(SCOPE),split_rule='Keep historical test IDs untouched; retain historical validation; move complete Bridge generator family into development validation across all classes.',candidate_policies=['baseline','sparse','combined'],model='Fixed training-only word TF-IDF 1-2 and character 3-5 TF-IDF, balanced logistic regression C=1, random_state=42',selection='Maximum validation macro-F1; ties prefer baseline, sparse, combined in that order',class_counts=counts,test_images_or_text_opened=0,historical_test_usage='Excluded entirely, including five Bridge relatives of development validation. Not an independent new test.',refit_on_validation=False,python=platform.python_version(),sklearn=sklearn.__version__)
 dump(out/'experiment_spec.json',spec);dump(out/'protected_before.json',before);csvout(out/'split_manifest.csv',rows)
 print(json.dumps(counts),flush=True)
 development=[r for r in rows if r['split']!='test'];train=[r for r in development if r['split']=='train'];val=[r for r in development if r['split']=='val']
 audit=[];texts={}
 for row in development:
  a,aa=load_ocr(row,'baseline');b,bb=load_ocr(row,'sparse');audit.extend([aa,bb])
  texts[row['sample_id']]={'baseline':a,'sparse':b,'combined':combine_outputs(a,b)}
 dump(out/'ocr_input_audit.json',audit)
 predictions=[];results={}
 for policy in spec['candidate_policies']:
  model=pipeline()
  with warnings.catch_warnings(record=True) as caught:
   warnings.simplefilter('always',ConvergenceWarning)
   model.fit([clean_text(texts[r['sample_id']][policy]) for r in train],[r['label'] for r in train])
   assert not any(issubclass(w.category,ConvergenceWarning) for w in caught),'Classifier failed to converge'
  inputs=[clean_text(texts[r['sample_id']][policy]) for r in val];pred=model.predict(inputs);scores=model.predict_proba(inputs)
  result=metrics([r['label'] for r in val],pred);results[policy]=result
  joblib.dump(model,out/(policy+'.joblib'));loaded=joblib.load(out/(policy+'.joblib'))
  assert np.array_equal(loaded.predict(inputs),pred)
  csvout(out/(policy+'_confusion.csv'),[dict(actual=label,**dict(zip(CLASSES,result['confusion_matrix'][i]))) for i,label in enumerate(CLASSES)])
  for r,label,prob in zip(val,pred,scores):predictions.append(dict(policy=policy,sample_id=r['sample_id'],actual=r['label'],predicted=label,correct=bool(label==r['label']),ocr_empty=not bool(clean_text(texts[r['sample_id']][policy])),max_uncalibrated_score=float(max(prob))))
  print(policy,result['correct'],'/',result['n'],'macro-F1',round(result['macro_f1'],4),flush=True)
 selected=max(spec['candidate_policies'],key=lambda p:results[p]['macro_f1'])
 selection=dict(selected=selected,ocr_policy=selected,scope_version='printed-only-v1',validation_macro_f1=results[selected]['macro_f1'],validation_accuracy=results[selected]['accuracy'],selection_rule=spec['selection'],new_test_result=None,test_images_opened=0)
 dump(out/'selection.json',selection);dump(out/'validation.json',dict(candidates=results,selection=selection,training_records=len(train),validation_records=len(val),historical_test_excluded=len(rows)-len(development),class_order=CLASSES,empty_ocr_by_policy={p:sum(not bool(clean_text(texts[r['sample_id']][p])) for r in development) for p in spec['candidate_policies']},limitations=['Small development validation reused from prior work; not an independent final test.','Five excluded historical test records share the broader Bridge family with validation; they were not opened or evaluated.','Validation delivery notes are three synthetic printed Bridge photos, not real new businesses.','Synthetic generator families grouped using known metadata; exhaustive provenance independence is unproven.','Existing reviewed labels include unresolved payment/language questions.','Scores are not calibrated; handwriting detection is not implemented.']))
 csvout(out/'validation_predictions.csv',predictions)
 for path,h in before.items():assert sha(ROOT/path)==h,path
 # Freeze activation only after artifacts and source-preservation checks succeed.
 active=HERE/'active_text_model.json'
 if active.exists():dump(out/'previous_active_model.json',json.loads(active.read_text(encoding='utf-8')))
 pointer=dict(run=args.run,model=selected,model_sha256=sha(out/(selected+'.joblib')),scope_version='printed-only-v1',ocr_policy=selected,selected_by='printed development validation macro-F1',test_result=None)
 temporary=active.with_suffix('.tmp');dump(temporary,pointer);temporary.replace(active)
 dump(out/'completion.json',dict(activated=pointer,protected_files_unchanged=len(before),historical_test_inputs_opened=0,train=len(train),validation=len(val)))
 print('Activated',args.run,selected,flush=True)
if __name__=='__main__':main()
