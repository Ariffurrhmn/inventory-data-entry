"""Local ruled-table OCR audit for a new document; never overwrites output."""
import argparse
from pathlib import Path
from localization import analyze
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('image',type=Path)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--tessdata',type=Path,default=ROOT/'classifier/engine/.cache/tessdata')
args=parser.parse_args()
result=analyze(args.image,args.output,args.tessdata)
for c in result['candidates']:
    print(c['method'],len(c['layout']['tables']),'grids')
    print(c.get('ocr',{}).get('ocr_text',c.get('failure','')))
