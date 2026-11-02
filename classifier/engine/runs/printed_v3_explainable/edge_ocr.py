"""Additional OCR for printed page edges, where document/copy headings often appear."""
import os,subprocess,tempfile
from pathlib import Path
from PIL import Image,ImageOps
from text_common import HERE

def edge_ocr(path):
 path=Path(path)
 if path.suffix.lower() in ['.heic','.heif']:
  from pillow_heif import register_heif_opener
  register_heif_opener()
 with Image.open(path) as raw:
  image=ImageOps.exif_transpose(raw).convert('RGB')
  if image.width<1400:
   scale=min(3,1400/image.width);image=image.resize((int(image.width*scale),int(image.height*scale)),Image.Resampling.LANCZOS)
  crops=[image.crop((0,0,image.width,int(image.height*.35))),image.crop((0,int(image.height*.65),image.width,image.height))]
  outputs=[]
  with tempfile.TemporaryDirectory(prefix='printed-edges-') as tmp:
   for index,crop in enumerate(crops):
    gray=ImageOps.autocontrast(ImageOps.grayscale(crop));prepared=ImageOps.expand(gray,border=20,fill='white');png=Path(tmp)/(str(index)+'.png');prepared.save(png)
    env=os.environ.copy();env['OMP_THREAD_LIMIT']='1'
    result=subprocess.run(['tesseract',str(png),'stdout','--tessdata-dir',str(HERE/'.cache/tessdata'),'-l','eng','--psm','6'],capture_output=True,env=env,timeout=120)
    if result.returncode:raise RuntimeError(result.stderr.decode('utf-8',errors='replace'))
    outputs.append(result.stdout.decode('utf-8'))
 return '\n'.join(outputs)
