"""Uniform printed OCR recovery; no label/sample-specific preprocessing."""
import os,subprocess,tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps,ImageFilter
from text_common import HERE
POLICY=dict(version='illumination-v1',min_width=1600,max_upscale=3,background_blur=24,foreground_threshold=190,full_psm=6,top_fraction=.4,top_rotations=[-12,0,12],top_psm=11,language='eng')

def illumination_ocr(path):
 if Path(path).suffix.lower() in ['.heic','.heif']:
  from pillow_heif import register_heif_opener
  register_heif_opener()
 with Image.open(path) as raw:
  im=ImageOps.exif_transpose(raw).convert('RGB')
  if im.width<POLICY['min_width']:
   scale=min(3,POLICY['min_width']/im.width);im=im.resize((int(im.width*scale),int(im.height*scale)),Image.Resampling.LANCZOS)
 gray=ImageOps.grayscale(im);background=gray.filter(ImageFilter.GaussianBlur(POLICY['background_blur']))
 ratio=np.asarray(gray,dtype=np.float32)/np.maximum(np.asarray(background,dtype=np.float32),1)
 normalized=Image.fromarray(np.clip(ratio*235,0,255).astype('uint8'))
 binary=normalized.point(lambda v:0 if v<POLICY['foreground_threshold'] else 255)
 top=binary.crop((0,0,binary.width,int(binary.height*POLICY['top_fraction'])))
 views=[('full',normalized,6)]+[('top_'+str(angle),top.rotate(angle,expand=True,fillcolor=255),11) for angle in POLICY['top_rotations']]
 result={}
 with tempfile.TemporaryDirectory(prefix='printed-illumination-') as tmp:
  for name,view,psm in views:
   png=Path(tmp)/(name+'.png');ImageOps.expand(view,border=20,fill=255).save(png)
   env=os.environ.copy();env['OMP_THREAD_LIMIT']='1'
   proc=subprocess.run(['tesseract',str(png),'stdout','--tessdata-dir',str(HERE/'.cache/tessdata'),'-l','eng','--psm',str(psm)],capture_output=True,env=env,timeout=120)
   if proc.returncode:raise RuntimeError(proc.stderr.decode('utf8',errors='replace'))
   result[name]=proc.stdout.decode('utf8')
 return result

