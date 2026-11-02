import pathlib,json,urllib.request,hashlib,csv
from PIL import Image,ImageDraw
B=pathlib.Path(r'E:\.shortcut-targets-by-id\1yOBXNuSORBcOSWDhEg-YF1MEWIDvc8J2\Capstone- Inventory Management System'); D=B/'Dataset/external_candidates'
r=json.loads((D/'cord/first_rows_v2.json').read_text(encoding='utf8'))
print('CORD rows',len(r['rows']))
for idx in [0,8]:
 x=next((x for x in r['rows'] if x['row_idx']==idx),None)
 if x:
  row=x['row']; p=D/'cord/viewer/train'/str(idx)/'image.jpg';p.parent.mkdir(parents=True,exist_ok=True)
  try:
   with urllib.request.urlopen(row['image']['src'],timeout=30) as u:p.write_bytes(u.read(5000000))
   (D/'cord'/f'ground_truth_{idx:05d}.json').write_text(row['ground_truth'],encoding='utf8')
   print('cord saved',idx)
  except Exception as e:print(e)
# Verify CORD pixel equivalence despite JPEG conversion: only report metric, never call approximate match exact.
p=D/'cord/viewer/train/8/image.jpg';q=B/'Dataset/Receipt/cord-train-0008.jpg'
if p.exists():
 a=Image.open(p).convert('RGB');b=Image.open(q).convert('RGB');print('CORD sizes',a.size,b.size)
 if a.size==b.size:
  import numpy as np
  aa=np.asarray(a).astype(float);bb=np.asarray(b).astype(float);print('CORD MAE',abs(aa-bb).mean())
# WildReceipt actual annotation summary.
lines=[json.loads(s) for s in (D/'wildreceipt/wildreceipt/train.txt').read_text(encoding='utf8').splitlines() if s.strip()]
print('wild train rows',len(lines),'keys',list(lines[0]),'annotation',lines[0]['annotations'][0])
hits=[]
for x in lines:
 text=' '.join(a['text'] for a in x['annotations'])
 if any(k in text.upper() for k in ['CUSTOMER COPY','GUEST COPY','OFFICE COPY','DUPLICATE']):hits.append({'file_name':x['file_name'],'text':text})
(D/'wildreceipt/copy_cue_candidates.json').write_text(json.dumps(hits,indent=2))
print('wild copy phrase candidates',len(hits))
paths=list((D/'wildreceipt').rglob('*.jpeg'))[:8]+[D/'docile/pdfs/516f2d61ea404b30a9192a72.preview.png']+list((D/'cord/viewer/train').rglob('image.jpg'))
paths.append(q)
sheet=Image.new('RGB',(1600,580*((len(paths)+3)//4)),'#ddd');dr=ImageDraw.Draw(sheet)
for i,p in enumerate(paths):
 im=Image.open(p).convert('RGB');im.thumbnail((390,530));x=i%4*400;y=i//4*580;sheet.paste(im,(x+(400-im.width)//2,y+35));dr.text((x+4,y+3),p.name[:42],fill='black')
out=pathlib.Path(r'C:\Users\Windows 11\.codex\visualizations\2026\10\19\01a153db-0be9-7973-965e-e192b1a1c981')/'candidate-contact-2.jpg';sheet.save(out)
print(out)
