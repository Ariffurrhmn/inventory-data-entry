from pathlib import Path
p=Path('classifier/docs/organize.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace('assert not mismatches,mismatches', "assert not [x for x in mismatches if Path(x).name.casefold()!='desktop.ini'],mismatches")
s=s.replace('pre_scan_all_hashes_match=True','pre_scan_data_and_code_hashes_match=True,windows_folder_metadata_differences=mismatches')
s=s.replace("rows={r['sample_id']:r for r in csv.DictReader((engine/'runs/printed_v3_explainable/split_manifest.csv').open(encoding='utf8'))}","rows={r['sample_id']:r for r in csv.DictReader((engine/'runs/printed_v3_explainable/split_manifest.csv').open(encoding='utf8'))}\noriginals={r['sample_id']:r for r in csv.DictReader((engine/'data/manifest.csv').open(encoding='utf8'))}")
s=s.replace("row.get('source_path','')","originals.get(sid,{}).get('source_path',row.get('source_path',''))")
p.write_text(s,encoding='utf8')
p=Path('classifier/app/assets/app.js');s=p.read_text(encoding='utf-8-sig');s=s.replace("function controls(){","function controls(){$('status').classList.toggle('busy',state.busy);");p.write_text(s,encoding='utf8')
p=Path('classifier/app/assets/style.css');s=p.read_text(encoding='utf-8-sig');s=s.replace("@import url('data:text/css,');\n",'');p.write_text(s,encoding='utf8')

