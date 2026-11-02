"""Checks for leakage barriers, metric arithmetic and inference input handling."""
import unittest
from text_common import clean_text,score_text,edit_distance,group_guard
from run_text_experiment import pipeline
class TextWorkflowTests(unittest.TestCase):
 def test_edit_distance_counts_insert_delete_substitute(self):
  self.assertEqual(edit_distance("kitten","sitting"),3)
  self.assertEqual(edit_distance("","abc"),3)
  self.assertEqual(edit_distance(["one","two"],["one","three","four"]),2)
 def test_normalization_is_shared_and_removes_bracket_spans(self):
  self.assertEqual(clean_text("A [signature]\n ₹ １２\tB"),"A ₹ 12 B")
  self.assertEqual(score_text("ABC\n１２"),"abc 12")
 def test_heldout_merchant_never_enters_training(self):
  old=[dict(sample_id="old",sha256="oldhash",group_id="supplier",split="test")]
  extra=[dict(sample_id="new",source="expressexpense_srd",source_sha256="newhash",merchant_review_key="Example Cafe")]
  result=group_guard(old,extra,{"old":"EXAMPLE CAFE receipt"})
  self.assertFalse(result[0]["experiment_include"])
  self.assertEqual(result[0]["experiment_split"],"excluded_guard")
 def test_exact_duplicate_is_excluded_even_if_training(self):
  old=[dict(sample_id="old",sha256="same",group_id="supplier",split="train")]
  extra=[dict(sample_id="new",source="company_documents_v2",source_sha256="same")]
  self.assertFalse(group_guard(old,extra,{"old":"text"})[0]["experiment_include"])
 def test_feature_fit_does_not_learn_validation_vocabulary(self):
  model=pipeline()
  model.fit(["purchase order buyer","cash receipt paid","delivery note shipped","customer copy duplicate"],["purchase_order","receipt","delivery_note","customer_copy"])
  before=set(model.named_steps["features"].transformer_list[0][1].vocabulary_)
  model.predict(["unseenvalidationtoken"])
  after=set(model.named_steps["features"].transformer_list[0][1].vocabulary_)
  self.assertEqual(before,after)
  self.assertNotIn("unseenvalidationtoken",after)
if __name__=="__main__":unittest.main()
