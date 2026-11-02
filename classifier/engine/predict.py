"""Classify a single image; supports HEIC; score is not a calibrated probability."""
import argparse,json,time
from pathlib import Path
import torch
from pillow_heif import register_heif_opener
from model import build,preprocess,load_image,CLASSES
from prepare import HERE
register_heif_opener()
def main():
 p=argparse.ArgumentParser();p.add_argument("image",type=Path);p.add_argument("--run",default="baseline");args=p.parse_args()
 torch.set_num_threads(4);checkpoint=torch.load(HERE/"runs"/args.run/"best.pt",map_location="cpu",weights_only=True)
 if checkpoint["classes"]!=CLASSES:raise ValueError("Unexpected class order")
 net=build();net.load_state_dict(checkpoint["state_dict"]);net.eval()
 x=preprocess()(load_image(args.image)).unsqueeze(0)
 with torch.inference_mode():prob=net(x).softmax(1)[0];k=int(prob.argmax())
 print(json.dumps(dict(document_type=CLASSES[k],score=float(prob[k]),scores=dict(zip(CLASSES,prob.tolist())),score_calibrated=False),indent=2))
if __name__=="__main__":main()
