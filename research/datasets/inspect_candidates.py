import pathlib, urllib.request, json, zipfile, os, hashlib, csv
from PIL import Image, ImageOps, ImageDraw
import pypdfium2 as pdfium
B=pathlib.Path(r'E:\.shortcut-targets-by-id\1yOBXNuSORBcOSWDhEg-YF1MEWIDvc8J2\Capstone- Inventory Management System')
D=B/'Dataset/external_candidates'
def get(url,p):
    p.parent.mkdir(parents=True,exist_ok=True)
    with urllib.request.urlopen(url,timeout=45) as r: data=r.read(8_000_001)
    if len(data)>8_000_000: raise ValueError('bounded download exceeded')
    p.write_bytes(data)
    return data
# Preserve publisher metadata/terms alongside examples.
meta={
'cord':[('README.md','https://raw.githubusercontent.com/clovaai/cord/master/README.md'),('LICENSE-CC-BY','https://raw.githubusercontent.com/clovaai/cord/master/LICENSE-CC-BY'),('sample.png','https://raw.githubusercontent.com/clovaai/cord/master/figure/sample.png')],
'company_documents_v2':[('README.md','https://huggingface.co/datasets/AyoubChLin/Company-document-dataset-v2/raw/main/README.md')],
'sroie':[('README.md','https://raw.githubusercontent.com/zzzDavid/ICDAR-2019-SROIE/master/README.md'),('LICENSE','https://raw.githubusercontent.com/zzzDavid/ICDAR-2019-SROIE/master/LICENSE')],
'expressexpense_srd':[('publisher.html','https://expressexpense.com/blog/free-receipt-images-ocr-machine-learning-dataset/')],
'wildreceipt':[('metafile.yml','https://raw.githubusercontent.com/open-mmlab/mmocr/main/dataset_zoo/wildreceipt/metafile.yml')]
}
for ds,files in meta.items():
 for name,url in files:
  try: get(url,D/ds/name)
  except Exception as e: print('metadata failed',ds,name,str(e))
# Small publisher archive; retain only four samples matching existing filenames and two unrelated samples.
z=zipfile.ZipFile(pathlib.Path(os.environ['TEMP'])/'classifier-SRD.zip')
(D/'expressexpense_srd/archive_members.json').write_text(json.dumps(z.namelist(),indent=2))
print('SRD archive',len(z.namelist()),'members',hashlib.md5((pathlib.Path(os.environ['TEMP'])/'classifier-SRD.zip').read_bytes()).hexdigest())
for name in ['1085-receipt.jpg','1057-receipt.jpg','1073-receipt.jpg','1164-receipt.jpg','1176-receipt.jpg','1078-receipt.jpg']:
 if name in z.namelist(): (D/'expressexpense_srd'/name).write_bytes(z.read(name))
# Retry bounded CORD and synthetic receipt rows.
for ds,cfg,off,n in [('naver-clova-ix/cord-v2','default',8,1),('AyoubChLin/Company-document-dataset-v2','receipt',0,3)]:
 url=f'https://datasets-server.huggingface.co/rows?dataset={ds}&config={cfg}&split=train&offset={off}&length={n}'
 folder='cord' if 'cord' in ds else 'company_documents_v2'
 try:
  data=get(url,D/folder/f'rows_{cfg}_{off}.json'); obj=json.loads(data)
  for x in obj['rows']:
   r=x['row']
   if folder=='cord':get(r['image']['src'],D/folder/'viewer/train/8/image.jpg')
   elif r['locale']=='en':
    get(r['pdf']['src'],D/folder/r['file_name'])
    get(r['pdf']['thumbnail']['src'],D/folder/(r['file_name']+'.png'))
  print('rows retrieved',folder,cfg)
 except Exception as e:print('rows failed',folder,cfg,str(e))
# PDF render previews and inspectable text, derived only.
for p in D.rglob('*.pdf'):
 try:
  pdf=pdfium.PdfDocument(str(p));page=pdf[0]
  page.render(scale=1.3).to_pil().save(p.with_suffix('.preview.png'))
  (p.with_suffix('.text.txt')).write_text(page.get_textpage().get_text_range(),encoding='utf8')
 except Exception as e:print('render failed',str(p),str(e))
# Exact byte matches and decoded pixel matches (compression/format changes are not exact pixel matches).
existing=[p for p in (B/'Dataset').rglob('*') if p.is_file() and 'external_candidates' not in p.parts and p.suffix.lower() in ['.jpg','.png','.jpeg']]
for p in (D/'expressexpense_srd').glob('*.jpg'):
 matches=[str(q.relative_to(B)) for q in existing if hashlib.sha256(q.read_bytes()).digest()==hashlib.sha256(p.read_bytes()).digest()]
 print('EXACT',p.name,matches)
# Contact sheet showing external samples plus selected existing source clues.
paths=list((D/'company_documents_v2').rglob('*.preview.png'))+list((D/'sroie/img').glob('*.jpg'))+list((D/'expressexpense_srd').glob('*.jpg'))+list((D/'cord').glob('sample.png'))+list((D/'cord/viewer/train').rglob('image.jpg'))
paths += [B/'Dataset/Customer_Copy/image_1850.jpg', B/'Dataset/Receipt/cord-train-0008.jpg']
w,h=400,570
sheet=Image.new('RGB',(w*4,h*((len(paths)+3)//4)),'#ddd');draw=ImageDraw.Draw(sheet)
for i,p in enumerate(paths):
 im=Image.open(p).convert('RGB');im.thumbnail((390,525)); x=(i%4)*w;y=(i//4)*h
 sheet.paste(im,(x+(w-im.width)//2,y+30));draw.text((x+4,y+4),p.parent.name+'/'+p.name,fill='black')
out=pathlib.Path(r'C:\Users\Windows 11\.codex\visualizations\2026\10\19\01a153db-0be9-7973-965e-e192b1a1c981')/'candidate-contact.jpg';sheet.save(out)
print('CONTACT',out, 'images',len(paths))
