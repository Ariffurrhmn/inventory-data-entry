"""Four-class prediction using the current active saved model."""
import argparse,json,sys
from pathlib import Path
from inference import Predictor

def main():
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--text-file',type=Path);group.add_argument('--image',type=Path)
    parser.add_argument('--run',default=None);args=parser.parse_args()
    try:
        predictor=Predictor(args.run)
        result=predictor.predict_text(args.text_file.read_text(encoding='utf-8')) if args.text_file else predictor.predict_image(args.image)
        result.pop('ocr_text',None);result.pop('heading_ocr_text',None)
        print(json.dumps(result,ensure_ascii=True,indent=2))
    except (ValueError,OSError,RuntimeError) as exc:
        print(json.dumps(dict(error=str(exc)),ensure_ascii=True));return 1
    return 0
if __name__=='__main__':sys.exit(main())
