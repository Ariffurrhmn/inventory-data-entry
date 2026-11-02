"""Audit saved automatic OCR artifacts; no generators or reference answers."""
from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
run=HERE/(sys.argv[1] if len(sys.argv)>1 else 'run6')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
summary=json.loads((run/'summary.json').read_text());findings=[]
for row in summary:
    p=run/row['id'];record=json.loads((p/'result.json').read_text())
    assert sha(Path(record['source']))==record['source_sha256']
    assert sha(p/'localization-source.py')==record['module_sha256']==sha(ROOT/'services/document_pipeline/localization.py')
    for name,ocr in [(c['method'],c['ocr']) for c in record['candidates'] if 'ocr' in c]+[('word_boxes_psm11',record['word_box_fallback'])]:
        assert ocr['returncode']==0
        assert sha(p/(name+'.png'))==ocr['image_sha256']
        assert sha(p/(name+'.txt'))==ocr['text_sha256']
        assert (p/(name+'.tsv')).exists()
    selected=next((c for c in record['candidates'] if c['layout']['tables'] and c.get('ocr',{}).get('returncode')==0),None)
    findings.append({'id':row['id'],'tables':len(selected['layout']['tables']) if selected else 0,'rows_including_headers':sum(len(t['rows']) for t in selected['layout']['tables']) if selected else 0,'columns_per_table':[len(t['rows'][0]) for t in selected['layout']['tables']] if selected else [],'seconds':row['seconds']})
result={'checks':'source/module/source-snapshot/OCR PNG/TXT hashes, successful commands, TSV presence; seven development manifest guards executed by runner','human_verified':False,'documents':findings,'documents_with_grid':sum(r['tables']>0 for r in findings),'total_wall_seconds':round(sum(r['seconds'] for r in findings),4),'total_ocr_seconds':round(sum(c.get('seconds') or 0 for r in summary for c in r['candidates']),4),'limits':'Grid presence and source agreement are not localization or extraction accuracy. OCR total excludes word-box fallback; wall includes all processing.'}
if len(sys.argv)>2:
    with Path(sys.argv[2]).open('x',encoding='utf-8') as stream: stream.write(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
