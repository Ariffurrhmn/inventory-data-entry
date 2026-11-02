import csv,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/'services/document_pipeline'))
from localization import analyze,sha
ids=['76cc99d39da4','f9918570b903','5dffabcb47cb','e396ade11def','cdd7aaa9004d','cc6e515ae67f','398c6ef688e4']
manifest=list(csv.DictReader((ROOT/'classifier/engine/runs/printed_v3_explainable/split_manifest.csv').open(encoding='utf-8-sig')))
out=HERE/(sys.argv[1] if len(sys.argv)>1 else 'run1');out.mkdir(exist_ok=False)
summary=[]
for sid in ids:
    rows=[r for r in manifest if r['sample_id']==sid]
    assert len(rows)==1 and rows[0]['split'] in ['train','val'] and rows[0]['historical_split']!='test' and rows[0]['scope_status']=='eligible',sid
    row=rows[0]; source=ROOT/row['image_path']
    start=time.perf_counter(); result=analyze(source,out/sid,ROOT/'classifier/engine/.cache/tessdata')
    summary.append({'id':sid,'split':row['split'],'historical_split':row['historical_split'],'source_sha256':sha(source),'seconds':round(time.perf_counter()-start,4),'candidates':[{'method':c['method'],'tables':len(c['layout']['tables']),'rows':sum(len(t['rows']) for t in c['layout']['tables']),'ocr_text':c.get('ocr',{}).get('ocr_text',''),'seconds':c.get('ocr',{}).get('seconds'),'rotation':c['layout']['rotation_degrees']} for c in result['candidates']]})
    print(json.dumps(summary[-1]),flush=True)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
