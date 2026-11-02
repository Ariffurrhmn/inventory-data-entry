import pathlib,csv,json,hashlib,urllib.parse
from PIL import Image
B=pathlib.Path(r'E:\.shortcut-targets-by-id\1yOBXNuSORBcOSWDhEg-YF1MEWIDvc8J2\Capstone- Inventory Management System');D=B/'Dataset/external_candidates';R=B/'research/datasets'
def csvout(path,rows,fields=None):
 with path.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
spec=[
('company_documents_v2','Company Documents v2','https://huggingface.co/datasets/AyoubChLin/Company-document-dataset-v2','https://huggingface.co/datasets/AyoubChLin/Company-document-dataset-v2/tree/main','Apache-2.0 generated documents; MIT/BSD source notices','research permitted subject to notices','purchase_order; packing_slip->delivery_note; receipt; GRN pending','publisher: PO50313; packing47740; receipt16456; GRN3689; includes French; target English yield unknown','7 English PDFs visually checked: 2 PO/2 packing/1 receipt/2 held GRN','English/French; born-digital printed synthetic; simulated scan/photo subset; four layout families','document_type and locale; JSON words/boxes; generated text not OCR','filter English; review copies; render PDFs; run OCR; group generator/doc variants','same-generator and Northwind predecessor overlap possible; no existing match confirmed','ready for bounded synthetic acquisition','0e9f5198e7e09f858834e544f96ec12436fdbb5e'),
('expressexpense_srd','ExpressExpense SRD','https://expressexpense.com/blog/free-receipt-images-ocr-machine-learning-dataset/','https://expressexpense.com/large-receipt-image-dataset-SRD.zip','MIT explicitly on publisher page; cite ExpressExpense','research permitted with license/attribution','receipt; explicit copy-marked subset->customer_copy','200 archive members verified; total class yields unknown','6 photos visually checked; 5 copy-marked are existing SHA256 matches','inspected English printed photos; handwriting/signature areas; merchant/capture variation','images only; no OCR transcript or document-label manifest','manually label copy cues; OCR; remove overlap before future merge','5 exact current matches; WildReceipt/web overlap possible not confirmed','ready; review for new unique examples','MD5:c8eb0f2d286da5ab742e7a5b59f15147'),
('docile','DocILE','https://docile.rossum.ai/','https://github.com/rossumai/docile','full dataset terms unverified; code MIT is distinct','research access offered via token form; no submission made','purchase_order/receipt candidates; other types not automatic mapping','publisher 6680 annotated; 1152 clusters; per-target counts unknown','1 public test PDF plus annotation/OCR inspected; tax_invoice; zero eligible PO verified','annotated set English printed PDF/scanned; heterogeneous business layouts','metadata.document_type/source/cluster; field/line-item JSON; predicted DocTR OCR','authorized token; filter types then visual review; render and group','shared UCSF/PIF ancestors with other benchmarks; no local match confirmed','conditional access and rights; sample is ineligible','public repo test fixture 516f2d61ea404b30a9192a72'),
('sroie','ICDAR 2019 SROIE','https://rrc.cvc.uab.es/?ch=13','https://github.com/zzzDavid/ICDAR-2019-SROIE','original dataset license unclear; mirror implementation MIT does not settle image rights','research permission requires original terms confirmation','receipt; copy-marked subset only if reviewed','paper1000; repackaging987; full usable count unverified','2 mirrored images and CSV box/text files inspected','English-oriented Malaysian printed scans; faint printing; handwriting marks in sample','quadrilateral+transcript CSV; extraction tasks; no four-class document labels','verify version/rights; filter language/payment/copy; parse commas carefully','mirrors are not independent; no current match confirmed','conditional original terms and release verification','mirror master retrieved 2026-10-19'),
('cord','CORD v2','https://github.com/clovaai/cord','https://huggingface.co/datasets/naver-clova-ix/cord-v2','CC-BY-4.0 explicit NAVER notice','research permitted with attribution/modification notices','receipt only after language/copy review','publisher public1000; 800train/100validation/100test; English yield unverified','2 viewer images and ground_truth JSON inspected; row8 existing visual match','Indonesian printed receipt photographs; blur/backgrounds/redactions; not English-first','valid_line word text/quads/categories; meta image_id; extraction not document types','exclude initial English acquisition; retain provenance; run project OCR for later diagnostics','v0/v1/v2 share images; row8 confirmed visual derivative of existing image','provenance/optional multilingual only','7f0115a4b758a71d6473b8d085751692da2fef98'),
('wildreceipt','WildReceipt','https://arxiv.org/html/2103.14470','https://download.openmmlab.com/mmocr/data/wildreceipt.tar','N/A in OpenMMLab dataset metadata; unclear','research use not established','receipt; potential copy-marked subset','paper1740 with conflicting table1768; paper1268/472; actual train1267 rows','46 images retained from10MiB prefix; 8 visually checked;21 transcript cue candidates not labels','English printed photos with folds/perspective/backgrounds; some handwriting','JSONL file_name/dimensions/annotations box,text,numeric extraction label','clarify license; inspect candidate images; rebuild document labels; OCR','possible cross-web/SRD overlap; none confirmed','quarantine pending rights','archive HEAD size185323520; Range0-10485759'),
('roboflow_purchase_order_set2','PURCHSE ORDER_SET2','https://universe.roboflow.com/purchase-order/purchse-order_set2','https://universe.roboflow.com/purchase-order/purchse-order_set2/browse','uploader declares CC-BY-4.0; underlying provenance unknown','uploader license permits research; source-rights/export review pending','purchase_order candidates only','uploader882 images;43 object categories; usable PO count unknown','2 public thumbnails;1 visibly PURCHASE ORDER;other inconclusive','printed monochrome form previews;full language/capture/handwriting/diversity unknown','field object categories; full annotations and OCR transcripts not inspected','authorized full-resolution export then inspect; manual document labels; OCR','local .rf filenames do not confirm project match; no match confirmed','conditional; thumbnails insufficient for OCR','publisher image IDs02ONWPxdYgODsd6hIRgh;04uLn8l5jyHQhCUbXOOX'),
('senga_header_10_03','Senga header-dataset-10-03','https://huggingface.co/datasets/senga-ml/header-dataset-10-03','https://huggingface.co/datasets/senga-ml/header-dataset-10-03','unclear; inaccessible','not established; live page/API/rows HTTP401','purchase_order/delivery_note lead; hybrid invoice/delivery pending','indexed preview530train; current count unverified','no downloaded image or annotation file; no visual assessment','indexed Kenyan business names; language/capture/handwriting/layout yield unknown','indexed gt_parse.header.document_type; no actual schema validation','obtain authorized access and terms; inspect images then labels','unknown; no matches claimed','access-dependent lead; not recommended yet','indexed preview versus live401 on2026-10-19'),
('chic','CHIC','https://arxiv.org/html/2305.01054','https://arxiv.org/abs/2305.01054','dataset terms unverified; paper license is not dataset license','not established','possible purchase_order mining; target yields unknown','paper774; component paragraph770; neither usable target count','no local dataset samples; paper only','English/French/German/Spanish/Italian; archival documents; printed/forms mix','paper describes OCR and VQA text/boxes; no verified target labels','locate authoritative release/terms; English filtering; visual relabel','derived from RVL-CDIP/XFUND; source overlap inherent','low-priority unverified lead','paper2305.01054v1'),
('fatura','FATURA','https://zenodo.org/records/8261508','https://zenodo.org/records/8261508/files/FATURA.zip','CC-BY-4.0 verified Zenodo API','research permitted with attribution; unsuitable direct class mapping','invoice is not automatic PO/receipt/copy','publisher10000 generated images;50templates; no target eligible count','no local dataset image/annotation inspection; rejected before archive','English generated printed invoices;50template layouts','publisher24 extraction object categories;3JSON formats;not document types','do not acquire for initial four classes; would need separate scope','template variants related; no local match confirmed','reject initial acquisition','Zenodo8261508v1;363504027byte archive'),
('rvl_cdip','RVL-CDIP','https://adamharley.com/rvl-cdip/','https://adamharley.com/rvl-cdip/','publisher refers to UCSF rights; blanket dataset terms unresolved','not established as blanket permission','forms/invoices require manual mining; no direct target categories','publisher400000 pages;16classes;25000/class; target yields unknown','no local sample inspection; no37GB archive fetched','archival English grayscale scans; printed and handwritten category mix','path-to-TIFF plus numeric image class; OCR referenced via IIT-CDIP','reject bulk initial acquisition; manual screening if reconsidered','UCSF/IIT/CDIP overlaps possible with DocILE/CHIC/DocVQA','reject bulk acquisition','publisher observed2026-10-19')]
fields=['dataset_id','dataset_name','original_source_url','access_url','license','research_use','mapping','counts_evidence','actual_inspection','language_capture_layout','annotations','required_work','overlap','recommendation','version_evidence']
rows=[dict(zip(fields,x),checked_date='2026-10-19') for x in spec];csvout(R/'sources.csv',rows)
# Build a file-level register; source URL refers to fetch or parent; all source filenames are retained.
repo='https://raw.githubusercontent.com/'; records=[]
for p in sorted(D.rglob('*')):
 if not p.is_file() or p.name in ['desktop.ini','PROVENANCE.md']:continue
 rel=p.relative_to(D);ds=rel.parts[0];s='/'.join(rel.parts[1:]);kind='download';parent='';url=''
 if ds=='company_documents_v2':
  stem=s.removesuffix('.preview.png').removesuffix('.text.txt')
  if s.endswith(('.preview.png','.text.txt')):kind='derived';parent=stem+'.pdf';url='https://huggingface.co/datasets/AyoubChLin/Company-document-dataset-v2'
  elif s.startswith('rows_'):
   cfg=s.removeprefix('rows_').removesuffix('.json').removesuffix('_0');url=f'https://datasets-server.huggingface.co/rows?dataset=AyoubChLin/Company-document-dataset-v2&config={cfg}&split=train&offset=0&length=3'
  elif s.endswith(('.pdf','.pdf.png')):
   target=s.removesuffix('.png');cfg=target.split('/')[0]
   candidates=list((D/ds).glob('rows_'+cfg+'*.json'))
   for q in candidates:
    for x in json.loads(q.read_text(encoding='utf-8'))['rows']:
     if x['row']['file_name']==target:
      url=x['row']['pdf']['thumbnail']['src'] if s.endswith('.png') else x['row']['pdf']['src'];parent=q.name
   if s.endswith('.png'):kind='publisher_preview'
  else:url=f'https://huggingface.co/datasets/AyoubChLin/Company-document-dataset-v2/resolve/0e9f5198e7e09f858834e544f96ec12436fdbb5e/{s}'
 elif ds=='sroie':url=repo+'zzzDavid/ICDAR-2019-SROIE/master/'+('data/'+s if s.startswith(('img/','box/')) else s)
 elif ds=='docile':
  if s.endswith(('.preview.png','.text.txt')):kind='derived';parent=s.rsplit('.',2)[0]+'.pdf';url=repo+'rossumai/docile/main/tests/data/sample-dataset/'+parent
  else:url=repo+'rossumai/docile/main/tests/data/sample-dataset/'+s
 elif ds=='expressexpense_srd':
  url='https://expressexpense.com/large-receipt-image-dataset-SRD.zip';parent=s
  if p.suffix.lower()=='.jpg':kind='archive_member'
  else:kind='derived_archive_inventory'
 elif ds=='cord':
  if s.startswith('viewer/'):
   n=rel.parts[-2];url=f'https://datasets-server.huggingface.co/assets/naver-clova-ix/cord-v2/--/default/train/{n}/image/image.jpg';parent='first_rows_v2.json; meta.image_id='+n
  elif s.startswith('ground_truth_'):url='https://datasets-server.huggingface.co/first-rows?dataset=naver-clova-ix/cord-v2&config=default&split=train';kind='extracted_annotation';parent='first_rows_v2.json'
  elif s=='first_rows_v2.json':url='https://datasets-server.huggingface.co/first-rows?dataset=naver-clova-ix/cord-v2&config=default&split=train'
  else:url=repo+'clovaai/cord/master/'+('figure/sample.png' if s=='sample.png' else s)
 elif ds=='wildreceipt':
  if s=='metafile.yml':url=repo+'open-mmlab/mmocr/main/dataset_zoo/wildreceipt/metafile.yml'
  else:url='https://download.openmmlab.com/mmocr/data/wildreceipt.tar';parent=s;kind='archive_member' if s.startswith('wildreceipt/') else 'derived_range_analysis'
 elif ds=='roboflow_purchase_order_set2':url='https://source.roboflow.com/kzu4dbllamXVkAh4MwrPaNdYUG93/'+s;kind='publisher_thumbnail'
 records.append(dict(dataset_id=ds,local_path=str(p.relative_to(B)).replace('\\','/'),source_url=url,source_member_or_parent=parent,kind=kind,bytes=p.stat().st_size,sha256=sha(p),retrieved_date='2026-10-19',notes='Source URL may be an expiring publisher viewer URL; stable row metadata is retained.' if 'Signature=' in url else ''))
