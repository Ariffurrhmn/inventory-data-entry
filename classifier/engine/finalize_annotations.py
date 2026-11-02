"""Validate and package the existing, reviewed annotations; never runs OCR or training."""
import argparse, csv, hashlib, html, json, os, re
from collections import Counter
from pathlib import Path
from reference_annotations import BASE, ROOT, ROWS

def main(base=BASE):
    base=Path(base).resolve()
    records=[]
    expected={r["sample_id"] for r in ROWS}
    actual={p.stem for p in (base/"transcriptions").glob("*.json")}
    assert actual==expected, "Transcription IDs differ from the frozen split manifest"
    actions_path=base/"review_actions.json"
    if not actions_path.exists():actions_path=BASE/"review_actions.json"
    actions=json.loads(actions_path.read_text(encoding="utf-8"))
    assert set(actions)=={str(i) for i in range(1,len(ROWS)+1)}
    queue=[]
    for n,row in enumerate(ROWS,1):
        record=json.loads((base/"transcriptions"/(row["sample_id"]+".json")).read_text(encoding="utf-8"))
        assert record["sample_id"]==row["sample_id"]
        assert record["classification"]==dict(label=row["label"],split=row["split"])
        assert record["source_image"]==dict(path=row["source_path"],sha256=row["sha256"])
        assert record["review"]["status"]=="assistant_visual_reviewed"
        assert record["review"]["human_verified"] is False
        text=record["transcription"]["full_text"]
        assert isinstance(text,str) and text.strip(), f"Empty transcription: {n}"
        assert "\ufffd" not in text, f"Replacement character in transcription: {n}"
        assert record["transcription"]["lines"]==text.splitlines()
        prepared=ROOT/record["prepared_image"]["path"]
        assert hashlib.sha256(prepared.read_bytes()).hexdigest()==record["prepared_image"]["sha256"], f"Prepared image changed: {n}"
        assert (ROOT/row["source_path"]).is_file(), f"Missing original: {n}"
        assert (ROOT/record["provenance"]["ocr_draft"]).is_file()
        records.append(record)
        markers=sorted(set(re.findall(r"\[[^\]\n]+\]",text)))
        uncertainties=record["review"]["uncertainties"]
        if uncertainties or any(m!="[signature]" for m in markers):
            queue.append(dict(number=n,sample_id=row["sample_id"],source_path=row["source_path"],markers=" | ".join(markers),uncertainties=" | ".join(uncertainties),transcription="transcriptions/"+row["sample_id"]+".json"))
    with (base/"transcriptions.jsonl").open("w",encoding="utf-8") as f:
        for record in records:f.write(json.dumps(record,ensure_ascii=False)+"\n")
    with (base/"review_queue.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=["number","sample_id","source_path","markers","uncertainties","transcription"])
        writer.writeheader();writer.writerows(queue)
    report=dict(date="2026-10-19",expected_images=len(ROWS),transcription_files=len(records),
        assistant_visual_reviewed=len(records),human_verified=0,unreviewed=0,
        classes=dict(Counter(r["classification"]["label"] for r in records)),
        splits=dict(Counter(r["classification"]["split"] for r in records)),
        records_with_explicit_uncertainties=sum(bool(r["review"]["uncertainties"]) for r in records),
        review_queue_records=len(queue),
        prepared_image_hashes_checked=len(records),
        source_paths_and_manifest_hashes_matched=len(records),
        original_file_hashes_recomputed=False,
        checks=["Unique exact manifest coverage","Nonempty UTF-8 text without replacement characters","Label and split match","Source path and recorded hash match manifest","Prepared image SHA-256 match","Original and OCR draft files exist","Consistent text/lines","All review actions present"],
        limitations=["Assistant visual review is not independent human verification.","Tables are linearized; geometry in OCR drafts is unreviewed.","Uncertainty spans and best readings need audit before exact-character benchmark scoring.","Original file hashes were matched to the existing manifest, not recomputed."])
    (base/"validation_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    cards=[]
    for n,r in enumerate(records,1):
        sid=r["sample_id"];label=r["classification"]["label"];split=r["classification"]["split"]
        esc=html.escape
        notes="; ".join(r["review"]["uncertainties"])
        image_src=Path(os.path.relpath(ROOT/r["prepared_image"]["path"],base)).as_posix()
        cards.append(f'<article data-class="{label}"><h2>{n}. {esc(sid)} · {label} · {split}</h2><p>{esc(r["source_image"]["path"])}</p><a href="transcriptions/{sid}.json">JSON record</a><p class="notes">{esc(notes)}</p><div class="pair"><img loading="lazy" alt="Source document {n}" src="{esc(image_src,quote=True)}"><pre>{esc(r["transcription"]["full_text"])}</pre></div></article>')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Document transcription references</title>
<style>body{font:16px system-ui;margin:24px;background:#f3f4f6;color:#17202a}header{background:white;padding:20px;border-radius:8px}article{background:white;padding:20px;margin:24px 0;border-radius:8px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:24px}.pair img{width:100%;height:auto}.pair pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.6 monospace;margin:0}.notes{color:#80520c}h2{font-size:19px}@media(max-width:800px){.pair{grid-template-columns:1fr}}select{font-size:16px}</style>
<header><h1>140 document transcription references</h1><p>OCR-assisted, individually visually reviewed by Codex. Human verified: 0. Markers and uncertain readings need audit before benchmark use. All text is displayed exactly as stored; tables are linearized.</p><label>Show class: <select id="filter"><option value="">All classes</option><option>purchase_order</option><option>receipt</option><option>delivery_note</option><option>customer_copy</option></select></label></header>'''
    page+="".join(cards)
    page+='<script>document.getElementById("filter").addEventListener("change",function(){document.querySelectorAll("article").forEach(a=>a.hidden=!!this.value&&a.dataset.class!==this.value)})</script></html>'
    (base/"review.html").write_text(page,encoding="utf-8")
    print(json.dumps(report,indent=2))
if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--annotations-dir",type=Path,default=BASE)
    main(parser.parse_args().annotations_dir)
