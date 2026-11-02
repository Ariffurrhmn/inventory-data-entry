"""Train frozen pretrained image features + classification head; select using validation only."""
import argparse,csv,hashlib,json,random,time
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader,Dataset
from sklearn.metrics import accuracy_score,f1_score
from model import build,preprocess,load_image,CLASSES
from prepare import HERE,read_csv
class Images(Dataset):
 def __init__(self,rows):self.rows=rows;self.transform=preprocess()
 def __len__(self):return len(self.rows)
 def __getitem__(self,i):
  row=self.rows[i];return self.transform(load_image(HERE/row["image_path"])),CLASSES.index(row["label"])
def main():
 p=argparse.ArgumentParser();p.add_argument("--epochs",type=int,default=100);p.add_argument("--seed",type=int,default=2026);p.add_argument("--run",default="baseline");p.add_argument("--threads",type=int,default=4);args=p.parse_args()
 if args.epochs<1:raise ValueError("epochs must be positive")
 out=HERE/"runs"/args.run
 if out.exists():raise SystemExit("Choose a new run name; existing runs are preserved.")
 out.mkdir(parents=True)
 torch.set_num_threads(args.threads);torch.manual_seed(args.seed);random.seed(args.seed);np.random.seed(args.seed)
 torch.hub.set_dir(str(HERE/".cache"))
 rows=read_csv(HERE/"data/splits.csv")
 if any(r["label_status"]!="reviewed" for r in rows):raise ValueError("Unreviewed labels")
 net=build(pretrained=True);net.eval()
 # Extract only train and validation; test images are untouched until evaluate.py.
 features={}
 with torch.inference_mode():
  for split in ["train","val"]:
   selected=[r for r in rows if r["split"]==split]
   xs=[];ys=[]
   for x,y in DataLoader(Images(selected),batch_size=16,shuffle=False,num_workers=0):
    z=net.avgpool(net.features(x)).flatten(1);xs.append(z.clone());ys.append(y)
   features[split]=(torch.cat(xs).clone(),torch.cat(ys).clone())
 features={s:(x.clone(),y.clone()) for s,(x,y) in features.items()}
 head=net.classifier
 counts=torch.bincount(features["train"][1],minlength=4).float()
 loss_fn=torch.nn.CrossEntropyLoss(weight=counts.sum()/(4*counts))
 opt=torch.optim.AdamW(head.parameters(),lr=.001,weight_decay=.01)
 best=-1.;history=[];start=time.time()
 for epoch in range(args.epochs):
  head.train();x,y=features["train"]
  for ix in torch.randperm(len(y)).split(16):
   opt.zero_grad();loss=loss_fn(head(x[ix]),y[ix]);loss.backward();opt.step()
  head.eval()
  with torch.no_grad():
   vx,vy=features["val"];pred=head(vx).argmax(1);score=f1_score(vy.numpy(),pred.numpy(),labels=list(range(4)),average="macro",zero_division=0)
  history.append(dict(epoch=epoch+1,val_macro_f1=float(score)))
  if score>best:
   best=score
   torch.save(dict(state_dict=net.state_dict(),classes=CLASSES,architecture="mobilenet_v3_small",input_size=224,seed=args.seed,epoch=epoch+1,val_macro_f1=float(score),
    split_sha256=hashlib.sha256((HERE/"data/splits.csv").read_bytes()).hexdigest(),training="frozen ImageNet features + trainable classification head"),out/"best.pt")
  if epoch==0 or (epoch+1)%10==0:print(f"epoch {epoch+1}: val macro-F1={score:.3f}; best={best:.3f}",flush=True)
 report=dict(history=history,seconds=time.time()-start,best_val_macro_f1=best,args=vars(args))
 (out/"training.json").write_text(json.dumps(report,indent=2))
 print("Saved "+str(out/"best.pt"),flush=True)
if __name__=="__main__":main()