csvout(R/'sample_provenance.csv',records)
# Visual review log: explicit subset only, no label changes to classifier manifests.
reviews=[]
def add(ds,path,mapping,status,notes):reviews.append(dict(dataset_id=ds,source_sample=path,proposed_mapping=mapping,review_status=status,review_date='2026-10-19',notes=notes))
for p in sorted((D/'company_documents_v2').rglob('*.pdf')):
 typ=p.parent.name;mapping={'purchase_order':'purchase_order','packing_slip':'delivery_note','receipt':'receipt'}.get(typ,'pending')
 add('company_documents_v2',str(p.relative_to(D/'company_documents_v2')).replace('\\','/'),mapping,'visually_inspected','English synthetic printed PDF; '+('goods received note needs taxonomy decision' if mapping=='pending' else 'clear document title; source is synthetic'))
for p in sorted((D/'expressexpense_srd').glob('*.jpg')):
 add('expressexpense_srd',p.name,'receipt' if p.name.startswith('1078-') else 'customer_copy','visually_inspected','additional receipt candidate; confirm full-page copy status on intake' if p.name.startswith('1078-') else 'Explicit Customer/Guest Copy; SHA256 match to current corpus, not new data')
for n in ['000','001']:add('sroie','img/'+n+'.jpg','receipt','visually_inspected','Printed Malaysian receipt; cash/payment indication; no visible copy cue; rights pending')
for n in [0,8]:add('cord',f'viewer/train/{n}/image.jpg','receipt','visually_inspected','Indonesian; exclude English-first addition; '+('confirmed same visual document as current cord-train-0008.jpg' if n==8 else 'photograph with background'))
for p in list((D/'wildreceipt').rglob('*.jpeg'))[:8]:
 add('wildreceipt',str(p.relative_to(D/'wildreceipt')).replace('\\','/'),'receipt_candidate','visually_inspected','Printed retail/restaurant receipt photo; field labels not document labels; rights pending; copy status needs full-resolution intake review')
