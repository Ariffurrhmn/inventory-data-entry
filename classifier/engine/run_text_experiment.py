"""Prespecified preliminary OCR-text baselines; existing corpus is never rewritten."""
import argparse,csv,json,platform,subprocess,time,warnings
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import joblib,numpy as np,sklearn
from sklearn.pipeline import Pipeline,FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score,f1_score,classification_report,confusion_matrix
from sklearn.exceptions import ConvergenceWarning
from text_common import HERE,ROOT,CLASSES,OCR_POLICY,sha,clean_text,score_text,edit_distance,group_guard,ocr_image
def dump(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
def csvout(path,rows,fields):
 with path.open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def pipeline():
 return Pipeline([("features",FeatureUnion([
  ("word",TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,max_features=30000)),
  ("char",TfidfVectorizer(analyzer="char_wb",ngram_range=(3,5),sublinear_tf=True,max_features=50000))
 ])),("classifier",LogisticRegression(C=1.0,class_weight="balanced",solver="lbfgs",max_iter=1000,random_state=42))])
def metrics(y,pred):
 return dict(n=len(y),correct=int(sum(a==b for a,b in zip(y,pred))),accuracy=float(accuracy_score(y,pred)),macro_f1=float(f1_score(y,pred,labels=CLASSES,average="macro",zero_division=0)),class_report=classification_report(y,pred,labels=CLASSES,output_dict=True,zero_division=0),confusion_matrix=confusion_matrix(y,pred,labels=CLASSES).tolist())
