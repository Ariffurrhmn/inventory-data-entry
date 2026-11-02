"""Evaluate a saved run once on held-out test data, preserving predictions and confusion matrix."""
import argparse,hashlib,json,time
from collections import defaultdict
import numpy as np
import torch
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report,confusion_matrix,accuracy_score,f1_score
from model import build,CLASSES
from train import Images
from prepare import HERE,read_csv,write_csv
def main():
 p=argparse.ArgumentParser();p.add_argument("--run",default="baseline");args=p.parse_args()
 torch.set_num_threads(4);out=HERE/"runs"/args.run
 if (out/"evaluation.json").exists():raise SystemExit("Evaluation already recorded; read existing report.")
 checkpoint=torch.load(out/"best.pt",map_location="cpu",weights_only=True)
 if checkpoint["split_sha256"]!=hashlib.sha256((HERE/"data/splits.csv").read_bytes()).hexdigest():raise ValueError("Split manifest changed")
 net=build();net.load_state_dict(checkpoint["state_dict"]);net.eval()
 rows=[r for r in read_csv(HERE/"data/splits.csv") if r["split"]=="test"];truth=[];pred=[];scores=[]
 start=time.time()
 with torch.inference_mode():
  for x,y in DataLoader(Images(rows),batch_size=8,num_workers=0):
   prob=net(x).softmax(1);scores.extend(prob.tolist());pred.extend(prob.argmax(1).tolist());truth.extend(y.tolist())
 report=dict(accuracy=accuracy_score(truth,pred),macro_f1=f1_score(truth,pred,labels=list(range(4)),average="macro",zero_division=0),
  classes=CLASSES,classification_report=classification_report(truth,pred,labels=list(range(4)),target_names=CLASSES,output_dict=True,zero_division=0),
  confusion_matrix=confusion_matrix(truth,pred,labels=list(range(4))).tolist(),test_images=len(rows),seconds=time.time()-start,
  limitation="Small mixed-origin group holdout, including photographed synthetic documents. Not an estimate of real-shop accuracy.",
  score_note="Softmax scores are uncalibrated.")
 (out/"evaluation.json").write_text(json.dumps(report,indent=2))
 predictions=[dict(source_path=r["source_path"],actual=r["label"],predicted=CLASSES[k],score=max(s),correct=r["label"]==CLASSES[k]) for r,k,s in zip(rows,pred,scores)]
 write_csv(out/"predictions.csv",predictions)
 write_csv(out/"confusion_matrix.csv",[dict(actual=CLASSES[i],**dict(zip(CLASSES,cm))) for i,cm in enumerate(report["confusion_matrix"])])
 print(json.dumps(report,indent=2))
if __name__=="__main__":main()
