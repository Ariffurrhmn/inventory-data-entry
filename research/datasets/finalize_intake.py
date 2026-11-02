"""Finalize reviewed intake, without merging data or assigning splits."""
import csv,hashlib,html,json,re
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"Dataset/intake/2026-10-19"
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_csv(name,rows,fields):
 with (BASE/name).open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def main():
 rows=json.loads((BASE/"records.json").read_text(encoding="utf-8"))
 actions=json.loads((BASE/"review_actions.json").read_text(encoding="utf-8"))
 assert len(rows)==240 and set(actions)=={str(i) for i in range(1,241)}
 before=json.loads((BASE/"protected_before.json").read_text())
 for p,h in before.items():assert digest(ROOT/p)==h,f"Protected original changed: {p}"
 manifests=list(csv.DictReader((ROOT/"classifier/engine/data/manifest.csv").open(encoding="utf-8")))
 existing={r["sha256"]:r for r in manifests}
 included=list(csv.DictReader((ROOT/"classifier/engine/data/splits.csv").open(encoding="utf-8")))
 for n in [208,227,237,240]:
  actions[str(n)]["evidence"]="Apparent missing content in overview preview; complete alternate Poppler render visually checked. Stored-image thumbnail differences are small; source corruption was not established. English "+("Purchase Order." if n==208 else "Packing Slip.")
 (BASE/"review_actions.json").write_text(json.dumps(actions,ensure_ascii=False,indent=2),encoding="utf-8")
 final=[];seen=set()
 for r in rows:
  n=r["number"];a=actions[str(n)]
  assert r["sample_id"] not in seen;seen.add(r["sample_id"])
  p=ROOT/(r.get("pdf_path") or r["image_path"])
  assert digest(p)==r["source_sha256"],f"Source bytes changed: {n}"
  with Image.open(ROOT/r["image_path"]) as im:
   im.verify()
  r["prepared_image_sha256"]=digest(ROOT/r["image_path"])
  r["label"]=a["label"];r["decision"]=a["decision"]
  r["review"]=dict(status="assistant_visual_reviewed",reviewer="Codex",human_verified=False,evidence=a["evidence"],review_date="2026-10-19")
  r["split"]="";r["merged_into_training_corpus"]=False
  r["merchant_review_key"]=a["merchant"]
  r["duplicate_of"]=a.get("duplicate_of","")
  r["usage"]="training_supplement_only_after_merge_checks" if r["synthetic"] else "candidate_for_future_grouped_intake"
  r["realworld_transaction_verified"]=False
  r["license"]="Apache-2.0 generated documents; source MIT/BSD notices" if r["synthetic"] else "MIT; cite ExpressExpense.com"
  if not r["synthetic"]:
   r["synthetic"]=None
   r["capture_type"]="publisher_receipt_photograph; transaction authenticity not independently verified"
   r["group_id"]="srd:merchant:"+a["merchant"]
   r["ocr_screening_path"]=str((BASE/"ocr_screening"/(Path(r["source_member"]).stem+".txt")).relative_to(ROOT))
  else:
   r["capture_type"]="synthetic_born_digital_pdf_render"
   r["layout_group"]="company-v2:layout:"+r["layout"]
   r["group_id"]="company-v2:generator"
   m=json.loads((ROOT/r["metadata_path"]).read_text(encoding="utf-8"))
   assert m["locale"]=="en" and m["pages"]==1
   assert m["document_type"]==r["source_document_type"]
   r["publisher_variant"]=m.get("variant")
   r["publisher_source_data"]=m.get("source")
  if r["source_sha256"] in existing:
   old=existing[r["source_sha256"]]
   assert r["decision"]=="excluded_existing_duplicate"
   r["related_existing_sample_id"]=old["sample_id"]
   r["related_existing_group_id"]=old["group_id"]
  if r["decision"]=="accepted_visual_review":
   assert r["label"] in {"receipt","customer_copy","purchase_order","delivery_note"}
   assert not r["overlap_paths"] and not r["duplicate_of"]
  final.append(r)
 byid={r["sample_id"]:r for r in final}
 for r in final:
  if r["duplicate_of"]:assert r["duplicate_of"] in byid
 # Rebuild readable pages for the final Poppler-rendered synthetic images.
 for start in range(200,240,4):
  sheet=Image.new("RGB",(2000,2200),"#ddd");d=ImageDraw.Draw(sheet)
  for j,r in enumerate(final[start:start+4]):
   with Image.open(ROOT/r["image_path"]) as im:thumb=ImageOps.contain(im.convert("RGB"),(980,1030))
   x=(j%2)*1000;y=(j//2)*1100;sheet.paste(thumb,(x+(1000-thumb.width)//2,y+42));d.text((x+8,y+5),str(r["number"])+" | "+r["sample_id"],fill="black")
  sheet.save(BASE/"review_pages"/f"{start+1:03d}.jpg",quality=95)
 # Duplicate screening is evidence for review only, never automatic grouping.
 cos=np.cos(np.pi*(2*np.arange(32)[None,:]+1)*np.arange(32)[:,None]/64)
 def feature(p):
  with Image.open(p) as im:arr=np.asarray(ImageOps.exif_transpose(im).convert("L").resize((32,32),Image.Resampling.LANCZOS),dtype=float)
  v=(cos@arr@cos.T)[:8,:8].flatten()[1:];return v>np.median(v)
 local=[(r,feature(ROOT/"classifier/engine"/r["image_path"])) for r in included]
 screen=[]
 for r in final:
  f=feature(ROOT/r["image_path"])
  for old,g in local:
   dist=int(np.count_nonzero(f!=g))
   if dist<=8:
    screen.append(dict(number=r["number"],sample_id=r["sample_id"],existing_sample_id=old["sample_id"],existing_path=old["source_path"],phash_hamming=dist,status="known_exact_excluded" if old["source_path"] in r["overlap_paths"] else "similarity_candidate_not_identity"))
 write_csv("existing_similarity_candidates.csv",screen,["number","sample_id","existing_sample_id","existing_path","phash_hamming","status"])
 (BASE/"reviewed_records.jsonl").write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in final),encoding="utf-8")
 fields=["number","sample_id","source","source_member","image_path","prepared_image_sha256","source_sha256","synthetic","label","decision","group_id","split","duplicate_of","review_evidence"]
 flat=[{k:(r["review"]["evidence"] if k=="review_evidence" else r.get(k,"")) for k in fields} for r in final]
 write_csv("review_manifest.csv",flat,fields)
 accepted=[r for r in final if r["decision"]=="accepted_visual_review"]
 write_csv("accepted_manifest.csv",[r for r in flat if r["decision"]=="accepted_visual_review"],fields)
 write_csv("held_manifest.csv",[r for r in flat if r["decision"].startswith("hold")],fields)
 write_csv("excluded_manifest.csv",[r for r in flat if r["decision"].startswith("excluded")],fields)
 counts=Counter(r["label"] for r in accepted)
 summary=dict(date="2026-10-19",staged=240,assistant_visual_reviewed=240,human_verified=0,accepted_for_staging=len(accepted),accepted_classes=dict(counts),accepted_sources=dict(Counter(r["source"] for r in accepted)),held=sum(r["decision"].startswith("hold") for r in final),excluded_existing_duplicates=5,excluded_intake_derivatives=4,accepted_unique_image_hashes=len({r["prepared_image_sha256"] for r in accepted}),source_hashes_validated=240,protected_files_unchanged=len(before),existing_training_samples=len(included),merged=0,new_splits_assigned=0,synthetic_revision=json.loads((BASE/"company_documents_v2/revision.json").read_text())["revision"],screening_candidate_rows=len(screen),limitations=["Assistant label review; not independent human verification.","Held bills are not negative training labels.","No full transcription gold truth was created for additions; screening OCR and publisher PDF text remain distinct.","No claim of exhaustive crop/rotation duplicate detection.","Synthetic set has four layout styles, one generator family; training supplement only."])
 (BASE/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
 esc=html.escape;cards=[]
 for r in final:
  img=(ROOT/r["image_path"]).relative_to(BASE).as_posix()
  badge=r["label"] or "unassigned"
  extra=""
  if r.get("ocr_screening_path"):
   txt=(ROOT/r["ocr_screening_path"]).read_text(encoding="utf-8",errors="replace")
   extra="<details><summary>Unreviewed OCR screening text</summary><pre>"+esc(txt)+"</pre></details>"
  elif r.get("pdf_path"):
   pdf=(ROOT/r["pdf_path"]).relative_to(BASE).as_posix()
   extra='<p><a href="'+esc(pdf,quote=True)+'">Original publisher PDF</a></p>'
  cards.append(f'<article data-status="{r["decision"]}" data-label="{badge}"><h2>{r["number"]}. {esc(r["sample_id"])} — {badge}</h2><p>{r["decision"]} · {esc(r["group_id"])}</p><p>{esc(r["review"]["evidence"])}</p><p>{esc(str(r["overlap_paths"])) if r["overlap_paths"] else ""}</p><img loading="lazy" src="{esc(img,quote=True)}" alt="Document {r["number"]}">{extra}</article>')
 page='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Reviewed dataset intake</title><style>body{font:16px system-ui;background:#f1f3f5;margin:24px;color:#16202b}header,article{background:white;padding:20px;margin:20px 0;border-radius:8px}article img{display:block;max-width:100%;max-height:1000px}pre{white-space:pre-wrap}select{font-size:16px}</style><header><h1>Reviewed dataset intake: 240 documents</h1><p>Assistant visual labels; independently human verified: 0. Staged separately; no training merge or new split assignment. OCR text is screening output, not ground truth.</p><label>Status <select id="status"><option value="">All</option><option>accepted_visual_review</option><option>hold_ambiguous</option><option>excluded_existing_duplicate</option><option>excluded_intake_duplicate</option></select></label> <label>Class <select id="label"><option value="">All</option><option>receipt</option><option>customer_copy</option><option>purchase_order</option><option>delivery_note</option><option>unassigned</option></select></label></header>'''
 page+="".join(cards)
 page+='<script>function filter(){const s=document.getElementById("status").value,l=document.getElementById("label").value;document.querySelectorAll("article").forEach(a=>a.hidden=(s&&a.dataset.status!==s)||(l&&a.dataset.label!==l))}document.querySelectorAll("select").forEach(e=>e.addEventListener("change",filter));</script></html>'
 (BASE/"review.html").write_text(page,encoding="utf-8")
 print(json.dumps(summary,indent=2));print("Non-exact similarity candidates:",[s for s in screen if s["status"]!="known_exact_excluded"])
if __name__=="__main__":main()
