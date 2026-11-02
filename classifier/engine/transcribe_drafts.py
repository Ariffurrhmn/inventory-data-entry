"""Prepare OCR drafts for annotation; drafts are never ground truth."""
import csv,hashlib,json,os,subprocess,tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from PIL import Image,ImageOps,ImageEnhance
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
ANNOTATIONS=ROOT/"Dataset/annotations"
def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument("--workers",type=int,default=3);args=p.parse_args()
 rows=list(csv.DictReader((HERE/"data/splits.csv").open(encoding="utf-8",newline="")))
 out=ANNOTATIONS/"ocr_drafts";out.mkdir(parents=True,exist_ok=True)
 tessdata=HERE/".cache/tessdata"
 def process(row):
  target=out/(row["sample_id"]+".json")
  if target.exists():return row["sample_id"],"cached"
  image=HERE/row["image_path"]
  with tempfile.TemporaryDirectory() as tmp:
   with Image.open(image) as raw:
    im=ImageOps.exif_transpose(raw).convert("RGB")
    # Enlarge small images for OCR only. Never overwrite image sources.
    if im.width<1400:
     scale=min(3,1400/im.width);im=im.resize((int(im.width*scale),int(im.height*scale)),Image.Resampling.LANCZOS)
    prepared=Path(tmp)/"page.png";im.save(prepared)
   env=os.environ.copy();env["OMP_THREAD_LIMIT"]="1"
   base=Path(tmp)/"ocr"
   result=subprocess.run(["tesseract",str(prepared),str(base),"--tessdata-dir",str(tessdata),"-l","eng","--psm","3","-c","tessedit_create_txt=1","-c","tessedit_create_tsv=1"],capture_output=True,text=True,env=env,timeout=120)
   if result.returncode:raise RuntimeError(row["source_path"]+": "+result.stderr)
   words=[]
   for w in csv.DictReader((base.with_suffix(".tsv")).open(encoding="utf-8"),delimiter="\t",quoting=csv.QUOTE_NONE):
    if w["text"].strip():words.append(dict(text=w["text"],confidence=float(w["conf"]),box=[int(w[k]) for k in ["left","top","width","height"]],block=int(w["block_num"]),paragraph=int(w["par_num"]),line=int(w["line_num"])))
   payload=dict(sample_id=row["sample_id"],source_path=row["source_path"],source_sha256=row["sha256"],prepared_image_path=row["image_path"],
    prepared_image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),label=row["label"],split=row["split"],
    status="unreviewed_ocr_draft",engine="Tesseract 5.5.3, tessdata_best eng, PSM 3",
    full_text=base.with_suffix(".txt").read_text(encoding="utf-8"),ocr_image_size=list(im.size),words=words)
   target.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
  return row["sample_id"],"done"
 count=0;errors=[]
 with ThreadPoolExecutor(max_workers=args.workers) as pool:
  futures={pool.submit(process,r):r for r in rows}
  for f in as_completed(futures):
   try:f.result();count+=1
   except Exception as e:errors.append(str(e));print(repr(e),flush=True)
   if count%10==0:print(f"OCR drafts: {count}/{len(rows)}; errors: {len(errors)}",flush=True)
 (ANNOTATIONS/"draft_status.json").write_text(json.dumps(dict(expected=len(rows),completed=count,errors=errors),indent=2))
 if errors:raise SystemExit("\n".join(errors))
 print("All drafts completed. Visual annotation still required.",flush=True)
if __name__=="__main__":main()
