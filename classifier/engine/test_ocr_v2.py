"""Checks for versioned OCR-combination behavior."""
import unittest
from ocr_v2 import combine_outputs,SPARSE_POLICY
class OCRRecoveryTests(unittest.TestCase):
 def test_deduplicate_lines_without_discarding_other_passes(self):
  self.assertEqual(combine_outputs("Delivery Challan\nA B\n","delivery challan\nC D\n"),"Delivery Challan\nA B\nC D")
 def test_empty_pass_preserves_the_other(self):
  self.assertEqual(combine_outputs(""," CUSTOMER COPY\n "),"CUSTOMER COPY")
  self.assertEqual(combine_outputs("receipt\n",""),"receipt")
 def test_policy_is_separate_from_legacy(self):
  from text_common import OCR_POLICY
  self.assertEqual(OCR_POLICY["psm"],3)
  self.assertEqual(SPARSE_POLICY["psm"],11)
if __name__=="__main__":unittest.main()
