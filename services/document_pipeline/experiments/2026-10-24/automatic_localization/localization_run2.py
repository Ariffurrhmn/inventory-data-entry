"""Image-independent ruled-table localization and local OCR (development).

Coordinates refer to EXIF-oriented source pixels. No source pixels or OCR are
rewritten. A missing grid is explicit and OCR word boxes remain fallback evidence.
"""
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageDraw
from scipy import ndimage as ndi

VERSION = 'ruled-layout-v1'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def normalized_image(image):
    gray = ImageOps.grayscale(image)
    bg = gray.filter(ImageFilter.GaussianBlur(24))
    return Image.fromarray(np.clip(np.asarray(gray, dtype=float) / np.maximum(np.asarray(bg, dtype=float), 1) * 235, 0, 255).astype('uint8'))

def _bands(mask, threshold):
    indices = np.flatnonzero(mask >= threshold)
    if not len(indices): return []
    return [int(round(g.mean())) for g in np.split(indices, np.flatnonzero(np.diff(indices)>3)+1)]

def locate(image, deskew=False):
    """Return transformed image and detected grids; no document-specific constants."""
    source = ImageOps.exif_transpose(image).convert('RGB')
    scale = min(1.0, 1400 / max(source.size))
    small = source.resize((round(source.width*scale),round(source.height*scale)))
    norm = normalized_image(small)
    binary = np.asarray(norm)<215
    angle = 0
    scores = []
    if deskew:
        for a in np.arange(-4,4.01,.5):
            rotated = ndi.rotate(binary, float(a), reshape=False, order=0, cval=0)
            lines = ndi.binary_opening(rotated, structure=np.ones((1,max(15,round(small.width*.07)))))
            score = int(lines.sum()); scores.append([float(a),score])
        angle = max(scores,key=lambda x:x[1])[0]
        norm = norm.rotate(angle, resample=Image.Resampling.BICUBIC, fillcolor=255)
        binary = np.asarray(norm)<215
    h,w=binary.shape
    horizontal = ndi.binary_opening(ndi.maximum_filter(binary,size=(3,1)),structure=np.ones((1,max(15,round(w*.04)))))
    vertical = ndi.binary_opening(ndi.maximum_filter(binary,size=(1,3)),structure=np.ones((max(15,round(h*.025)),1)))
    # Bridge small breaks due to camera perspective and curved rules.
    grid = ndi.binary_dilation(horizontal|vertical, iterations=2)
    labels,count=ndi.label(grid)
    tables=[]
    for sl in ndi.find_objects(labels):
        if sl is None: continue
        ys,xs=sl; bw=xs.stop-xs.start; bh=ys.stop-ys.start
        if bw<w*.25 or bh<h*.045: continue
        hm=horizontal[ys,xs]; vm=vertical[ys,xs]
        ylines=_bands(ndi.maximum_filter(hm,size=(7,1)).sum(axis=1),bw*.40)
        xlines=_bands(ndi.maximum_filter(vm,size=(1,9)).sum(axis=0),bh*.40)
        if len(ylines)<3 or len(xlines)<2: continue
        rows=[]
        for y0,y1 in zip(ylines,ylines[1:]):
            if y1-y0<8: continue
            cells=[]
            for x0,x1 in zip(xlines,xlines[1:]):
                # Inset scales with cell size, capped to avoid clipping content.
                ix=min(8,max(3,round((x1-x0)*.025))); iy=min(7,max(3,round((y1-y0)*.12)))
                box=[xs.start+x0+ix,ys.start+y0+iy,xs.start+x1-ix,ys.start+y1-iy]
                if box[2]>box[0] and box[3]>box[1]: cells.append(box)
            if cells: rows.append(cells)
        if rows: tables.append({'box':[xs.start,ys.start,xs.stop,ys.stop],'horizontal_rules':[ys.start+y for y in ylines], 'vertical_rules':[xs.start+x for x in xlines], 'rows':rows})
    return norm, {'version':VERSION,'source_size':list(source.size),'working_size':list(norm.size),'scale':scale,'rotation_degrees':angle,'rotation_scores':scores,'coordinate_system':'EXIF-oriented source scaled by scale, then rotated about image center; inverse affine provided','inverse_affine':inverse_affine(source.size,scale,angle),'tables':tables}, grid

