"""Known-model controls for faithful explanations, independent of learned artifacts."""
import unittest
import numpy as np
from explain import explain_prediction

class ControlledModel:
 classes_=np.array(['customer_copy','delivery_note','purchase_order','receipt'])
 def predict_proba(self,texts):
  return np.array([[.05,.05,.05,.85] if 'paid' in t.split() else [.25,.25,.25,.25] for t in texts])
class ControlledPredictor:
 model=ControlledModel()
 def predict_text(self,text,heading_text=None):
  scores=self.model.predict_proba([text])[0]
  return dict(label='receipt',decision_source='trained_classifier',scores=dict(zip(self.model.classes_,map(float,scores))),run='control',ambiguous_heading=False)
class ExplanationTests(unittest.TestCase):
 def test_positive_attribution_agrees_with_manual_fixed_model_omission(self):
  p=ControlledPredictor();text='cash paid total'
  e=explain_prediction(p,text,max_blocks=3)
  block=next(b for b in e['all_effects'] if b['text']=='paid')
  expected=p.model.predict_proba([text])[0,3]-p.model.predict_proba(['cash total'])[0,3]
  self.assertAlmostEqual(block['target_score_drop'],expected)
  self.assertTrue(block['label_changed_without_block']);self.assertEqual(e['supporting_blocks'][0]['text'],'paid')
 def test_heading_trace_does_not_invent_model_attribution(self):
  p=ControlledPredictor()
  result=dict(label='purchase_order',decision_source='printed_heading',statistical_label='receipt',run='control')
  e=explain_prediction(p,'Purchase Order',result=result)
  self.assertEqual(e['normalized_matched_text'],'Purchase Order')
  self.assertEqual(e['method'],'deterministic_heading_trace')
  self.assertNotIn('supporting_blocks',e)
 def test_explanation_preserves_model_prediction_and_input(self):
  p=ControlledPredictor();text='cash paid total';before=p.model.predict_proba([text]).copy()
  explain_prediction(p,text,max_blocks=2)
  np.testing.assert_array_equal(before,p.model.predict_proba([text]))
  self.assertEqual(text,'cash paid total')
if __name__=='__main__':unittest.main()

