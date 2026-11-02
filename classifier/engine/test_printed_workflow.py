"""Checks for printed development isolation, heading ambiguity and inference failure."""
import unittest
from train_printed import development_split
from heading_rules import heading_decision
from inference import Predictor
class PrintedWorkflowTests(unittest.TestCase):
 def test_related_bridge_development_forms_stay_together_and_test_is_unused(self):
  rows=[dict(sample_id='train_'+label,label=label,split='train',group_id='train:'+label) for label in ['purchase_order','receipt','delivery_note','customer_copy']]
  rows += [dict(sample_id='val_'+label,label=label,split='val',group_id='val:'+label) for label in ['purchase_order','receipt','customer_copy']]
  rows += [dict(sample_id='bridge_dn',label='delivery_note',split='train',group_id='dn:bridge-printed'),dict(sample_id='old_test',label='purchase_order',split='test',group_id='po:bridge-printed-table')]
  split=development_split(rows);lookup={r['sample_id']:r for r in split}
  self.assertEqual(lookup['bridge_dn']['split'],'val');self.assertEqual(lookup['old_test']['split'],'test')
  self.assertEqual(lookup['bridge_dn']['development_group'],lookup['old_test']['development_group'])
  self.assertEqual(lookup['bridge_dn']['historical_split'],'train')
 def test_titles_and_split_lines(self):
  self.assertEqual(heading_decision('ABC\nPurchase Order\nBuyer Example')['label'],'purchase_order')
  self.assertEqual(heading_decision('Packing\nSlip\nItem Qty')['label'],'delivery_note')
  self.assertEqual(heading_decision('CARD TERMINAL\nCustomer Receipt Copy')['label'],'customer_copy')
 def test_copy_order_hybrid_has_no_invented_precedence(self):
  decision=heading_decision('Purchase Order\nCUSTOMER COPY')
  self.assertIsNone(decision['label']);self.assertTrue(decision['ambiguous'])
 def test_retail_order_number_is_not_purchase_order_heading(self):
  self.assertIsNone(heading_decision('Order #12\nTotal 7.50\nCash 10.00')['label'])
 def test_edge_heading_does_not_become_statistical_training_features(self):
  import numpy as np
  from text_common import CLASSES
  class FakeModel:
   classes_=np.array(CLASSES)
   def predict_proba(self,texts):
    self.seen=texts
    return np.array([[.1,.7,.1,.1]])
  predictor=Predictor.__new__(Predictor);predictor.model=FakeModel();predictor.heading_rules=True
  predictor.selection={'new_test_result':None};predictor.metadata=lambda:dict(experimental=True)
  result=predictor.predict_text('Cash paid',heading_text='Cash paid\nCUSTOMER COPY')
  self.assertEqual(predictor.model.seen,['Cash paid'])
  self.assertEqual(result['label'],'customer_copy');self.assertEqual(result['statistical_label'],'receipt')
  self.assertEqual(result['decision_source'],'printed_heading');self.assertFalse(result['scores_calibrated'])
 def test_empty_ocr_does_not_produce_a_fabricated_label(self):
  predictor=Predictor.__new__(Predictor)
  with self.assertRaises(ValueError):predictor.predict_text(' [signature] ')
if __name__=='__main__':unittest.main()