def inverse_affine(size,scale,angle):
    # PIL positive rotation: x'=cos*x+sin*y; y'=-sin*x+cos*y about center.
    a=np.deg2rad(angle); c=float(np.cos(a)); s=float(np.sin(a)); cx=round(size[0]*scale)/2; cy=round(size[1]*scale)/2
    return [[c/scale,-s/scale,(cx-c*cx+s*cy)/scale],[s/scale,c/scale,(cy-s*cx-c*cy)/scale]]

def montage(image,tables):
    strips=[]; mapping=[]; y=20
    for ti,table in enumerate(tables):
        for ri,row in enumerate(table['rows']):
            tiles=[image.crop(tuple(box)) for box in row]
            height=max(t.height for t in tiles)+30
            strip=Image.new('L',(sum(t.width for t in tiles)+35*(len(tiles)+1),height),255)
            x=35
            for ci,(tile,box) in enumerate(zip(tiles,row)):
                strip.paste(tile,(x,15)); mapping.append({'table':ti,'row':ri,'column':ci,'working_box':box,'montage_box':[x,y+15,x+tile.width,y+15+tile.height]}); x+=tile.width+35
            strips.append(strip); y+=height+25
    if not strips: return None,[]
    canvas=Image.new('L',(max(s.width for s in strips),y),255); y=20
    for strip in strips: canvas.paste(strip,(0,y)); y+=strip.height+25
    return canvas,mapping

def ocr(view,base,tessdata,psm=6):
    png=Path(str(base)+'.png'); view.save(png)
    command=[shutil.which('tesseract'),str(png),str(base),'--tessdata-dir',str(tessdata),'-l','eng','--psm',str(psm),'-c','tessedit_create_txt=1','-c','tessedit_create_tsv=1']
    env=os.environ.copy();env['OMP_THREAD_LIMIT']='1'; start=time.perf_counter()
    proc=subprocess.run(command,capture_output=True,env=env,timeout=120)
    textpath=Path(str(base)+'.txt'); tsvpath=Path(str(base)+'.tsv')
    text=textpath.read_text(encoding='utf-8') if textpath.exists() else ''
    words=[]
    if tsvpath.exists():
        for word in csv.DictReader(io.StringIO(tsvpath.read_text(encoding='utf-8')),delimiter='\t'):
            if word.get('text','').strip(): words.append(word)
    return {'command':command,'returncode':proc.returncode,'seconds':round(time.perf_counter()-start,4),'stderr':proc.stderr.decode('utf-8',errors='replace'),'ocr_text':text,'words':words,'image_sha256':sha(png),'text_sha256':sha(textpath) if textpath.exists() else None}

def analyze(image_path,output,tessdata):
    """Write all candidates, including failures, to a NEW output directory."""
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    with Image.open(image_path) as im: source=ImageOps.exif_transpose(im).convert('RGB')
    result={'source':str(image_path),'source_sha256':sha(image_path),'human_verified':False,'module_sha256':sha(__file__),'candidates':[]}
    for method in ['axis_grid','deskew_grid']:
        norm,layout,grid=locate(source,deskew=method=='deskew_grid')
        Image.fromarray((grid*255).astype('uint8')).save(output/(method+'_mask.png'))
        overlay=norm.convert('RGB');draw=ImageDraw.Draw(overlay)
        for table in layout['tables']:
            for row in table['rows']:
                for box in row: draw.rectangle(box,outline='red',width=2)
        overlay.save(output/(method+'_overlay.png'))
        view,mapping=montage(norm,layout['tables'])
        candidate={'method':method,'layout':layout,'mapping':mapping}
        if view:
            view=view.resize((view.width*2,view.height*2),Image.Resampling.LANCZOS)
            candidate['ocr']=ocr(view,output/method,tessdata)
            candidate['mapping_scale_to_ocr']=2
        else: candidate['failure']='No eligible ruled grid detected; no invented cells.'
        result['candidates'].append(candidate)
    # OCR word boxes/layout grouping is a separate fallback, with no table claim.
    norm=normalized_image(source)
    fallback=ocr(norm,output/'word_boxes_psm11',tessdata,11)
    groups={}
    for word in fallback['words']:
        key=tuple(word[k] for k in ['block_num','par_num','line_num'])
        groups.setdefault(':'.join(key),[]).append(word)
    result['word_box_fallback']={**fallback,'line_groups':groups,'limitation':'Tesseract line grouping does not establish table cells or row roles.'}
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result

