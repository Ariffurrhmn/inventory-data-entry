"""OCR for intake screening only. Output is unreviewed, not reference truth."""
import csv,json,re,subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"Dataset/intake/2026-10-19"
out=BASE/"ocr_screening";out.mkdir(exist_ok=True)
paths=sorted((BASE/"expressexpense_srd/images").glob("*.jpg"))
assert len(paths)==200
def run(p):
 dest=out/(p.stem+".txt")
 if not dest.exists():
  r=subprocess.run([r"C:\Users\Windows 11\scoop\shims\tesseract.exe",str(p),"stdout","--tessdata-dir",str(ROOT/"services/document_classifier/.cache/tessdata"),"-l","eng","--psm","3"],capture_output=True,timeout=90)
  if r.returncode:raise RuntimeError(p.name+": "+r.stderr.decode("utf-8",errors="replace")[:200])
  dest.write_bytes(r.stdout)
 text=dest.read_text(encoding="utf-8",errors="replace")
 cues=[line.strip() for line in text.splitlines() if re.search(r"copy|duplicate|paid|cash|change|balance|due|credit|visa|master|approved|sale|bill|total|tip",line,re.I)]
 return dict(filename=p.name,ocr_characters=len(text),screening_cues=" | ".join(cues),status="unreviewed_OCR_screening_only")
rows=[]
with ThreadPoolExecutor(max_workers=4) as pool:
 futures={pool.submit(run,p):p for p in paths}
 for f in as_completed(futures):
  rows.append(f.result())
  if len(rows)%25==0:print(f"OCR screening {len(rows)}/200",flush=True)
rows.sort(key=lambda r:r["filename"])
with (out/"cues.csv").open("w",encoding="utf-8",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print("Completed 200 screening drafts; no model training or reference transcription changes.")
