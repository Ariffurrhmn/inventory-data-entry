"""Validate actual isolated extraction responses; field accuracy is intentionally absent."""
import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/'services/document_pipeline'))
from contract import validate_record

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(output):
    if output.exists():raise SystemExit('Choose new output; no overwrite')
    report={'accuracy_measured':False,'human_verified':False,'contract_sha256':sha(ROOT/'services/document_pipeline/contract.py'),'trials':{}}
    for branch,source in [('primary',HERE.parent/'inputs/ocr-only.json'),('region',HERE/'region-input.json')]:
        response=HERE/(branch+'-response.json')
        if not response.exists():continue
        inputs={r['id']:r for r in json.loads(source.read_text(encoding='utf-8-sig'))}
        records=json.loads(response.read_text(encoding='utf-8-sig'))
        trial={'input_sha256':sha(source),'response_sha256':sha(response),'prompt_sha256':sha(HERE/(branch+'-prompt.txt')),'human_verified':False,'records':{}}
        for sid,r in records.items():
            entry={'rows':len(r.get('line_items',[])),'populated_quantities':sum(x.get('quantity') is not None for x in r.get('line_items',[])),'complete_numeric_rows':sum(all(x.get(k) is not None for k in ('quantity','unit_price','line_total')) for x in r.get('line_items',[])),'proposed_corrections':r.get('corrections',[])}
            for policy in ('literal','grouped_commas'):
                try:
                    a=validate_record(r,inputs[sid]['ocr_text'],numeric_policy=policy)
                    entry[policy]={'schema_valid':True,'classification_preserved':r['document_type']==inputs[sid]['document_type'],**a}
                except (ValueError,TypeError,KeyError) as e:entry[policy]={'schema_valid':False,'error':str(e)}
            trial['records'][sid]=entry
        trial['input_ids_missing']=sorted(set(inputs)-set(records))
        trial['counts']={key:sum(entry[key] for entry in trial['records'].values()) for key in ('rows','populated_quantities','complete_numeric_rows')}
        for policy in ('literal','grouped_commas'):
            audits=[x[policy] for x in trial['records'].values()]
            trial[policy]={'schema_valid':sum(x.get('schema_valid',False) for x in audits),'review_required':sum(x.get('review_required',False) for x in audits),'all_evidence_supported':sum(all(f['status'] in ('supported','supported_normalized') for f in x.get('evidence_findings',[])) and x.get('schema_valid',False) for x in audits),'arithmetic':{status:sum(c['status']==status for x in audits for c in x.get('checks',[])) for status in ('passed','failed','not_applicable')}}
        report['trials'][branch]=trial
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({b:{k:v for k,v in t.items() if k in ('counts','literal','grouped_commas')} for b,t in report['trials'].items()},indent=2))
if __name__=='__main__':run(Path(sys.argv[1]))
