"""Bounded train/validation-only OCR recovery experiment. Never evaluates test images."""
import csv,json,subprocess,warnings
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import joblib,numpy as np
from sklearn.exceptions import ConvergenceWarning
from text_common import HERE,ROOT,CLASSES,clean_text,score_text,edit_distance,sha
from ocr_v2 import sparse_ocr,combine_outputs,SPARSE_POLICY
from run_text_experiment import pipeline,metrics,csvout,dump
def main():
 old=HERE/"runs/text_preliminary";out=HERE/"runs/text_delivery_v2";out.mkdir(exist_ok=True)
 if (out/"validation.json").exists():raise SystemExit("Completed validation run exists; preserve it.")
 originals=list(csv.DictReader((HERE/"data/splits.csv").open(encoding="utf-8")))
 rows=list(csv.DictReader((old/"experiment_manifest.csv").open(encoding="utf-8")))
 # Remove the exposed test rows before opening any OCR cache/image/reference.
 rows=[r for r in rows if r["split"] in {"train","val"} and r["include"]=="yes"]
 assert len(rows)==203
 ids={r["sample_id"] for r in rows}
 forbidden={r["sample_id"] for r in originals if r["split"]=="test"}
 assert not ids&forbidden
 before={str(p.relative_to(ROOT)):sha(p) for p in [HERE/"labels.csv",HERE/"data/manifest.csv",HERE/"data/splits.csv",old/"evaluation.json",old/"selection.json",old/"original_ocr.joblib"]}
 spec=dict(date="2026-10-19",purpose="recover document text lost by automatic page segmentation",scope="train/validation only; no new test evaluation",policy=SPARSE_POLICY,candidates=["sparse_original","combined_original","sparse_augmented","combined_augmented"],unchanged_classifier="word1-2/char_wb3-5 TF-IDF, balanced LR C1, seed42",selection="highest validation macro-F1; ties favor fewer training records then sparse policy; promote only if beats frozen selected original_ocr validation macro-F1",protected_before=before,original_train=86,augmented_train=177,validation=26,test_images_opened=0)
 dump(out/"spec.json",spec)
 cache=out/"ocr_sparse";cache.mkdir(exist_ok=True)
 baseline={};sparse={}
 for r in rows:
  d=json.loads((old/"ocr"/(r["sample_id"]+".json")).read_text(encoding="utf-8"))
  assert sha(ROOT/r["image_path"])==d["image_sha256"]
  baseline[r["sample_id"]]=d["full_text"]
 def process(r):
  sid=r["sample_id"];p=cache/(sid+".json")
  if p.exists():
   d=json.loads(p.read_text(encoding="utf-8"));assert d["policy"]==SPARSE_POLICY and d["image_sha256"]==sha(ROOT/r["image_path"]);return sid,d["full_text"]
  text=sparse_ocr(ROOT/r["image_path"])
  dump(p,dict(sample_id=sid,policy=SPARSE_POLICY,image_sha256=sha(ROOT/r["image_path"]),full_text=text,status="unreviewed_OCR_output"))
  return sid,text
 done=0
 with ThreadPoolExecutor(max_workers=4) as pool:
  for f in as_completed([pool.submit(process,r) for r in rows]):
   sid,text=f.result();sparse[sid]=text;done+=1
   if done%25==0:print(f"Sparse OCR {done}/{len(rows)} (train/validation only)",flush=True)
 text_for=lambda r,mode:clean_text(sparse[r["sample_id"]] if mode=="sparse" else combine_outputs(baseline[r["sample_id"]],sparse[r["sample_id"]]))
 train=[r for r in rows if r["split"]=="train" and r["source"]=="original"]
 augmented=[r for r in rows if r["split"]=="train"]
 val=[r for r in rows if r["split"]=="val"]
 results={};prediction_rows=[];models={}
 warnings.simplefilter("error",ConvergenceWarning)
 for name,mode,training in [("sparse_original","sparse",train),("combined_original","combined",train),("sparse_augmented","sparse",augmented),("combined_augmented","combined",augmented)]:
  model=pipeline();model.fit([text_for(r,mode) for r in training],[r["label"] for r in training]);models[name]=model
  joblib.dump(model,out/(name+".joblib"))
  pred=model.predict([text_for(r,mode) for r in val]);scores=model.predict_proba([text_for(r,mode) for r in val])
  assert np.array_equal(joblib.load(out/(name+".joblib")).predict([text_for(r,mode) for r in val]),pred)
  results[name]=dict(ocr_policy=mode,training=len(training),metrics=metrics([r["label"] for r in val],pred))
  csvout(out/(name+"_confusion.csv"),[dict(label=c,**dict(zip(CLASSES,line))) for c,line in zip(CLASSES,results[name]["metrics"]["confusion_matrix"])],["label"]+CLASSES)
  for r,p,s in zip(val,pred,scores):prediction_rows.append(dict(candidate=name,sample_id=r["sample_id"],expected=r["label"],predicted=p,correct=r["label"]==p,max_score=float(max(s))))
  print(name,results[name]["metrics"]["correct"],"/26",round(results[name]["metrics"]["macro_f1"],4),flush=True)
 ranked=sorted(results,key=lambda k:(-results[k]["metrics"]["macro_f1"],results[k]["training"],results[k]["ocr_policy"]!="sparse"))
 best=ranked[0]
 old_selection=json.loads((old/"selection.json").read_text(encoding="utf-8"));old_name=old_selection["selected"];old_f1=old_selection["validation"][old_name]["macro_f1"]
 promote=results[best]["metrics"]["macro_f1"]>old_f1
 selected=dict(candidate=best,promoted_validation_candidate=promote,previous_run="text_preliminary",previous_candidate=old_name,previous_validation_macro_f1=old_f1,validation_macro_f1=results[best]["metrics"]["macro_f1"],ocr_policy=results[best]["ocr_policy"],new_test_result=None,test_images_opened=0,reason="validation-only comparison; no test-based promotion")
 dump(out/"selection.json",selected)
 # Whole-page OCR comparison only for train/validation references eligible under the old scoring policy.
 old_quality=list(csv.DictReader((old/"ocr_quality_documents.csv").open(encoding="utf-8")))
 eligible={r["sample_id"] for r in old_quality if r["split"] in {"train","val"} and r["included"]=="True"}
 quality=[];coverage=[];ref_before={}
 for r in rows:
  sid=r["sample_id"]
  coverage.append(dict(sample_id=sid,split=r["split"],label=r["label"],baseline_characters=len(baseline[sid].strip()),sparse_characters=len(sparse[sid].strip()),baseline_empty=not baseline[sid].strip(),sparse_empty=not sparse[sid].strip()))
  if sid not in eligible:continue
  path=ROOT/"Dataset/annotations/transcriptions"/(sid+".json");ref_before[str(path.relative_to(ROOT))]=sha(path)
  reference=json.loads(path.read_text(encoding="utf-8"))["transcription"]["full_text"];ref=score_text(reference)
  for policy,text in [("baseline",baseline[sid]),("sparse",sparse[sid])]:
   hypo=score_text(text);quality.append(dict(sample_id=sid,split=r["split"],policy=policy,reference_characters=len(ref),character_edits=edit_distance(ref,hypo),reference_words=len(ref.split()),word_edits=edit_distance(ref.split(),hypo.split())))
 summaries={}
 for policy in ["baseline","sparse"]:
  q=[r for r in quality if r["policy"]==policy];nc=sum(r["reference_characters"] for r in q);nw=sum(r["reference_words"] for r in q)
  summaries[policy]=dict(documents=len(q),cer=sum(r["character_edits"] for r in q)/nc if nc else None,wer=sum(r["word_edits"] for r in q)/nw if nw else None)
 # Diagnostic text exports only for known train/validation errors; not corrected references.
 failure_ids={r["sample_id"] for r in csv.DictReader((old/"predictions.csv").open(encoding="utf-8")) if r["split"]=="val" and r["scenario"]==old_name and r["correct"]=="False"}
 diagnostics=out/"diagnostic_text";diagnostics.mkdir(exist_ok=True)
 for sid in failure_ids:
  assert sid in ids and sid not in forbidden
  (diagnostics/(sid+".txt")).write_text("BASELINE OCR:\n"+baseline[sid]+"\nSPARSE OCR:\n"+sparse[sid],encoding="utf-8")
 for p,h in {**before,**ref_before}.items():assert sha(ROOT/p)==h,"Protected file changed: "+p
 csvout(out/"coverage.csv",coverage,list(coverage[0]));csvout(out/"ocr_quality_documents.csv",quality,list(quality[0]));csvout(out/"validation_predictions.csv",prediction_rows,list(prediction_rows[0]))
 dump(out/"validation.json",dict(selection=selected,candidates=results,ocr_quality=summaries,baseline_empty=sum(r["baseline_empty"] for r in coverage),sparse_empty=sum(r["sparse_empty"] for r in coverage),empty_recovered=sum(r["baseline_empty"] and not r["sparse_empty"] for r in coverage),test_images_opened=0,protected_files_unchanged=len(before)+len(ref_before),limitations=["Validation reused adaptively; fresh independent holdout still required.","Sparse mode changes reading order; CER/WER are not pure recognition accuracy.","AI reference truth; no independently verified labels.","No new test or fresh real holdout evaluation."]))
 print(json.dumps(dict(selection=selected,ocr_quality=summaries,baseline_empty=sum(r["baseline_empty"] for r in coverage),sparse_empty=sum(r["sparse_empty"] for r in coverage)),indent=2),flush=True)
if __name__=="__main__":main()
