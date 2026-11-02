"""Build blind extraction inputs using a predetermined geometry-only policy."""
from pathlib import Path
import json,hashlib,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[4]/'services/document_pipeline'))
from region_evidence import combine
run=HERE/(sys.argv[1] if len(sys.argv)>1 else 'run5')
destination=Path(sys.argv[2]) if len(sys.argv)>2 else HERE
input_target=destination/'blinded-region-inputs.json';provenance_target=destination/'blinded-region-provenance.json'
if input_target.exists() or provenance_target.exists(): raise SystemExit('Refusing to overwrite blinded inputs/provenance; supply a new destination directory.')
destination.mkdir(parents=True,exist_ok=True)
primary_path=HERE.parent/'inputs/ocr-only.json'
rows=json.loads(primary_path.read_text(encoding='utf-8-sig'));out=[];provenance=[]
def digest(b): return hashlib.sha256(b).hexdigest()
for row in rows:
    result_path=run/row['id']/'result.json';result=json.loads(result_path.read_text())
    selected=next((c for c in result['candidates'] if c['layout']['tables'] and c.get('ocr',{}).get('returncode')==0),None)
    region=selected['ocr']['ocr_text'] if selected else ''
    primary=row['ocr_text']; separator='\n\n=== AUTOMATIC RULED-CELL OCR; SEPARATE VIEW; DO NOT DUPLICATE ROWS ===\n'
    text=combine(primary,region) if selected else primary
    out.append({'id':row['id'],'document_type':row['document_type'],'ocr_text':text})
    provenance.append({'id':row['id'],'source_sha256':result['source_sha256'],'primary_input_file_sha256':digest(primary_path.read_bytes()),'primary_ocr_utf8_sha256':digest(primary.encode()),'result_file':str(result_path.relative_to(HERE)),'result_file_sha256':digest(result_path.read_bytes()),'selection_policy':'First candidate in fixed [axis_grid,deskew_grid] order with >=1 grid. Geometry only; no expected values or OCR scoring. No grid => primary alone. Word-box fallback is saved separately and not appended.','selected_method':selected['method'] if selected else None,'region_ocr_utf8_sha256':digest(region.encode()),'region_start_character':len(primary)+len('\n\nBEGIN_AUTOMATIC_REGION_OCR\n') if selected else None,'extraction_source_utf8_sha256':digest(text.encode()),'human_verified':False})
input_target.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
provenance_target.write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')

