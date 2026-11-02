"""Bounded public intake staging. Does not change training data or splits."""
import csv,hashlib,io,json,os,shutil,urllib.request,zipfile,time
from collections import Counter
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import pypdfium2 as pdfium
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"Dataset/intake/2026-10-19"
BASE.mkdir(parents=True,exist_ok=True)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected=[ROOT/"services/document_classifier"/p for p in ["labels.csv","data/manifest.csv","data/splits.csv","RESULTS.md"]]
protected+=sorted((ROOT/"Dataset/annotations/transcriptions").glob("*.json"))
before={str(p.relative_to(ROOT)):digest(p) for p in protected}
checkpoint=BASE/"protected_before.json"
if checkpoint.exists():assert json.loads(checkpoint.read_text())==before,"Protected files changed since intake began"
else:checkpoint.write_text(json.dumps(before,indent=2))
def write_once(p,data):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==data,f"Existing different file: {p}"
 else:p.write_bytes(data)
def get(url,limit=10000000):
 for attempt in range(3):
  try:
   with urllib.request.urlopen(url,timeout=40) as r:data=r.read(limit+1)
   if len(data)>limit:raise ValueError("Download exceeded bound")
   return data
  except Exception:
   if attempt==2:raise
   time.sleep(1)
records=[]
# SRD: use the independently checked publisher archive already cached.
archive=Path(os.environ["TEMP"])/"classifier-SRD.zip"
if not archive.exists():write_once(archive,get("https://expressexpense.com/large-receipt-image-dataset-SRD.zip",25000000))
assert hashlib.md5(archive.read_bytes()).hexdigest()=="c8eb0f2d286da5ab742e7a5b59f15147"
manifest=list(csv.DictReader((ROOT/"services/document_classifier/data/manifest.csv").open(encoding="utf-8")))
known={}
for r in manifest:known.setdefault(r["sha256"],[]).append(r["source_path"])
with zipfile.ZipFile(archive) as z:
 names=sorted(n for n in z.namelist() if Path(n).suffix.lower() in {".jpg",".jpeg",".png"})
 assert len(names)==200
 for n,name in enumerate(names,1):
  assert Path(name).name==name
  data=z.read(name);sha=hashlib.sha256(data).hexdigest()
  p=BASE/"expressexpense_srd/images"/name;write_once(p,data)
  with Image.open(p) as im:w,h=im.size
  records.append(dict(number=n,sample_id="srd_"+Path(name).stem,source="expressexpense_srd",source_url="https://expressexpense.com/large-receipt-image-dataset-SRD.zip",source_member=name,source_sha256=sha,image_path=str(p.relative_to(ROOT)),width=w,height=h,synthetic=False,overlap_paths=known.get(sha,[]),label="",decision="excluded_existing_duplicate" if sha in known else "pending_visual_review",group_id=""))
