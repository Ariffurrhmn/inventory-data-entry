"""Fresh local OCR + automatic regions + actual extraction import, isolated database."""
import argparse,base64,hashlib,json,sys,time
from pathlib import Path
from tempfile import TemporaryDirectory
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'services/document_pipeline'))
sys.path.insert(0,str(ROOT/'classifier/engine'))
from gateway import Store
from inference import Predictor
from region_evidence import make_region_processor

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--responses',type=Path);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    records=json.loads(a.responses.read_text(encoding='utf-8-sig')) if a.responses else {}
    begin=time.perf_counter();predictor=Predictor();startup=time.perf_counter()-begin
    summary={'predictor_startup_seconds':startup,'human_verified':False,'accuracy_measured':False,'records':{}}
    with TemporaryDirectory(prefix='region-smoke-') as temp:
        store=Store(Path(temp)/'submissions.sqlite3',predictor,make_region_processor(a.output/'regions',ROOT/'classifier/engine/.cache/tessdata'))
        for sid in ('76cc99d39da4','f9918570b903'):
            image=ROOT/f'classifier/demo/images/{sid}.jpg'
            data={'filename':image.name,'image_base64':base64.b64encode(image.read_bytes()).decode()}
            start=time.perf_counter();result,replay=store.submit('fresh-region-'+sid,data);elapsed=time.perf_counter()-start
            assert result['state']=='awaiting_extraction',result
            source=result['extraction_source'];assert source['status']=='regions_added'
            assert source['source_image_sha256']==hashlib.sha256(image.read_bytes()).hexdigest()
            if sid in records:
                result=store.attach(result['submission_id'],records[sid]);assert result['state']=='completed'
                consumer=store.consumer(result['submission_id']);assert consumer['inventory_updated'] is False
                result['consumer_observation']=consumer
            (a.output/(sid+'.json')).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
            summary['records'][sid]={'ocr_and_regions_seconds':elapsed,'state':result['state'],'label':result['classification']['label'],'region_method':source['method'],'review_required':result.get('verification',{}).get('review_required'),'evidence_findings':result.get('verification',{}).get('evidence_findings',[])}
            print(json.dumps({'id':sid,**summary['records'][sid]},ensure_ascii=False),flush=True)
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
