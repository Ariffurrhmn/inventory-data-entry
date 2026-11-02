"""Reference annotation management. OCR drafts remain separate from visual review."""
import argparse,csv,json,hashlib
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=ROOT/"Dataset/annotations"
ROWS=list(csv.DictReader((HERE/"data/splits.csv").open(encoding="utf-8",newline="")))
def export(output=None):
 output=Path(output).resolve() if output is not None else BASE
 if output != BASE.resolve():
  output.mkdir(parents=True,exist_ok=False)
 actions=json.loads((BASE/"review_actions.json").read_text(encoding="utf-8")) if (BASE/"review_actions.json").exists() else {}
 refs=output/"transcriptions";refs.mkdir(exist_ok=True)
 index=[]
 for i,row in enumerate(ROWS,1):
  draft_path=BASE/"ocr_drafts"/(row["sample_id"]+".json")
  if not draft_path.exists():continue
  draft=json.loads(draft_path.read_text(encoding="utf-8"));a=actions.get(str(i))
  text=(a.get("text",draft["full_text"]) if a else draft["full_text"]).strip()
  for old,new in (a.get("replace",[]) if a else []):text=text.replace(old,new)
  payload=dict(schema_version="1.0",sample_id=row["sample_id"],source_image=dict(path=row["source_path"],sha256=row["sha256"]),
   prepared_image=dict(path="classifier/engine/"+row["image_path"],sha256=draft["prepared_image_sha256"]),
   classification=dict(label=row["label"],split=row["split"]),transcription=dict(full_text=text,lines=text.splitlines(),reading_order="top-to-bottom, left-to-right; tables may be linearized"),
   review=dict(status="assistant_visual_reviewed" if a else "unreviewed_ocr_draft",reviewer="Codex" if a else None,human_verified=False,
   uncertainties=a.get("uncertainties",[]) if a else [],notes=a.get("notes","") if a else "OCR draft only; not a reference truth."),
   provenance=dict(ocr_draft="Dataset/annotations/ocr_drafts/"+draft_path.name,method="OCR-assisted visual transcription" if a else "Tesseract OCR draft",date="2026-10-19"),
   usage=dict(ocr_evaluation="exclude uncertainty markers and unresolved spans; human audit recommended" if a else "not eligible until reviewed",
    classifier_input="Use transcription text only, never label, filename, split, notes, or reviewer metadata. Fit text features on train only."))
  (refs/draft_path.name).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
  index.append(dict(number=i,sample_id=row["sample_id"],source_path=row["source_path"],label=row["label"],split=row["split"],transcription="transcriptions/"+draft_path.name,status=payload["review"]["status"],uncertainties=len(payload["review"]["uncertainties"])))
 with (output/"index.csv").open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(index[0]));w.writeheader();w.writerows(index)
 print(f"Reference JSON files: {len(index)}; visually reviewed: {sum(r['status']=='assistant_visual_reviewed' for r in index)}; expected: {len(ROWS)}")
def batch(start,end):
 directory=BASE/"review_pages";directory.mkdir(exist_ok=True)
 for begin in range(start,end+1,2):
  selected=list(enumerate(ROWS[begin-1:min(end,begin+1)],begin))
  sheet=Image.new("RGB",(2000,1480),"#dddddd");draw=ImageDraw.Draw(sheet)
  for j,(i,row) in enumerate(selected):
   with Image.open(HERE/row["image_path"]) as im:thumb=ImageOps.contain(im.convert("RGB"),(980,1410))
   x=j*1000;sheet.paste(thumb,(x+(1000-thumb.width)//2,30))
   draw.text((x+8,5),str(i)+" | "+row["source_path"],fill="black")
   draft=json.loads((BASE/"ocr_drafts"/(row["sample_id"]+".json")).read_text(encoding="utf-8"))
   print(json.dumps(dict(number=i,id=row["sample_id"],source=row["source_path"],text=draft["full_text"]),ensure_ascii=False))
  sheet.save(directory/f"{begin:03d}.jpg",quality=96)
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("action",choices=["export","batch"]);p.add_argument("start",type=int,nargs="?",default=1);p.add_argument("end",type=int,nargs="?",default=2);p.add_argument("--output",type=Path,help="New output directory; existing directory is refused");a=p.parse_args()
 if a.action=="export":export(a.output)
 else:batch(a.start,a.end)
