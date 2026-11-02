"""Reproducible live development smoke; no historical test/annotation inputs."""
import base64, hashlib, json, sys, tempfile, threading, time, urllib.error, urllib.request
from pathlib import Path
from gateway import make_server
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def run():
    manifest = json.loads((ROOT / "classifier/demo/manifest.json").read_text(encoding="utf-8-sig"))
    out = HERE / "validation/2026-10-24"
    out.mkdir(parents=True, exist_ok=True)
    report = {"scope": "Live development smoke, no recognition accuracy claim", "results": [],
              "historical_test_inputs_opened": False, "paid_api_calls": 0}
    with tempfile.TemporaryDirectory(prefix="pipeline-smoke-") as folder:
        server = make_server(0, Path(folder) / "test.sqlite3")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = "http://127.0.0.1:" + str(server.server_port)
        def req(path, data=None, key=None):
            headers = {"Authorization": "Bearer " + server.token, "Content-Type": "application/json"}
            if key: headers["Idempotency-Key"] = key
            request = urllib.request.Request(base + path, data=None if data is None else json.dumps(data).encode(), headers=headers)
            try:
                with urllib.request.urlopen(request, timeout=240) as response:
                    return response.status, json.load(response)
            except urllib.error.HTTPError as error:
                return error.code, json.load(error)
        try:
            # All four predicted document routes plus known classifier failure.
            for item in manifest:
                record_path = ROOT / "classifier" / item["record"]
                saved = json.loads(record_path.read_text(encoding="utf-8-sig"))
                payload = {"text": saved["result"]["ocr_text"]}
                start = time.perf_counter()
                status, response = req("/api/submissions", payload, "text-" + item["id"])
                submission = response["result"]
                assert status == 201 and submission["state"] == "awaiting_extraction", response
                replay_code, replay = req("/api/submissions", payload, "text-" + item["id"])
                assert replay_code == 200 and replay["replayed"] and replay["result"]["submission_id"] == submission["submission_id"]
                conflict, _ = req("/api/submissions", {"text": payload["text"] + " changed"}, "text-" + item["id"])
                assert conflict == 409
                report["results"].append({"id": item["id"], "mode": "recorded_OCR_live_classification",
                    "input_sha256": hashlib.sha256(payload["text"].encode()).hexdigest(),
                    "prediction": submission["classification"]["label"], "expected_existing_development_label": item["expected_label"],
                    "recorded_prediction": saved["result"]["label"], "submission_state": submission["state"],
                    "same_key_replayed": True, "changed_payload_conflict": True,
                    "elapsed_seconds": round(time.perf_counter()-start, 3)})
                (out / ("text-" + item["id"] + ".json")).write_text(json.dumps(submission, indent=2), encoding="utf-8")
                print("Text smoke:", item["id"], submission["classification"]["label"], flush=True)
            # Two actual image uploads; no saved OCR reused by this path.
            for item in [manifest[0], manifest[2]]:
                image = ROOT / "classifier" / item["image"]
                raw = image.read_bytes()
                payload = {"filename": image.name, "image_base64": base64.b64encode(raw).decode()}
                start = time.perf_counter()
                status, response = req("/api/submissions", payload, "image-" + item["id"])
                submission = response["result"]
                assert status == 201 and submission["state"] == "awaiting_extraction", response
                report["results"].append({"id": item["id"], "mode": "live_image_OCR_classification",
                    "source_sha256": hashlib.sha256(raw).hexdigest(), "prediction": submission["classification"]["label"],
                    "expected_existing_development_label": item["expected_label"],
                    "ocr_characters": len(submission["classification"]["ocr_text"]),
                    "elapsed_seconds": round(time.perf_counter()-start, 3), "submission_state": submission["state"]})
                (out / ("image-" + item["id"] + ".json")).write_text(json.dumps(submission, indent=2), encoding="utf-8")
                print("Image smoke:", item["id"], report["results"][-1], flush=True)
            code, bad = req("/api/submissions", {"filename": "bad.jpg", "image_base64": base64.b64encode(b"not an image").decode()}, "bad-image")
            assert code == 201 and bad["result"]["state"] == "failed"
            report["invalid_image_failure_persisted"] = True
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
    report["passed"] = True
    (out / "live-smoke.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)

if __name__ == "__main__":
    run()

