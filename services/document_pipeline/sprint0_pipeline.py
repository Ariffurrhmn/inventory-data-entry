"""Sprint 0 one-photo pipeline: Tesseract OCR -> classifier hint -> Haiku JSON.

Haiku receives the OCR TEXT ONLY, never the image. Arithmetic/evidence checks run
in code via contract.validate_record (Decimal). Nothing is written to the repo
except files under services/document_pipeline/.runtime/sprint0/.

Run with the classifier runtime (it holds Pillow, pillow-heif, joblib and the
classifier model code) plus the anthropic SDK:

  D:\\DocumentLab\\python-env\\Scripts\\python.exe sprint0_pipeline.py <photo>

The API key is read only from the ANTHROPIC_API_KEY environment variable. If it
is unset the script stops after OCR and the classifier hint and exits with code 2.
Exit codes: 0 success, 1 pipeline error, 2 missing API key.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ENGINE = REPO / "classifier" / "engine"
RUNTIME = HERE / ".runtime" / "sprint0"
MODEL = "claude-haiku-5-5"
sys.path[:0] = [str(HERE), str(ENGINE)]

import gateway  # extraction_prompt, strict_json (reused, not re-implemented)
from contract import validate_record
from text_common import ocr_image

log = logging.getLogger("sprint0")


def setup_logging():
    RUNTIME.mkdir(parents=True, exist_ok=True)
    handlers = [logging.StreamHandler(sys.stderr),
                logging.FileHandler(RUNTIME / "sprint0_run.log", encoding="utf-8")]
    logging.basicConfig(level=logging.INFO, handlers=handlers,
                        format="%(asctime)s %(levelname)s %(message)s")


def enable_heic():
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except Exception as exc:  # HEIC support is optional for JPEG/PNG photos
        log.warning("HEIC opener unavailable (%s); JPEG/PNG only", exc)


def ocr_and_classify(photo):
    """Same image path the gateway uses: Predictor.predict_image (saved OCR policy,
    heading rules). Returns (ocr_text, label_or_None, classifier_error_or_None).

    A classifier failure is logged and the run continues without the hint. OCR
    failures are not caught here and stop the run.
    """
    from inference import Predictor
    try:
        predictor = Predictor()
    except Exception as exc:
        log.exception("classifier load error, continuing without hint: %s", exc)
        return ocr_image(photo), None, f"{type(exc).__name__}: {exc}"
    try:
        result = predictor.predict_image(photo)
        return result["ocr_text"], result["label"], None
    except Exception as exc:
        log.exception("classifier error, continuing without hint: %s", exc)
        return predictor.extract(photo), None, f"{type(exc).__name__}: {exc}"


def call_haiku(ocr_text, hint):
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        log.error("STOP: ANTHROPIC_API_KEY is not set in this environment. "
                  "Sprint 0 Tasks 3 and 6 stop here (no key, no Haiku call).")
        sys.exit(2)
    import anthropic  # official SDK, per project rule for Python code

    label = hint or "none"
    prompt = gateway.extraction_prompt({"label": label, "ocr_text": ocr_text})
    if hint is None:
        prompt += ("\nNo classifier hint is available. Choose document_type from the four "
                   "allowed classes using the OCR text only, and list that choice as an "
                   "uncertainty.")
    client = anthropic.Anthropic(api_key=key)
    message = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )
    if message.stop_reason != "end_turn":
        raise RuntimeError(f"Haiku stopped with stop_reason={message.stop_reason}")
    raw = "".join(block.text for block in message.content if block.type == "text")
    (RUNTIME / "haiku_raw.txt").write_text(raw, encoding="utf-8")
    return raw


def main():
    parser = argparse.ArgumentParser(description="Sprint 0 one-photo JSON pipeline")
    parser.add_argument("photo", type=Path)
    args = parser.parse_args()
    setup_logging()
    enable_heic()
    stem = args.photo.stem

    log.info("OCR + classifier start: %s", args.photo)
    ocr_text, hint, hint_error = ocr_and_classify(args.photo)
    (RUNTIME / f"{stem}_ocr.txt").write_text(ocr_text, encoding="utf-8")
    log.info("OCR done: %d characters -> %s_ocr.txt", len(ocr_text), stem)
    log.info("classifier hint: %s (error: %s)", hint, hint_error)

    raw = call_haiku(ocr_text, hint)
    record = gateway.strict_json(raw)
    report = validate_record(record, ocr_text)
    out = {"source_photo": str(args.photo), "model": MODEL,
           "classifier_hint": hint, "classifier_error": hint_error,
           "record": record, "verification": report}
    (RUNTIME / f"{stem}_result.json").write_text(json.dumps(out, indent=2, ensure_ascii=False),
                                                 encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        log.exception("pipeline failed: %s", exc)
        sys.exit(1)
