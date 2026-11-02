"""Build derived JPEGs, provenance manifest, and review sheets; never edits originals."""
import argparse, csv, hashlib, json
from pathlib import Path
from collections import Counter
from PIL import Image, ImageOps, ImageDraw
from pillow_heif import register_heif_opener
register_heif_opener()
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CLASSES = ["purchase_order", "receipt", "delivery_note", "customer_copy"]
FOLDERS = {
 "Dataset/Purchase_Order": ("purchase_order", "curated"),
 "Dataset/Receipt": ("receipt", "curated"),
 "Dataset/Delivery_Note": ("delivery_note", "curated"),
 "Dataset/Customer_Copy": ("customer_copy", "curated"),
 "Dataset/Dataset-2/Purchase order": ("purchase_order", "printed_synthetic_photo"),
 "Dataset/Dataset-2/Delivery note challan": ("delivery_note", "printed_synthetic_photo"),
 "Dataset/Dataset-2/Customer copy": ("customer_copy", "printed_synthetic_photo"),
}
EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif"}
def write_csv(path, rows, fields=None):
 path.parent.mkdir(parents=True, exist_ok=True)
 with path.open("w", newline="", encoding="utf-8") as f:
  w=csv.DictWriter(f, fieldnames=fields or list(rows[0])); w.writeheader(); w.writerows(rows)
def read_csv(path):
 with path.open(newline="", encoding="utf-8") as f: return list(csv.DictReader(f))
def main():
 parser=argparse.ArgumentParser(); parser.add_argument("--rebuild-images", action="store_true"); parser.add_argument("--labels-only",action="store_true"); args=parser.parse_args()
 out=HERE/"data"; (out/"images").mkdir(parents=True, exist_ok=True)
 overrides={r["source_path"]:r for r in read_csv(HERE/"labels.csv")} if (HERE/"labels.csv").exists() else {}
 if args.labels_only:
  rows=read_csv(out/"manifest.csv")
  for row in rows:
   override=overrides.get(row["source_path"],{})
   for field in ["label","group_id","label_status","include","notes"]:
    if override.get(field):row[field]=override[field]
  write_csv(out/"manifest.csv",rows)
  print(json.dumps(dict(included=dict(Counter(r["label"] for r in rows if r["include"]=="yes")),excluded=[r["source_path"] for r in rows if r["include"]!="yes"]),indent=2))
  return
 rows=[]; errors=[]; hashes={}
 for folder,(label,source) in FOLDERS.items():
  for path in sorted((ROOT/folder).glob("*")):
   if path.suffix.lower() not in EXTENSIONS: continue
   rel=path.relative_to(ROOT).as_posix()
   identity=hashlib.sha256(rel.encode()).hexdigest()[:12]
   dest=out/"images"/(identity+".jpg")
   try:
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    with Image.open(path) as raw:
     im=ImageOps.exif_transpose(raw).convert("RGB"); width,height=im.size
     im.thumbnail((1800,1800), Image.Resampling.LANCZOS)
     if not dest.exists() or args.rebuild_images: im.save(dest, quality=94)
    override=overrides.get(rel,{})
    # Until a template/document is mapped, group conservatively by class and source.
    group=override.get("group_id") or source+":"+label
    row=dict(sample_id=identity,source_path=rel,image_path=dest.relative_to(HERE).as_posix(),
     label=override.get("label") or label,source=source,sha256=sha,width=width,height=height,
     group_id=group,label_status=override.get("label_status") or "folder_label_unverified",
     include=override.get("include") or "yes",notes=override.get("notes",""))
    rows.append(row); hashes.setdefault(sha,[]).append(rel)
   except Exception as e: errors.append(dict(source_path=rel,error=str(e)))
 write_csv(out/"manifest.csv",rows)
 for label in CLASSES:
  selected=[r for r in rows if r["label"]==label]
  for page,start in enumerate(range(0,len(selected),20),1):
   batch=selected[start:start+20]; sheet=Image.new("RGB",(1200,340*((len(batch)+3)//4)),"#dedede"); draw=ImageDraw.Draw(sheet)
   for i,row in enumerate(batch):
    with Image.open(HERE/row["image_path"]) as im: thumb=ImageOps.contain(im,(288,295))
    x=(i%4)*300; y=(i//4)*340
    sheet.paste(thumb,(x+(300-thumb.width)//2,y))
    draw.text((x+4,y+298),Path(row["source_path"]).name[:38],fill="black")
    draw.text((x+4,y+314),row["sample_id"]+" "+row["source"][:15],fill="black")
   sheet.save(out/f"review_{label}_{page}.jpg",quality=90)
 report=dict(counts=dict(Counter(r["label"] for r in rows)),sources=dict(Counter(r["source"] for r in rows)),
  errors=errors,exact_duplicates=[v for v in hashes.values() if len(v)>1],
  excluded_sources=["synthetic_dataset/images","ChatGPT_Bridge/4_approved","Dataset/_excluded"],
  note="Generated originals excluded; Dataset-2 is printed-synthetic phone photography per user. Curated provenance is not assumed real.")
 (out/"audit.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print(json.dumps(report,indent=2),flush=True)
 if errors: raise SystemExit("Some inputs failed; see data/audit.json.")
if __name__=="__main__": main()
