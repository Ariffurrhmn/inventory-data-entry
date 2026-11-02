"""Independent bounded overlap audit of retained candidates and cached SRD archive."""
import csv,hashlib,io,json,os,zipfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"research/datasets"
manifest=list(csv.DictReader((ROOT/"classifier/engine/data/manifest.csv").open(encoding="utf-8")))
splitrows=list(csv.DictReader((ROOT/"classifier/engine/data/splits.csv").open(encoding="utf-8")))
hashmap={}
for row in manifest:hashmap.setdefault(row["sha256"],[]).append(row)
cos=np.cos(np.pi*(2*np.arange(32)[None,:]+1)*np.arange(32)[:,None]/64)
def feature(im):
    im=ImageOps.exif_transpose(im).convert("L").resize((32,32),Image.Resampling.LANCZOS)
    coeff=cos@np.asarray(im,dtype=float)@cos.T
    v=coeff[:8,:8].flatten()[1:]
    return v>np.median(v)
local=[]
for row in splitrows:
    p=ROOT/"classifier/engine"/row["image_path"]
    with Image.open(p) as im:local.append((row,feature(im)))
candidates=[]
for p in (ROOT/"Dataset/external_candidates").rglob("*"):
    if p.suffix.lower() in {".jpg",".jpeg",".png"} and p.is_file():
        candidates.append((str(p.relative_to(ROOT)),p.read_bytes()))
zpath=Path(os.environ["TEMP"])/"classifier-SRD.zip"
archive_members=0
if zpath.exists():
    with zipfile.ZipFile(zpath) as z:
        for name in z.namelist():
            if Path(name).suffix.lower() in {".jpg",".jpeg",".png"}:
                candidates.append(("ExpressExpense SRD archive::"+name,z.read(name)));archive_members+=1
exact=[];near=[];seen=set();errors=[]
for path,data in candidates:
    sha=hashlib.sha256(data).hexdigest()
    if sha in seen:continue
    seen.add(sha)
    for row in hashmap.get(sha,[]):
        exact.append(dict(candidate=path,existing=row["source_path"],sample_id=row["sample_id"],sha256=sha,match="confirmed_byte_identity"))
    if sha in hashmap:continue
    try:
        with Image.open(io.BytesIO(data)) as im:f=feature(im)
    except Exception as e:errors.append(dict(path=path,error=str(e)));continue
    ranked=sorted([(int(np.count_nonzero(f!=g)),row) for row,g in local],key=lambda p:p[0])
    d,row=ranked[0]
    if d<=8:
        near.append(dict(candidate=path,existing=row["source_path"],sample_id=row["sample_id"],phash_hamming_63=d,status="screening_candidate_only_not_confirmed"))
def save(name,rows,fields):
    with (OUT/name).open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
save("overlap_recheck_exact.csv",exact,["candidate","existing","sample_id","sha256","match"])
save("overlap_recheck_near_candidates.csv",near,["candidate","existing","sample_id","phash_hamming_63","status"])
report=dict(date="2026-10-19",existing_manifest_rows=len(manifest),included_comparison_images=len(local),retained_and_archive_image_entries=len(candidates),cached_srd_images=archive_members,unique_candidate_image_bytes=len(seen),exact_correspondences=len(exact),near_screening_candidates=len(near),errors=errors,limitation="Bounded retained samples plus cached SRD archive if present; no claim of full-release disjointness. Perceptual hash similarity is not identity.")
(OUT/"overlap_recheck_validation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2));print("EXACT",json.dumps(exact,indent=2));print("NEAR",json.dumps(near,indent=2))
