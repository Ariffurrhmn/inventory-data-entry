"""Read-only, no-download feasibility probe; creates a new report, never overwrites."""
import argparse, ctypes, hashlib, importlib.util, json, os, platform, shutil, subprocess, sys, time
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
    if a.output.exists(): raise SystemExit('Refusing to overwrite report')
    class Memory(ctypes.Structure):
        _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(x,ctypes.c_ulonglong) for x in ('total_physical','available_physical','total_pagefile','available_pagefile','total_virtual','available_virtual','extended')]
    m=Memory(); m.length=ctypes.sizeof(m); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    report={'python':sys.executable,'platform':platform.platform(),'logical_cpus':os.cpu_count(),'memory_bytes':{x:getattr(m,x) for x in ('total_physical','available_physical')},'packages':{x:bool(importlib.util.find_spec(x)) for x in ('torch','transformers','llama_cpp','cv2','psutil','onnxruntime')},'executables':{x:shutil.which(x) for x in ('ollama','llama-cli','llama-server','nvidia-smi')},'cache_files':[],'downloads':False,'generation_executed':False}
    caches=[Path.home()/'.cache/huggingface/hub',Path(sys.executable).parents[2]/'hf-cache']
    for cache in caches:
        for model in cache.glob('models--*'):
            files=[{'path':str(f),'bytes':f.stat().st_size} for f in model.rglob('*') if f.is_file()]
            report['cache_files'].append({'model':model.name,'files':files})
    import torch
    report['torch']={'version':torch.__version__,'cuda_available':torch.cuda.is_available()}
    os.environ['HF_HUB_OFFLINE']='1'; os.environ['TRANSFORMERS_OFFLINE']='1'
    start=time.perf_counter()
    try:
        from transformers import AutoModelForCausalLM
        AutoModelForCausalLM.from_pretrained(str(Path.home()/'.cache/huggingface/hub/models--google--gemma-2b-it/snapshots/96988410cbdaeb8d5093d1ebdc5a8fb563e02bad'),local_files_only=True)
        report['offline_load']='unexpected success'
    except Exception as e:
        report['offline_load']={'exception':type(e).__name__,'message':str(e)}
    report['offline_load_seconds']=time.perf_counter()-start
    report['limitations']=['No generative weights available in inspected caches; classifier encoders are not extraction generators.','No generation latency, schema compliance, extraction accuracy or model resource use measured.','Current free memory is a snapshot, not peak capacity. CPU inference may be possible after provisioning but is unvalidated.','No weights downloaded, no paid API used, Codex agents are experimental handoffs.']
    report['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='cache_files'},indent=2))
if __name__=='__main__':main()
