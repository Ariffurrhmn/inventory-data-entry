"""Apply one visually reviewed batch; refuses edited/person-reviewed drafts and repeat runs."""
from pathlib import Path
import json,sys,hashlib
from datetime import datetime,timezone
AUDIT=Path(__file__).resolve().parent
ROOT=AUDIT.parents[3]
sys.path.insert(0,str(ROOT/'services/annotation_portal'))
from server import Catalog,Store,validate_review,Conflict
assert not (AUDIT/'applied.json').exists(),'Already applied; preserve this batch.'
catalog=Catalog(ROOT);store=Store(ROOT/'Dataset/annotations/human_review/reviews.sqlite3')
plan=json.loads((AUDIT/'review_plan.json').read_text(encoding='utf-8'))
previous=store.all_latest();results=[];exports=[]
for item in plan:
 sid=item['sample_id'];detail=catalog.detail(sid,store);saved=detail['saved'];ref=detail['reference'];old=ref['transcription']['full_text']
 if saved and (saved['text']!=old or saved['label']!=detail['record']['label'] or saved['status']!='draft' or saved.get('reviewer','').strip() or saved.get('notes','').strip() or saved.get('uncertainties','')!='\n'.join(ref['review']['uncertainties'])):
  results.append(dict(sample_id=sid,result='skipped_edited_or_named_review'));continue
 text=old
 for source,target in item['replacements']:
  assert source in text,(sid,source)
  text=text.replace(source,target)
 data=dict(text=text,label=detail['record']['label'],status='needs_review',reviewer='Codex (AI visual review)',reviewer_type='ai',verified_confirmation=False,uncertainties=item['uncertainties'],notes='Second-pass visual review by Codex (AI), authorized by the user. Not an independent human review. Masked content was not reconstructed. '+item['notes'],expected_revision=saved['revision'] if saved else 0,text_source=detail['reference_path'])
 detail['_image_path']=catalog.image_path(sid)
 payload=validate_review(data,detail)
 try:record=store.save(sid,data['expected_revision'],payload)
 except Conflict:
  results.append(dict(sample_id=sid,result='skipped_concurrent_save'));continue
 assert record['human_verified'] is False and record['reviewer_type']=='ai'
 exports.append(record);results.append(dict(sample_id=sid,result='saved_ai_review',revision=record['revision'],prior_draft_preserved=bool(saved),text_changed=text!=old,payment_status_flag=item.get('payment_flag',False),split=detail['record']['split']))
for sid,old_record in previous.items():assert any(r==old_record for r in store.history(sid)),sid
before=json.loads((AUDIT/'protected_before.json').read_text(encoding='utf-8'))
for path,h in before.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h,path
(AUDIT/'reviews.json').write_text(json.dumps(exports,ensure_ascii=False,indent=2),encoding='utf-8')
report=dict(date=datetime.now(timezone.utc).isoformat(),visually_inspected=10,saved=sum(r['result']=='saved_ai_review' for r in results),text_corrected=sum(r.get('text_changed',False) for r in results),payment_status_flags=sum(r.get('payment_status_flag',False) for r in results),human_verified_created=0,reviewer_type='ai',status='needs_review',preexisting_reviews_preserved=len(previous),protected_sources_unchanged=len(before),model_training=False,model_evaluation=False,results=results)
(AUDIT/'applied.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
