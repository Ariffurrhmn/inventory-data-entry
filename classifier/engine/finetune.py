"""Fine-tune the last two visual blocks, selecting only on validation macro-F1."""
import argparse,hashlib,json,random,time
import numpy as np
import torch
from torch.utils.data import DataLoader,TensorDataset
from sklearn.metrics import f1_score
from model import build,CLASSES
from train import Images
from prepare import HERE,read_csv
def main():
 p=argparse.ArgumentParser();p.add_argument("--from-run",default="baseline");p.add_argument("--run",default="finetuned");p.add_argument("--epochs",type=int,default=20);args=p.parse_args()
 if args.epochs<1:raise ValueError("epochs must be positive")
 torch.set_num_threads(4);torch.manual_seed(2026);np.random.seed(2026);random.seed(2026)
 out=HERE/"runs"/args.run
 if out.exists():raise SystemExit("Existing run preserved; choose another name.")
 out.mkdir(parents=True)
 checkpoint=torch.load(HERE/"runs"/args.from_run/"best.pt",map_location="cpu",weights_only=True)
 fingerprint=hashlib.sha256((HERE/"data/splits.csv").read_bytes()).hexdigest()
 if checkpoint["split_sha256"]!=fingerprint:raise ValueError("Split changed")
 net=build();net.load_state_dict(checkpoint["state_dict"])
 for param in net.parameters():param.requires_grad=False
 for block in [net.features[-2:],net.classifier]:
  for param in block.parameters():param.requires_grad=True
 rows=read_csv(HERE/"data/splits.csv");loaders={}
 # Cache only train/validation images in RAM, never test.
 for split in ["train","val"]:
  ds=Images([r for r in rows if r["split"]==split])
  samples=[ds[i] for i in range(len(ds))]
  loaders[split]=DataLoader(TensorDataset(torch.stack([x for x,y in samples]),torch.tensor([y for x,y in samples])),batch_size=12,shuffle=split=="train")
 counts=torch.bincount(loaders["train"].dataset.tensors[1],minlength=4).float()
 loss_fn=torch.nn.CrossEntropyLoss(weight=counts.sum()/(4*counts))
 opt=torch.optim.AdamW([p for p in net.parameters() if p.requires_grad],lr=.0001,weight_decay=.01)
 # Preserve starting checkpoint if no validation improvement.
 torch.save(checkpoint,out/"best.pt");best=checkpoint["val_macro_f1"];history=[];start=time.time()
 for epoch in range(args.epochs):
  net.eval();net.classifier.train() # Keep tiny-corpus batch-normalization statistics fixed.
  loss_total=0
  for x,y in loaders["train"]:
   opt.zero_grad();loss=loss_fn(net(x),y);loss.backward();opt.step();loss_total+=float(loss.detach())*len(y)
  net.eval();truth=[];pred=[]
  with torch.inference_mode():
   for x,y in loaders["val"]:pred.extend(net(x).argmax(1).tolist());truth.extend(y.tolist())
  score=float(f1_score(truth,pred,labels=list(range(4)),average="macro",zero_division=0))
  history.append(dict(epoch=epoch+1,val_macro_f1=score,train_loss=loss_total/len(loaders["train"].dataset)))
  if score>best:
   best=score
   torch.save(dict(state_dict=net.state_dict(),classes=CLASSES,architecture="mobilenet_v3_small",input_size=224,seed=2026,epoch=epoch+1,val_macro_f1=score,split_sha256=fingerprint,
    training="Last two MobileNet visual blocks + classification head; fixed batchnorm statistics",initialized_from=args.from_run),out/"best.pt")
  print(f"epoch {epoch+1}: val macro-F1={score:.3f}; best={best:.3f}",flush=True)
 (out/"training.json").write_text(json.dumps(dict(args=vars(args),history=history,seconds=time.time()-start,best_val_macro_f1=best),indent=2))
if __name__=="__main__":main()