def main():
 p=argparse.ArgumentParser();p.add_argument("--run",default="text_preliminary");p.add_argument("--workers",type=int,default=4);args=p.parse_args()
 out=HERE/"runs"/args.run;out.mkdir(exist_ok=True);cache=out/"ocr";cache.mkdir(exist_ok=True)
 if (out/"evaluation.json").exists():raise SystemExit("Completed run exists; preserve it. Use a new run name.")
 originals=list(csv.DictReader((HERE/"data/splits.csv").open(encoding="utf-8")))
 protected=[HERE/s for s in ["labels.csv","data/manifest.csv","data/splits.csv","RESULTS.md"]]
 refs={};ocr={};before={str(p.relative_to(ROOT)):sha(p) for p in protected}
 for row in originals:
  sid=row["sample_id"];path=ROOT/"Dataset/annotations/transcriptions"/(sid+".json")
  before[str(path.relative_to(ROOT))]=sha(path)
  ref=json.loads(path.read_text(encoding="utf-8"));refs[sid]=ref
  assert ref["classification"]==dict(label=row["label"],split=row["split"])
  draft_path=ROOT/"Dataset/annotations/ocr_drafts"/(sid+".json")
  draft=json.loads(draft_path.read_text(encoding="utf-8"));im=HERE/row["image_path"]
  assert draft["prepared_image_sha256"]==sha(im)
  assert draft["source_sha256"]==row["sha256"]
  ocr[sid]=draft["full_text"]
  dump(cache/(sid+".json"),dict(sample_id=sid,image_path=str(im.relative_to(ROOT)),image_sha256=draft["prepared_image_sha256"],full_text=draft["full_text"],origin=str(draft_path.relative_to(ROOT)),policy=OCR_POLICY,status="unreviewed_OCR_output"))
 assert len(originals)==140 and Counter(r["split"] for r in originals)=={"train":86,"val":26,"test":28}
 assignments={}
 for row in originals:
  assignments.setdefault(row["group_id"],set()).add(row["split"])
 assert all(len(v)==1 for v in assignments.values()),"Existing group crosses splits"
 intake=ROOT/"Dataset/intake/2026-10-19/reviewed_records.jsonl"
 additions=[json.loads(s) for s in intake.read_text(encoding="utf-8").splitlines() if s]
 additions=[r for r in additions if r["decision"]=="accepted_visual_review"]
 assert len(additions)==91
 guarded=group_guard(originals,additions,{sid:r["transcription"]["full_text"] for sid,r in refs.items()})
 usable=[r for r in guarded if r["experiment_include"]]
 spec=dict(date="2026-10-19",classes=CLASSES,run=args.run,parameters=dict(word_ngrams=[1,2],char_wb_ngrams=[3,5],C=1.0,class_weight="balanced",max_iter=1000),selection="Choose original_ocr or augmented_ocr by validation macro-F1 only; tie favors original_ocr.",reference_model="diagnostic only; no new reference truth for additional photos",ocr_policy=OCR_POLICY,seed=42,sklearn=sklearn.__version__,python=platform.python_version(),tesseract=subprocess.run(["tesseract","--version"],capture_output=True,text=True).stdout.splitlines()[0],tessdata_sha256=sha(HERE/".cache/tessdata/eng.traineddata"),protected_before=before,reference_policy="Assistant visual review; no independent human verification. Remove bracket annotations from classification features only.",ocr_scoring_policy="NFKC, casefold, collapse whitespace; score only whole original records without any bracket marker or explicit uncertainty; exclude other records entirely, including signature-marked pages. Corpus micro CER/WER; not exact-layout scoring.",evaluation="Frozen 26 validation/28 test; old test previously inspected in image experiments, so exploratory comparison, not fresh final validation.",hypotheses=["reference-trained reference-input diagnostic","reference-trained OCR-input degradation diagnostic","OCR-trained original-only baseline","OCR-trained augmented training-only baseline"])
 dump(out/"experiment_spec.json",spec)
 manifest=[]
 for row in originals:manifest.append(dict(sample_id=row["sample_id"],image_path=str((HERE/row["image_path"]).relative_to(ROOT)),label=row["label"],split=row["split"],group_id=row["group_id"],include="yes",source="original",reason="frozen assignment"))
 for row in guarded:
  manifest.append(dict(sample_id=row["sample_id"],image_path=row["image_path"],label=row["label"],split=row["experiment_split"],group_id=row["group_id"],include="yes" if row["experiment_include"] else "no",source=row["source"],reason=row["guard_reason"]))
 csvout(out/"experiment_manifest.csv",manifest,list(manifest[0]))
 dump(out/"group_audit.json",dict(original_groups=len(assignments),original_split_hash=sha(HERE/"data/splits.csv"),training_only_additions=len(usable),excluded_additions=[dict(sample_id=r["sample_id"],reason=r["guard_reason"]) for r in guarded if not r["experiment_include"]],caveat="Merchant text matching and previous visual/perceptual audits cannot prove exhaustive supplier/template independence. All synthetic additions share one training-only generator group."))
 def extra_ocr(row):
  sid=row["sample_id"];im=ROOT/row["image_path"];dest=cache/(sid+".json");digest=sha(im)
  assert digest==row["prepared_image_sha256"]
  if dest.exists():
   old=json.loads(dest.read_text(encoding="utf-8"));assert old["image_sha256"]==digest and old["policy"]==OCR_POLICY;return sid,old["full_text"]
  text=ocr_image(im);dump(dest,dict(sample_id=sid,image_path=row["image_path"],image_sha256=digest,full_text=text,policy=OCR_POLICY,status="unreviewed_OCR_output"))
  return sid,text
 done=0
 with ThreadPoolExecutor(max_workers=args.workers) as pool:
  for f in as_completed([pool.submit(extra_ocr,r) for r in usable]):
   sid,text=f.result();ocr[sid]=text;done+=1
   if done%20==0:print(f"Consistent OCR on additions: {done}/{len(usable)}",flush=True)
 print("OCR complete; scoring resolved whole reference pages.",flush=True)
 score_rows=[]
 for row in originals:
  sid=row["sample_id"];r=refs[sid];raw=r["transcription"]["full_text"]
  reason="explicit uncertainty" if r["review"]["uncertainties"] else "annotation marker" if __import__("re").search(r"\[[^\]\n]+\]",raw) else ""
  record=dict(sample_id=sid,split=row["split"],label=row["label"],included=not bool(reason),exclusion_reason=reason,reference_characters=0,character_edits=0,reference_words=0,word_edits=0)
  if not reason:
   a=score_text(raw);b=score_text(ocr[sid]);record.update(reference_characters=len(a),character_edits=edit_distance(a,b),reference_words=len(a.split()),word_edits=edit_distance(a.split(),b.split()))
  score_rows.append(record)
 def aggregate(rows):
  chars=sum(r["reference_characters"] for r in rows);words=sum(r["reference_words"] for r in rows)
  return dict(documents=sum(r["included"] for r in rows),excluded=sum(not r["included"] for r in rows),reference_characters=chars,reference_words=words,cer=sum(r["character_edits"] for r in rows)/chars if chars else None,wer=sum(r["word_edits"] for r in rows)/words if words else None)
 dump(out/"ocr_quality.json",dict(policy=spec["ocr_scoring_policy"],all=aggregate(score_rows),by_split={s:aggregate([r for r in score_rows if r["split"]==s]) for s in ["train","val","test"]},by_class={c:aggregate([r for r in score_rows if r["label"]==c]) for c in CLASSES},preliminary=True,human_verified=False))
 csvout(out/"ocr_quality_documents.csv",score_rows,list(score_rows[0]))
 datasets={s:[r for r in originals if r["split"]==s] for s in ["train","val","test"]}
 reftext=lambda row:clean_text(refs[row["sample_id"]]["transcription"]["full_text"])
 ocrtext=lambda row:clean_text(ocr[row["sample_id"]])
 models={};validation={};warnings.simplefilter("error",ConvergenceWarning)
 for name,training,kind in [("reference",datasets["train"],"reference"),("original_ocr",datasets["train"],"ocr"),("augmented_ocr",datasets["train"]+usable,"ocr")]:
  texts=[reftext(r) if kind=="reference" else ocrtext(r) for r in training]
  model=pipeline();model.fit(texts,[r["label"] for r in training]);models[name]=model
  joblib.dump(model,out/(name+".joblib"))
  check=joblib.load(out/(name+".joblib"))
  assert np.array_equal(model.predict(texts[:2]),check.predict(texts[:2]))
  predictions=model.predict([ocrtext(r) for r in datasets["val"]])
  validation[name]=metrics([r["label"] for r in datasets["val"]],predictions)
  print(name,"train",len(training),"validation macro-F1",round(validation[name]["macro_f1"],4),flush=True)
 selected=max(["original_ocr","augmented_ocr"],key=lambda k:validation[k]["macro_f1"])
 # Commit validation-only selection to disk before any test predictions.
 dump(out/"selection.json",dict(selected=selected,validation=validation,rule=spec["selection"]))
 evaluations={};prediction_rows=[]
 scenarios=[("reference_on_reference","reference",reftext),("reference_on_ocr","reference",ocrtext),("original_ocr","original_ocr",ocrtext),("augmented_ocr","augmented_ocr",ocrtext)]
 for scenario,name,textfn in scenarios:
  evaluations[scenario]={}
  for split in ["val","test"]:
   rows=datasets[split];texts=[textfn(r) for r in rows];pred=models[name].predict(texts);probs=models[name].predict_proba(texts)
   evaluations[scenario][split]=metrics([r["label"] for r in rows],pred)
   csvout(out/(scenario+"_"+split+"_confusion.csv"),[dict(label=c,**dict(zip(CLASSES,line))) for c,line in zip(CLASSES,evaluations[scenario][split]["confusion_matrix"])],["label"]+CLASSES)
   for r,guess,scores in zip(rows,pred,probs):
    prediction_rows.append(dict(scenario=scenario,split=split,sample_id=r["sample_id"],expected=r["label"],predicted=guess,correct=r["label"]==guess,max_score=float(max(scores)),ocr_empty=not bool(ocrtext(r)),source_path=r["source_path"]))
 for p,h in before.items():assert sha(ROOT/p)==h,"Protected file changed: "+p
 result=dict(selected=selected,training_original=86,training_augmented=86+len(usable),validation=26,test=28,classes=CLASSES,evaluations=evaluations,protected_files_unchanged=len(before),empty_original_ocr=[r["sample_id"] for r in originals if not ocrtext(r)],empty_additional_ocr=[r["sample_id"] for r in usable if not ocrtext(r)],preliminary=True,score_calibrated=False)
 csvout(out/"predictions.csv",prediction_rows,list(prediction_rows[0]));dump(out/"evaluation.json",result)
 print(json.dumps(dict(selected=selected,augmented_training=86+len(usable),tests={k:dict(correct=v["test"]["correct"],n=v["test"]["n"],macro_f1=v["test"]["macro_f1"]) for k,v in evaluations.items()},ocr_quality=json.loads((out/"ocr_quality.json").read_text())["all"]),indent=2),flush=True)
if __name__=="__main__":main()