# Freeze and retain the publisher metadata used for selecting 20 per type.
repo="AyoubChLin/Company-document-dataset-v2"
meta=json.loads(get("https://huggingface.co/api/datasets/"+repo))
revision=meta["sha"]
(BASE/"company_documents_v2").mkdir(exist_ok=True)
(BASE/"company_documents_v2/revision.json").write_text(json.dumps(dict(repo=repo,revision=revision,date="2026-10-19",selection="20 English one-page documents per type; up to five per layout"),indent=2))
for kind in ["purchase_order","packing_slip"]:
 snap=BASE/"company_documents_v2"/("rows_"+kind+".json")
 if snap.exists():obj=json.loads(snap.read_text())
 else:
  url="https://datasets-server.huggingface.co/rows?dataset="+repo+"&config="+kind+"&split=train&offset=0&length=100"
  data=get(url,20000000);write_once(snap,data);obj=json.loads(data)
 selected=[];layouts=Counter()
 for x in obj["rows"]:
  row=x["row"]
  if row.get("locale")!="en" or row.get("pages")!=1:continue
  layout=row.get("layout","unknown")
  if layouts[layout]>=5:continue
  selected.append(row);layouts[layout]+=1
  if len(selected)==20:break
 if len(selected)!=20:raise ValueError(f"Need further bounded rows for {kind}: {dict(layouts)}")
 for row in selected:
  doc=row["doc_id"]
  path=BASE/"company_documents_v2/pdfs"/kind/(doc+".pdf")
  if not path.exists():write_once(path,get(row["pdf"]["src"],3000000))
  pdf=pdfium.PdfDocument(str(path));assert len(pdf)==1
  page=pdf[0]
  image=BASE/"company_documents_v2/images"/kind/(doc+".jpg");image.parent.mkdir(parents=True,exist_ok=True)
  if not image.exists():page.render(scale=2).to_pil().convert("RGB").save(image,quality=95)
  with Image.open(image) as im:w,h=im.size
  metadata=BASE/"company_documents_v2/metadata"/kind/(doc+".json")
  write_once(metadata,json.dumps(row,ensure_ascii=False,indent=2).encode("utf-8"))
  text=BASE/"company_documents_v2/text"/kind/(doc+".txt")
  write_once(text,page.get_textpage().get_text_range().encode("utf-8"))
  records.append(dict(number=len(records)+1,sample_id="company_"+doc,source="company_documents_v2",source_url="https://huggingface.co/datasets/"+repo,source_member=row["file_name"],source_sha256=digest(path),image_path=str(image.relative_to(ROOT)),width=w,height=h,synthetic=True,overlap_paths=known.get(digest(path),[]),label="purchase_order" if kind=="purchase_order" else "delivery_note",decision="pending_visual_review",group_id="company-v2:layout:"+row["layout"],doc_id=doc,source_document_type=kind,layout=row["layout"],theme=row.get("theme"),source_revision=revision,pdf_path=str(path.relative_to(ROOT)),text_path=str(text.relative_to(ROOT)),metadata_path=str(metadata.relative_to(ROOT))))
assert json.loads(get("https://huggingface.co/api/datasets/"+repo))["sha"]==revision,"Source revision changed during intake"
(BASE/"records.json").write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding="utf-8")
# License snapshots and links; originals are retained, not rewritten.
licenses=BASE/"licenses";licenses.mkdir(exist_ok=True)
for src in [ROOT/"Dataset/external_candidates/expressexpense_srd/publisher.html",ROOT/"Dataset/external_candidates/company_documents_v2/README.md"]:
 if src.exists():write_once(licenses/(src.parent.name+"_"+src.name),src.read_bytes())
for p in (ROOT/"Dataset/external_candidates/company_documents_v2/licenses").glob("*"):
 if p.is_file():write_once(licenses/p.name,p.read_bytes())
# 4 documents per inspectable page. Individual originals remain available for detail.
pages=BASE/"review_pages";pages.mkdir(exist_ok=True)
for start in range(0,len(records),4):
 sheet=Image.new("RGB",(2000,2200),"#dddddd");d=ImageDraw.Draw(sheet)
 for j,r in enumerate(records[start:start+4]):
  with Image.open(ROOT/r["image_path"]) as im:im=ImageOps.contain(im.convert("RGB"),(980,1030))
  x=(j%2)*1000;y=(j//2)*1100
  sheet.paste(im,(x+(1000-im.width)//2,y+42))
  d.text((x+8,y+5),str(r["number"])+" | "+r["sample_id"]+(" | EXISTING DUPLICATE" if r["overlap_paths"] else ""),fill="black")
 sheet.save(pages/f"{start+1:03d}.jpg",quality=95)
assert all(digest(ROOT/p)==h for p,h in before.items())
print(json.dumps(dict(staged=len(records),srd=200,synthetic=len(records)-200,known_duplicate_images=sum(bool(r["overlap_paths"]) for r in records),synthetic_layout_counts=dict(Counter(r.get("layout") for r in records if r["synthetic"])),revision=revision),indent=2))
