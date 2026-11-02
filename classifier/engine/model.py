"""Image-only four-class MobileNetV3 classifier; full page retained with letterboxing."""
import torch
from PIL import Image,ImageOps
from torchvision import models,transforms
CLASSES=["purchase_order","receipt","delivery_note","customer_copy"]
class Letterbox:
 def __init__(self,size=224): self.size=size
 def __call__(self,image): return ImageOps.pad(image,(self.size,self.size),method=Image.Resampling.LANCZOS,color="white")
def preprocess(augment=False):
 ops=[Letterbox()]
 if augment: ops += [transforms.RandomRotation(4,fill=255),transforms.ColorJitter(brightness=.15,contrast=.15)]
 return transforms.Compose(ops+[transforms.ToTensor(),transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
def build(pretrained=False):
 net=models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None)
 net.classifier[-1]=torch.nn.Linear(net.classifier[-1].in_features,len(CLASSES))
 return net
def load_image(path):
 with Image.open(path) as im: return ImageOps.exif_transpose(im).convert("RGB")
