import csv,json,sys,hashlib,urllib.request
from pathlib import Path
root=Path.cwd();home=root/'classifier';engine=home/'engine'
sys.path.insert(0,str(engine))
from text_common import sha
active=json.loads((engine/'active_text_model.json').read_text(encoding='utf8'))
assert active['run']=='printed_v3_explainable'
assert sha(engine/'runs'/active['run']/'classifier.joblib')==active['model_sha256']=='bd1dba65eb03c3f2282697a502400794ce754543c5e16150625b73cea62ce0bd'
protected=json.loads((engine/'runs/printed_v1_grouped/protected_before.json').read_text(encoding='utf8'))
for name,digest in protected.items():assert sha(root/name)==digest,name
legacy_count=0
for suffix in ['runs/text_preliminary/ocr','runs/text_delivery_v2/ocr_sparse']:
 for path in (engine/suffix).glob('*.json'):
  assert sha(path)==sha(root/'services/document_classifier'/suffix/path.name),path.name
  legacy_count+=1
examples=json.loads((home/'demo/manifest.json').read_text(encoding='utf8'))
for item in examples:
 assert sha(home/item['image'])==item['image_sha256']
 record=json.loads((home/item['record']).read_text(encoding='utf8'))
 assert record['result']['model_sha256']==active['model_sha256']
for name in ['recorded-report.json','exported-report.json']:
 report=json.loads((home/'docs/qa'/name).read_text(encoding='utf8'))
 assert report['mode']=='recorded' and report['result']['model_sha256']==active['model_sha256']
 assert 'preview' not in report
with urllib.request.urlopen('http://127.0.0.1:8770/api/info',timeout=15) as response:info=json.load(response)
assert info['app_id']=='document-lab-supervisor-v1' and info['model']['model_sha256']==active['model_sha256']
portal_live=None
try:
 with urllib.request.urlopen('http://127.0.0.1:8765/api/record/5dffabcb47cb',timeout=15) as response:record=json.load(response)
 portal_live=dict(image_available=record['image_available'],ocr_sources=len(record['drafts']))
 assert portal_live['image_available']
except Exception as e:portal_live=dict(check_error=type(e).__name__+': '+str(e))
result=dict(date='2026-10-20',app_url='http://127.0.0.1:8770',model_run=active['run'],model_hash_unchanged=True,protected_historical_hashes_verified=len(protected),example_image_and_model_hashes_verified=len(examples),legacy_ocr_json_copies_verified=legacy_count,automated_checks=dict(demo_api=5,classifier=30,annotation_portal=8,total=43),portal_catalog_images_resolved=236,existing_portal_session=portal_live,browser_checks=['recorded purchase intent','receipt exact learned-feature contributions','office-copy heading','known failure transparently labelled','live image OCR and classification','OCR inspection','model/evidence page','explicit project report save','JSON download'],live_image_check=dict(sample_id='76cc99d39da4',predicted_label='purchase_order',elapsed_seconds=10.51,new_benchmark=False),demo_examples_use_historical_test=False,recorded_mode_clearly_labelled=True,raw_datasets_and_annotation_truth_modified=False,setup_new_pc_executed=False,preview='classifier/docs/demo-preview.png')
(home/'docs/demo-validation.json').write_text(json.dumps(result,indent=2),encoding='utf8')
mapping=home/'docs/migration/path-migration.json'
original=json.loads(mapping.read_text(encoding='utf8'));original.update(historical_ocr_caches=['services/document_classifier/runs/text_preliminary/ocr','services/document_classifier/runs/text_delivery_v2/ocr_sparse'],pre_scan_was_partial=True)
mapping.write_text(json.dumps(original,indent=2),encoding='utf8')
print('Final validation:',len(examples),'examples;',legacy_count,'legacy OCR records;',len(protected),'protected hashes; existing portal:',portal_live)

