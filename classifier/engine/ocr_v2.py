"""Versioned OCR alternatives; does not alter the preliminary OCR policy."""
import os,re,subprocess,tempfile
from pathlib import Path
from PIL import Image,ImageOps
from text_common import HERE
SPARSE_POLICY={"engine":"Tesseract","language":"eng","psm":11,"min_width":1400,"max_upscale":3}
def sparse_ocr(path):
 with tempfile.TemporaryDirectory(prefix="document-sparse-") as tmp:
  with Image.open(path) as raw:
   im=ImageOps.exif_transpose(raw).convert("RGB")
   if im.width<1400:
    scale=min(3,1400/im.width);im=im.resize((int(im.width*scale),int(im.height*scale)),Image.Resampling.LANCZOS)
   png=Path(tmp)/"page.png";im.save(png)
  env=os.environ.copy();env["OMP_THREAD_LIMIT"]="1"
  cmd=["tesseract",str(png),"stdout","--tessdata-dir",str(HERE/".cache/tessdata"),"-l","eng","--psm","11"]
  result=subprocess.run(cmd,capture_output=True,env=env,timeout=120)
  if result.returncode:raise RuntimeError(result.stderr.decode("utf-8",errors="replace"))
  return result.stdout.decode("utf-8")
def combine_outputs(baseline,sparse):
 seen=set();lines=[]
 for raw in (baseline,sparse):
  for line in raw.splitlines():
   line=" ".join(line.split());key=line.casefold()
   if key and key not in seen:seen.add(key);lines.append(line)
 return "\n".join(lines)
