"""Create immutable approximately 60/20/20 splits, preserving reviewed document/template groups."""
import argparse, hashlib, json, random
from collections import Counter,defaultdict
from prepare import HERE,CLASSES,read_csv,write_csv
def make_splits(rows,seed=2026):
 rows=[dict(r) for r in rows if r["include"]=="yes"]
 if any(r["label_status"]!="reviewed" for r in rows):
  raise ValueError("Review labels/groups in labels.csv first, then rerun prepare.py.")
 groups=defaultdict(list)
 for r in rows:
  if r["label"] not in CLASSES: raise ValueError("Unknown label: "+r["label"])
  groups[r["group_id"]].append(r)
 hashes=defaultdict(set)
 for r in rows: hashes[r["sha256"]].add(r["group_id"])
 if any(len(g)>1 for g in hashes.values()): raise ValueError("Identical inputs assigned to different groups.")
 if any(len({r["label"] for r in rs})!=1 for rs in groups.values()): raise ValueError("Mixed-label group.")
 allocation={}; rng=random.Random(seed)
 for label in CLASSES:
  local=sorted(g for g,rs in groups.items() if rs[0]["label"]==label)
  if len(local)<3: raise ValueError(f"{label}: need >=3 independent groups, got {len(local)}")
  n=max(1,round(len(local)*0.2));total=sum(len(groups[g]) for g in local)
  # Optimize counts only; no model outputs or image features affect split selection.
  best=None
  for _ in range(1000):
   candidate=local.copy();rng.shuffle(candidate)
   proposed={g:("test" if i<n else "val" if i<2*n else "train") for i,g in enumerate(candidate)}
   counts=Counter()
   for g,s in proposed.items():counts[s]+=len(groups[g])
   score=sum((counts[s]/total-target)**2 for s,target in [("train",.6),("val",.2),("test",.2)])
   if best is None or score<best[0]:best=(score,proposed)
  allocation.update(best[1])
 for r in rows:r["split"]=allocation[r["group_id"]]
 return rows
def main():
 parser=argparse.ArgumentParser();parser.add_argument("--seed",type=int,default=2026);args=parser.parse_args()
 dest=HERE/"data/splits.csv";rows=make_splits(read_csv(HERE/"data/manifest.csv"),args.seed)
 if dest.exists() and read_csv(dest)!=rows: raise SystemExit("Refusing to change frozen splits. Version/archive existing splits first.")
 write_csv(dest,rows)
 summary={s:dict(Counter(r["label"] for r in rows if r["split"]==s)) for s in ["train","val","test"]}
 (HERE/"data/split_summary.json").write_text(json.dumps(dict(seed=args.seed,counts=summary,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
  limitation="Known original/photo and template relationships grouped by visual review. Small mixed-origin corpus; unknown relationships may remain."),indent=2))
 print(json.dumps(summary,indent=2))
if __name__=="__main__": main()
