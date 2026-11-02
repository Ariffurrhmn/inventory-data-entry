"""Fix multi-view title-window handling without refitting or changing classifiers."""
import csv,json,shutil
from text_common import HERE,ROOT,sha
from train_printed import dump,csvout,load_ocr
from run_text_experiment import metrics
from heading_rules_v3 import heading_decision
out=HERE/'runs/printed_v3_sections';out.mkdir(exist_ok=False)
parent=HERE/'runs/printed_v2_rules'
dump(out/'experiment_spec.json',dict(parent=parent.name,reason='Concatenating OCR outputs imposed a single 30-line title window: corrected headers in later views were ignored. Preserve view boundaries and inspect each view independently.',model_fitted=False,model_unchanged='Training-group-CV selected ComplementNB',adaptive_design=True,historical_test_inputs_opened=0,code_sha256=sha(HERE/'heading_rules_v3.py')))
shutil.copy2(parent/'split_manifest.csv',out/'split_manifest.csv');shutil.copy2(HERE/'heading_rules_v3.py',out/'heading_rules_v3.py')
rows=list(csv.DictReader((out/'split_manifest.csv').open(encoding='utf8')));lookup={r['sample_id']:r for r in rows}
results={}
for split,name in [('train','training_oof'),('val','validation')]:
 source=parent/('training_oof_predictions.csv' if split=='train' else 'validation_predictions.csv')
 previous=list(csv.DictReader(source.open(encoding='utf8')));records=[];labels=[];actual=[]
 for row in previous:
  r=lookup[row['sample_id']];assert r['split']==split
  views=json.loads((HERE/'runs/printed_v2_illumination/ocr'/(r['sample_id']+'.json')).read_text(encoding='utf8'))['views'];parts=[load_ocr(r,'sparse')[0]]
  if split=='val':parts.append(json.loads((HERE/'runs/printed_v1_edges/ocr_edges'/(r['sample_id']+'.json')).read_text(encoding='utf8'))['full_text'])
  parts.extend(views.values());cue=heading_decision('\f'.join(parts));label=cue['label'] or row['fallback'];labels.append(label);actual.append(r['label'])
  detail=cue.get('rule') or {}
  records.append(dict(sample_id=r['sample_id'],actual=r['label'],predicted=label,fallback=row['fallback'],previous=row['predicted'],rule_kind=detail.get('kind',''),evidence=cue['evidence'] or '',ocr_section=detail.get('ocr_section_index'),ambiguous=cue['ambiguous'],correct=label==r['label']))
 result=metrics(actual,labels);results[name]=result;csvout(out/(name+'_predictions.csv'),records)
 print(name,result['correct'],'/',result['n'],round(result['macro_f1'],4),flush=True)
dump(out/'validation.json',dict(results=results,adaptive_validation=True,training_oof_model='Refitted per grouped training fold in parent run; rule design remains adaptive',historical_test_inputs_opened=0))
for path,digest in json.loads((HERE/'runs/printed_v1_grouped/protected_before.json').read_text(encoding='utf8')).items():assert sha(ROOT/path)==digest
dump(out/'completion.json',dict(metrics=results,activated=False,historical_test_inputs_opened=0))