add('docile','pdfs/516f2d61ea404b30a9192a72.pdf','exclude','visually_inspected','Sample invoice, metadata tax_invoice; not verified payment receipt or PO')
add('roboflow_purchase_order_set2','02ONWPxdYgODsd6hIRgh/thumb.jpg','purchase_order_candidate','visually_inspected','Visible PURCHASE ORDER title; thumbnail insufficient for OCR acquisition')
add('roboflow_purchase_order_set2','04uLn8l5jyHQhCUbXOOX/thumb.jpg','pending','visually_inspected','Low-resolution monochrome form; cannot reliably confirm document class')
csvout(R/'sample_review.csv',reviews)
# Match evidence.
matches=[]
for name,current in [('1085-receipt.jpg','express_srd_1085-receipt.jpg'),('1057-receipt.jpg','1057-receipt.jpg'),('1073-receipt.jpg','1073-receipt.jpg'),('1164-receipt.jpg','1164-receipt.jpg'),('1176-receipt.jpg','1176-receipt.jpg')]:
 p=D/'expressexpense_srd'/name;q=B/'Dataset/Customer_Copy'/current
 assert sha(p)==sha(q)
 matches.append(dict(existing_path=str(q.relative_to(B)),candidate_path=str(p.relative_to(B)),match_type='confirmed_byte_identity',existing_sha256=sha(q),candidate_sha256=sha(p),metric='SHA256 equality'))
