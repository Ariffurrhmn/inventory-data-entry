import unittest
from split import make_splits
from model import preprocess
from PIL import Image
class WorkflowTests(unittest.TestCase):
 def rows(self):
  rows=[]
  for label in ["purchase_order","receipt","delivery_note","customer_copy"]:
   for i in range(8):
    rows.append(dict(label=label,include="yes",label_status="reviewed",group_id=f"{label}:{i}",sha256=f"{label}:{i}",source="curated"))
   for i in range(2):
    rows.append(dict(label=label,include="yes",label_status="reviewed",group_id=f"photo:{label}",sha256=f"photo:{label}:{i}",source="printed_synthetic_photo"))
  return rows
 def test_group_isolation_and_determinism(self):
  a=make_splits(self.rows());self.assertEqual(a,make_splits(self.rows()))
  for group in {r["group_id"] for r in a}:
   self.assertEqual(len({r["split"] for r in a if r["group_id"]==group}),1)
  self.assertEqual({r["split"] for r in a},{"train","val","test"})
 def test_duplicate_group_conflict_rejected(self):
  rows=self.rows();rows[1]["sha256"]=rows[0]["sha256"]
  with self.assertRaisesRegex(ValueError,"Identical"):make_splits(rows)
 def test_unreviewed_rejected(self):
  rows=self.rows();rows[0]["label_status"]="unverified"
  with self.assertRaisesRegex(ValueError,"Review"):make_splits(rows)
 def test_actual_frozen_splits_have_no_overlap(self):
  from prepare import HERE,read_csv
  rows=read_csv(HERE/"data/splits.csv")
  for field in ["group_id","sha256","source_path"]:
   assignment={}
   for row in rows:
    prior=assignment.setdefault(row[field],row["split"])
    self.assertEqual(prior,row["split"],f"{field} crosses splits: {row[field]}")
  self.assertEqual(len(rows),len({r["sample_id"] for r in rows}))
  self.assertTrue(all(r["label_status"]=="reviewed" for r in rows))
 def test_full_page_preprocessing(self):
  im=Image.new("RGB",(120,800),"black")
  tensor=preprocess()(im)
  self.assertEqual(tuple(tensor.shape),(3,224,224))
  # Tall full page is letterboxed, not centre-cropped.
  self.assertGreater(float(tensor[:,112,0].mean()),1)
if __name__=="__main__":unittest.main()
