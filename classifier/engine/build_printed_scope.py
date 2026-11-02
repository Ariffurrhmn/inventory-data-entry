"""Build a versioned printed-only subset from explicit per-image scope decisions."""
import argparse,csv,json,hashlib
from collections import Counter,defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
DEFAULT=ROOT/'Dataset/annotations/scope/printed-only-v1'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write_csv(path,rows):
 with path.open('w',encoding='utf-8',newline='') as handle:
  writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def build(directory,activate=False):
 directory=Path(directory).resolve()
 if (directory/'validation.json').exists():raise SystemExit('Completed scope edition exists; preserve it.')
 source=json.loads((directory/'source_inventory.json').read_text(encoding='utf-8'))
 decisions=json.loads((directory/'decisions.json').read_text(encoding='utf-8'))
 assert len(source)==len({r['sample_id'] for r in source})==len(decisions)
 assert {r['sample_id'] for r in source}==set(decisions)
 protected=[HERE/'data/manifest.csv',HERE/'data/splits.csv',HERE/'labels.csv',HERE/'runs/text_preliminary/selection.json',HERE/'runs/text_preliminary/evaluation.json',HERE/'runs/text_preliminary/original_ocr.joblib',ROOT/'Dataset/annotations/review_actions.json']
 protected+=list((ROOT/'Dataset/annotations/versions/utf8-v2/transcriptions').glob('*.json'))
 before={p.relative_to(ROOT).as_posix():sha(p) for p in protected}
 (directory/'protected_before.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
 manifest=[]
 for row in source:
  sid=row['sample_id'];decision=decisions[sid];style=decision['content_style']
  assert style in ['printed','printed_signature_only','handwriting_dependent','needs_printed_region']
  status='excluded_handwriting' if style=='handwriting_dependent' else 'held_for_printed_region' if style=='needs_printed_region' else 'eligible' if row['included'] else 'previously_excluded'
  image=ROOT/row['image_path'];assert image.is_file()
  manifest.append(dict(sample_id=sid,image_path=row['image_path'],label=row['label'],split=row['split'],group_id=row['group_id'],source=row['source'],source_path=row['source_path'],historical_included='yes' if row['included'] else 'no',include='yes' if status=='eligible' else 'no',scope_status=status,content_style=style,scope_reason=decision['reason'],scope_evidence=decision['evidence'],image_sha256=sha(image),human_verified='false'))
 eligible=[r for r in manifest if r['include']=='yes']
 assert all(r['historical_included']=='yes' for r in eligible)
 groups=defaultdict(set)
 for row in eligible:groups[row['group_id']].add(row['split'])
 assert all(len(splits)==1 for splits in groups.values()),'Existing family crossed split boundaries'
 write_csv(directory/'manifest.csv',manifest);write_csv(directory/'eligible_manifest.csv',eligible)
 write_csv(directory/'excluded_or_held.csv',[r for r in manifest if r['include']=='no'])
 flagged={r['sample_id'] for r in csv.DictReader((ROOT/'Dataset/annotations/versions/utf8-v2/review_queue.csv').open(encoding='utf-8'))}
 write_csv(directory/'review_queue.csv',[r for r in eligible if r['sample_id'] in flagged])
 for path,h in before.items():assert sha(ROOT/path)==h,path
 report=dict(date='2026-10-20',records_screened=len(manifest),method='AI visual scope screening of all 236 contact-sheet images, selected individual enlargements; not full-text/human verification',scope_status_counts=dict(Counter(r['scope_status'] for r in manifest)),eligible=len(eligible),eligible_classes=dict(Counter(r['label'] for r in eligible)),eligible_splits=dict(Counter(r['split'] for r in eligible)),eligible_originals=sum(not r['sample_id'].startswith(('srd_','company_')) for r in eligible),eligible_intake=sum(r['sample_id'].startswith(('srd_','company_')) for r in eligible),eligible_flagged_review_queue=sum(r['sample_id'] in flagged for r in eligible),protected_files_unchanged=len(before),unchanged_existing_splits=True,new_training=False,new_test_evaluation=False,human_verified_created=0,limitations=['Content-style screening is not a verified transcription or label audit.','English-only, payment and taxonomy questions remain independent quality gates.','Held originals are excluded until a separately reviewed printed-only derivative exists.','Incidental signatures are not transcription targets; no signature-recognition guarantee is made for legacy OCR.','Existing legacy model is not retrained under printed-only scope.'])
 (directory/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 if activate:
  (ROOT/'Dataset/annotations/scope/active.json').write_text(json.dumps(dict(version=directory.name,manifest=(directory/'manifest.csv').relative_to(ROOT).as_posix()),indent=2),encoding='utf-8')
 print(json.dumps(report,indent=2))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--directory',type=Path,default=DEFAULT);parser.add_argument('--activate',action='store_true');args=parser.parse_args();build(args.directory,args.activate)
