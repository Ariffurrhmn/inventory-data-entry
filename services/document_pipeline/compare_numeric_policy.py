"""Diagnostic locale-policy comparison over preserved agent responses; not accuracy."""
import hashlib, json
from pathlib import Path
from contract import validate_record
HERE = Path(__file__).resolve().parent
EXPERIMENT = HERE / "experiments/2026-10-24"

def run():
    sources = {r["id"]:r for r in json.loads((EXPERIMENT/"inputs/ocr-only.json").read_text(encoding="utf-8-sig"))}
    report = {"scope":"Explicit numeric evidence policy comparison; no value mutation; no measured accuracy",
              "gateway_default":"literal", "contract_sha256":hashlib.sha256((HERE/"contract.py").read_bytes()).hexdigest(), "results":{}}
    for approach in ("direct", "evidence"):
        records = json.loads((EXPERIMENT/("outputs/"+approach+"-agent-response.json")).read_text(encoding="utf-8-sig"))
        for policy in ("literal", "grouped_commas"):
            audits = {key:validate_record(record,sources[key]["ocr_text"],numeric_policy=policy) for key,record in records.items()}
            counts = {
                "records":len(audits),
                "schema_valid":len(audits),
                "all_populated_fields_supported":sum(all(f["status"] in {"supported","supported_normalized"} for f in a["evidence_findings"]) for a in audits.values()),
                "review_required":sum(a["review_required"] for a in audits.values()),
                "audited_normalizations":sum(len(a["normalization_findings"]) for a in audits.values()),
                "arithmetic_passed":sum(c["status"]=="passed" for a in audits.values() for c in a["checks"])
            }
            report["results"][approach+"-"+policy]={"counts":counts,"records":audits}
    (HERE/"validation/2026-10-24/numeric-policy.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({key:value["counts"] for key,value in report["results"].items()},indent=2))

if __name__ == "__main__":
    run()

