"""Shared, deterministic OCR/text handling for the preliminary experiment."""
import hashlib,os,re,subprocess,tempfile,unicodedata
from pathlib import Path
from PIL import Image,ImageOps
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CLASSES=["purchase_order","receipt","delivery_note","customer_copy"]
OCR_POLICY={"engine":"Tesseract","language":"eng","psm":3,"min_width":1400,"max_upscale":3,"normalization":"NFKC; collapse whitespace; casefold for CER/WER"}
def sha(path):
 path=Path(path)
 if not path.exists():
  try:path=HERE/path.relative_to(ROOT/'services/document_classifier')
  except ValueError:pass
 return hashlib.sha256(path.read_bytes()).hexdigest()
def clean_text(text):
 text=re.sub(r"\[[^\]\n]*\]"," ",text)
 return " ".join(unicodedata.normalize("NFKC",text).split())
def score_text(text):return " ".join(unicodedata.normalize("NFKC",text).casefold().split())
def edit_distance(a,b):
 if len(a)<len(b):a,b=b,a
 prev=list(range(len(b)+1))
 for i,x in enumerate(a,1):
  row=[i]
  for j,y in enumerate(b,1):row.append(min(row[-1]+1,prev[j]+1,prev[j-1]+(x!=y)))
  prev=row
 return prev[-1]
def group_guard(originals, additions, reference_texts):
 norm=lambda s:re.sub("[^a-z0-9]","",s.lower())
 normalized={r["sample_id"]:norm(reference_texts[r["sample_id"]]) for r in originals}
 train_hashes={r["sha256"]:r for r in originals}
 guarded=[]
 for r in additions:
  row=dict(r);row["experiment_split"]="train";row["experiment_include"]=True;row["guard_reason"]="new staged addition; train only"
  row["related_existing_groups"]=[]
  if row["source_sha256"] in train_hashes:
   row["experiment_include"]=False;row["guard_reason"]="exact existing source; excluded"
  key=norm(row.get("merchant_review_key",""))
  if row["source"]=="expressexpense_srd" and len(key)>=4 and not key.startswith("unknown"):
   matches=[old for old in originals if key in normalized[old["sample_id"]]]
   row["related_existing_groups"]=sorted({old["group_id"] for old in matches})
   if any(old["split"]!="train" for old in matches):
    row["experiment_include"]=False;row["guard_reason"]="merchant family touches frozen validation/test; excluded"
   elif matches:row["guard_reason"]="merchant family matches existing training only"
  if not row["experiment_include"]:row["experiment_split"]="excluded_guard"
  guarded.append(row)
 return guarded
def ocr_image(path):
 path=Path(path)
 with tempfile.TemporaryDirectory(prefix="document-text-") as tmp:
  with Image.open(path) as raw:
   image=ImageOps.exif_transpose(raw).convert("RGB")
   if image.width<1400:
    scale=min(3,1400/image.width);image=image.resize((int(image.width*scale),int(image.height*scale)),Image.Resampling.LANCZOS)
   png=Path(tmp)/"page.png";image.save(png)
  env=os.environ.copy();env["OMP_THREAD_LIMIT"]="1"
  cmd=["tesseract",str(png),"stdout","--tessdata-dir",str(HERE/".cache/tessdata"),"-l","eng","--psm","3"]
  result=subprocess.run(cmd,capture_output=True,timeout=120,env=env)
  if result.returncode:raise RuntimeError(result.stderr.decode("utf-8",errors="replace"))
  return result.stdout.decode("utf-8")
