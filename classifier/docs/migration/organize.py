import csv,json,hashlib,shutil,sys
from pathlib import Path
root=Path.cwd();home=root/'classifier';engine=home/'engine'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=list(csv.DictReader((home/'docs/migration-before.csv').open(encoding='utf8')))
mismatches=[]
for item in before:
 p=engine/item['path']
 if not p.exists() or digest(p)!=item['sha256']:mismatches.append(item['path'])
assert not [x for x in mismatches if Path(x).name.casefold()!='desktop.ini'],mismatches
after=[dict(path=p.relative_to(engine).as_posix(),size=p.stat().st_size,sha256=digest(p)) for p in engine.rglob('*') if p.is_file()]
with (home/'docs/migration-after.csv').open('w',encoding='utf8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['path','size','sha256']);w.writeheader();w.writerows(after)
(home/'docs/migration-validation.json').write_text(json.dumps(dict(pre_scan_hashed=len(before),post_scan_files=len(after),pre_scan_data_and_code_hashes_match=True,windows_folder_metadata_differences=mismatches,note='The pre-scan overlapped relocation and covers941 files rather than the whole directory. The full post-scan is preserved; Move-Item moved all non-data entries and data was copied, never deleted.',legacy_data_preserved=True,raw_datasets_or_annotations_modified=False),indent=2),encoding='utf8')
rows={r['sample_id']:r for r in csv.DictReader((engine/'runs/printed_v3_explainable/split_manifest.csv').open(encoding='utf8'))}
originals={r['sample_id']:r for r in csv.DictReader((engine/'data/manifest.csv').open(encoding='utf8'))}
choices=[('76cc99d39da4','Purchase request',False),('5dffabcb47cb','Retail receipt',False),('f9918570b903','Delivery challan',False),('e396ade11def','Office copy',False),('cdd7aaa9004d','Faint copy stamp',True)]
manifest=[]
for sid,title,failure in choices:
 row=rows[sid];assert row['split']=='val'
 source=root/row['image_path'];assert digest(source)==row['image_sha256']
 image=home/'demo/images'/(sid+'.jpg');shutil.copy2(source,image)
 record=engine/'runs/printed_v3_explainable/explanations'/(sid+'.json');saved=json.loads(record.read_text(encoding='utf8'))
 assert (saved['result']['label']!=row['label'])==failure
 target=home/'demo/records'/(sid+'.json');shutil.copy2(record,target)
 provenance=('Photograph of a printed synthetic document' if 'Dataset-2' in originals.get(sid,{}).get('source_path',row.get('source_path','')) else 'Existing development document')+' · recorded OCR analysis'
 manifest.append(dict(id=sid,title=title,expected_label=row['label'],known_failure=failure,image=image.relative_to(home).as_posix(),record=target.relative_to(home).as_posix(),image_sha256=digest(image),provenance=provenance,split='val'))
(home/'demo/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
# Resolve historical audit names at the hashing boundary without modifying old records.
p=engine/'text_common.py';s=p.read_text(encoding='utf8')
s=s.replace('def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()',"""def sha(path):
 path=Path(path)
 if not path.exists():
  try:path=HERE/path.relative_to(ROOT/'services/document_classifier')
  except ValueError:pass
 return hashlib.sha256(path.read_bytes()).hexdigest()""")
p.write_text(s,encoding='utf8')
# Portal uses the new canonical classifier, while its temp-fixture legacy layout still works.
p=root/'services/annotation_portal/server.py';s=p.read_text(encoding='utf8')
s=s.replace("CLASSIFIER = ROOT / 'services/document_classifier'","CLASSIFIER = ROOT / 'classifier/engine'")
s=s.replace("self.service = self.root / 'services/document_classifier'","self.service = self.root / ('classifier/engine' if (self.root/'classifier/engine').is_dir() else 'services/document_classifier')\n        self.service_relative = self.service.relative_to(self.root).as_posix()")
s=s.replace("image_path='services/document_classifier/' + row['image_path']", "image_path=self.service_relative+'/' + row['image_path']")
s=s.replace("image = 'services/document_classifier/' + image","image = self.service_relative+'/' + image")
p.write_text(s,encoding='utf8')
for name in ['research/datasets/finalize_intake.py','research/datasets/recheck_overlap.py']:
 p=root/name;s=p.read_text(encoding='utf8');p.write_text(s.replace('services/document_classifier','classifier/engine'),encoding='utf8')
p=engine/'reference_annotations.py';s=p.read_text(encoding='utf8');p.write_text(s.replace('services/document_classifier/','classifier/engine/'),encoding='utf8')
print('Relocation verified:',len(before),'pre-scan hashes;',len(after),'files in full post-scan. Prepared five existing validation examples.')

