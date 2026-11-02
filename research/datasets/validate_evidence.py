import pathlib,json,csv,re,hashlib
from PIL import Image,ImageDraw
B=pathlib.Path(r'E:\.shortcut-targets-by-id\1yOBXNuSORBcOSWDhEg-YF1MEWIDvc8J2\Capstone- Inventory Management System');D=B/'Dataset/external_candidates';R=B/'research/datasets'
# Correct the inspection scripts to preserve viewer-served basename on any future authorized use.
p=R/'inspect_candidates.py';s=p.read_text(encoding='utf8');s=s.replace("D/folder/'train/image/00008.png'","D/folder/'viewer/train/8/image.jpg'");s=s.replace("list((D/'cord/train/image').glob('*.png'))","list((D/'cord/viewer/train').rglob('image.jpg'))");p.write_text(s,encoding='utf8')
p=R/'inspect_annotations.py';s=p.read_text(encoding='utf8');s=s.replace("D/'cord/train/image'/f'{idx:05d}.png'","D/'cord/viewer/train'/str(idx)/'image.jpg'");s=s.replace("D/'cord/train/image/00008.png'","D/'cord/viewer/train/8/image.jpg'");s=s.replace("list((D/'cord/train/image').glob('*.png'))","list((D/'cord/viewer/train').rglob('image.jpg'))");s=s.replace('.read_text()',".read_text(encoding='utf8')");p.write_text(s,encoding='utf8')
paths=list((D/'wildreceipt').rglob('*.jpeg'))[:8]+[D/'docile/pdfs/516f2d61ea404b30a9192a72.preview.png']+list((D/'cord/viewer/train').rglob('image.jpg'))+[B/'Dataset/Receipt/cord-train-0008.jpg']
im=Image.new('RGB',(1600,580*((len(paths)+3)//4)),'#ddd');dr=ImageDraw.Draw(im)
for i,p in enumerate(paths):
 a=Image.open(p).convert('RGB');a.thumbnail((390,530));x=i%4*400;y=i//4*580;im.paste(a,(x+(400-a.width)//2,y+35));label=('CORD train row '+p.parent.name+'/image.jpg') if p.name=='image.jpg' else p.name[:42];dr.text((x+4,y+3),label,fill='black')
im.save(R/'previews/candidate-contact-2.jpg')
# Validate every registered local file and every cited local artifact.
rows=list(csv.DictReader((R/'sample_provenance.csv').open(encoding='utf8')))
assert all(x['source_url'] for x in rows)
assert all((B/x['local_path']).exists() for x in rows)
assert all(hashlib.sha256((B/x['local_path']).read_bytes()).hexdigest()==x['sha256'] for x in rows)
source=list(csv.DictReader((R/'sources.csv').open(encoding='utf8')))
reviews=list(csv.DictReader((R/'sample_review.csv').open(encoding='utf8')))
for x in reviews:assert (D/x['dataset_id']/x['source_sample']).exists(),x
print('VALID',len(source),'sources;',len(rows),'non-system provenance records;',len(reviews),'reviewed samples; hashes and paths valid')
print('total retained evidence MB',round(sum(int(x['bytes']) for x in rows)/1e6,2))
print('protected classifier unchanged',all(x['unchanged'] for x in json.loads((R/'validation.json').read_text())['protected_files']))
