"""Export actual AI candidates and BLANK review forms; creates no field truth."""
import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/'services/document_pipeline'))
from field_review import prepare
out=HERE/'review-preparation';out.mkdir(exist_ok=False)
records=json.loads((HERE/'region-response.json').read_text(encoding='utf-8-sig'))
manifest=[]
for sid,record in records.items():
    candidate=out/(sid+'-candidate.json');candidate.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    image=ROOT/f'classifier/demo/images/{sid}.jpg'
    review=prepare(image,candidate)
    (out/(sid+'-blank-review.json')).write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
    manifest.append({'id':sid,'source_kind':'actual_isolated_codex_agent_candidate','human_verified':False,'image':str(image.relative_to(ROOT)),'image_sha256':review['image_sha256'],'candidate_file':candidate.name,'candidate_sha256':review['candidate_sha256'],'independent_field_truth':False})
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('Prepared',len(records),'AI candidates and blank reviews; no ground truth.')