p=D/'cord/viewer/train/8/image.jpg';q=B/'Dataset/Receipt/cord-train-0008.jpg'
matches.append(dict(existing_path=str(q.relative_to(B)),candidate_path=str(p.relative_to(B)),match_type='confirmed_visual_derivative_not_byte_identical',existing_sha256=sha(q),candidate_sha256=sha(p),metric='visual paired inspection; equal864x1296; decoded RGB MAE1.8797897852842556/255'))
csvout(R/'overlap_matches.csv',matches)
for folder in D.iterdir():
 if not folder.is_dir():continue
 source=next((x for x in rows if x['dataset_id']==folder.name),None)
 if source:
  (folder/'PROVENANCE.md').write_text('# Candidate quarantine: '+source['dataset_name']+'\n\nChecked 2026-10-19. Source: '+source['original_source_url']+'\n\nAccess: '+source['access_url']+'\n\nRights: '+source['license']+'\n\nInspection: '+source['actual_inspection']+'\n\nDecision: '+source['recommendation']+'\n\nFull local file hashes and source/member mappings: research/datasets/sample_provenance.csv. Visual review decisions: research/datasets/sample_review.csv. These are research candidates only, not approved training labels. Preserve source filenames and related templates. No acceptance of account terms or external messages occurred.\n',encoding='utf8')
print('registered sources',len(rows),'files',len(records),'visual reviews',len(reviews),'matches',len(matches))
# verify report-finalization preservation check
baseline=list(csv.DictReader((R/'protected_files_before_finalization.csv').open(encoding='utf-8-sig')))
checks=[{'path':x['Path'],'sha256':sha(pathlib.Path(x['Path'])),'unchanged':sha(pathlib.Path(x['Path'])).upper()==x['Hash'].upper()} for x in baseline]
assert all(x['unchanged'] for x in checks)
(R/'validation.json').write_text(json.dumps({'date':'2026-10-19','scope':'protected classifier hashes checked across final report writing only','protected_files':checks,'sources':len(rows),'file_provenance_rows':len(records),'visual_review_rows':len(reviews),'confirmed_correspondences':len(matches)},indent=2))


