"""Replay actual sub-agent responses through the real classifier and persistent gateway."""
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from gateway import Store
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "classifier/engine"))
from inference import Predictor

def run():
    experiment = HERE / "experiments/2026-10-24"
    inputs = json.loads((experiment / "inputs/ocr-only.json").read_text(encoding="utf-8-sig"))
    report = {"scope": "Actual saved sub-agent JSON through current live classifier/gateway; development evidence",
              "accuracy_measured": False, "automatic_llm_available": False, "results": []}
    with tempfile.TemporaryDirectory(prefix="handoff-replay-") as folder:
        store = Store(Path(folder) / "submissions.sqlite3", Predictor())
        for approach in ["direct", "strict"]:
            output_path = experiment / ("outputs/" + approach + "-agent-response.json")
            records = json.loads(output_path.read_text(encoding="utf-8-sig"))
            for original in inputs:
                submission, replay = store.submit(approach + "-" + original["id"], {"text": original["ocr_text"]})
                assert not replay and submission["state"] == "awaiting_extraction"
                final = store.attach(submission["submission_id"], records[original["id"]])
                consumer = store.consumer(submission["submission_id"])
                assert final["state"] == "completed"
                assert consumer["status"] == "blocked_for_review" and not consumer["inventory_updated"]
                same = store.attach(submission["submission_id"], records[original["id"]])
                assert same == final
                report["results"].append({"approach": approach, "sample_id": original["id"],
                    "ocr_sha256": hashlib.sha256(original["ocr_text"].encode()).hexdigest(),
                    "response_file_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
                    "state": final["state"], "classification": final["classification"]["label"],
                    "verification": final["verification"], "consumer": consumer,
                    "identical_extraction_replay": True})
    report["completed"] = len(report["results"])
    report["review_required"] = sum(r["verification"]["review_required"] for r in report["results"])
    report["passed"] = True
    output = HERE / "validation/2026-10-24/handoff-replay.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k != "results"}, indent=2))

if __name__ == "__main__":
    run()

