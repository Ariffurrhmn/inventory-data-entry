"""Regression checks for Windows UTF-8 annotation export and preservation."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import reference_annotations as annotations

class AnnotationEncodingTests(unittest.TestCase):
 def fixture(self,base):
  (base/"ocr_drafts").mkdir()
  (base/"ocr_drafts/sample.json").write_text(json.dumps({"full_text":"OCR draft","prepared_image_sha256":"prepared"}),encoding="utf-8")
  text="Interior \u2022 Exterior \u20b9 12 \u2014 \u00e9"
  (base/"review_actions.json").write_text(json.dumps({"1":{"text":text}},ensure_ascii=False),encoding="utf-8")
  return text
 def test_export_survives_cp1252_system_default(self):
  with tempfile.TemporaryDirectory() as directory:
   base=Path(directory)/"source";base.mkdir();expected=self.fixture(base);output=Path(directory)/"version"
   row=dict(sample_id="sample",source_path="source.jpg",sha256="source",image_path="data/sample.jpg",label="receipt",split="train")
   original_read=Path.read_text
   def windows_read(path,*args,**kwargs):
    if not args and "encoding" not in kwargs:kwargs["encoding"]="cp1252"
    return original_read(path,*args,**kwargs)
   before=(base/"review_actions.json").read_bytes()
   with patch.object(annotations,"BASE",base),patch.object(annotations,"ROWS",[row]),patch.object(Path,"read_text",windows_read):annotations.export(output)
   result=json.loads((output/"transcriptions/sample.json").read_text(encoding="utf-8"))
   self.assertEqual(result["transcription"]["full_text"],expected)
   self.assertEqual(result["transcription"]["lines"],expected.splitlines())
   self.assertFalse(result["review"]["human_verified"])
   self.assertEqual((base/"review_actions.json").read_bytes(),before)
   self.assertFalse((base/"transcriptions").exists())
 def test_existing_version_is_not_overwritten(self):
  with tempfile.TemporaryDirectory() as directory:
   output=Path(directory)/"version";output.mkdir();sentinel=output/"keep.txt";sentinel.write_text("keep",encoding="utf-8")
   with self.assertRaises(FileExistsError):annotations.export(output)
   self.assertEqual(sentinel.read_text(encoding="utf-8"),"keep")
if __name__=="__main__":unittest.main()
