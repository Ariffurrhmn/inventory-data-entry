"""Rule ambiguity, cross-view boundaries, and algebraic explanation controls."""
import unittest,numpy as np
from heading_rules_v3 import heading_decision
from explain import exact_linear_evidence
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import ComplementNB
from sklearn.linear_model import LogisticRegression

class RecoveredWorkflowTests(unittest.TestCase):
 def test_later_ocr_view_gets_its_own_title_window(self):
  text='\n'.join(['unreadable']*40)+'\fPurchase Order\nItems quantities'
  cue=heading_decision(text)
  self.assertEqual(cue['label'],'purchase_order')
  self.assertEqual(cue['rule']['ocr_section_index'],1)
 def test_purchase_intent_requires_all_three_fields(self):
  cue=heading_decision('Order No 42\nRequired By Friday\nPlease supply the following goods')
  self.assertEqual(cue['label'],'purchase_order')
  self.assertEqual(cue['rule']['kind'],'purchase_request_intent')
  self.assertIsNone(heading_decision('Order No42\nDate today\nCash received')['label'])
 def test_ocr_copy_marker_records_correction(self):
  cue=heading_decision('Total 7.50\nuplicate #1')
  self.assertEqual(cue['label'],'customer_copy')
  self.assertEqual(cue['rule']['canonical_term'],'duplicate')
  self.assertEqual(cue['rule']['edit_distance'],1)
 def test_copy_purchase_conflict_remains_unresolved(self):
  cue=heading_decision('Customer Copy\fOrder No:42\nRequired By Friday\nPlease supply goods')
  self.assertTrue(cue['ambiguous']);self.assertIsNone(cue['label'])
 def test_exact_nb_and_logistic_explanations_reconstruct_observed_score_contrast(self):
  texts=['cash paid shop','cash paid retail','purchase goods order','purchase supply order','delivery goods signed','delivery note signed','customer copy card','customer duplicate card']
  y=['receipt','receipt','purchase_order','purchase_order','delivery_note','delivery_note','customer_copy','customer_copy']
  for clf in [ComplementNB(alpha=.1),LogisticRegression(C=1,max_iter=1000)]:
   model=Pipeline([('features',TfidfVectorizer(ngram_range=(1,2))),('classifier',clf)]).fit(texts,y)
   target=model.predict(['cash paid shop'])[0]
   e=exact_linear_evidence(model,'cash paid shop',target)
   logp=model.predict_log_proba(['cash paid shop'])[0];classes=list(model.classes_)
   actual=logp[classes.index(target)]-logp[classes.index(e['alternative_class'])]
   self.assertAlmostEqual(e['reconstructed_logit_margin'],actual,places=6)
   self.assertLess(e['reconstruction_error'],1e-6)
 def test_image_views_preserve_titles_without_entering_learned_features(self):
  from unittest.mock import patch
  from inference import Predictor
  from text_common import CLASSES
  class Model:
   classes_=np.array(CLASSES)
   def predict_proba(self,texts):
    self.seen=texts;return np.array([[.1,.7,.1,.1]])
  p=Predictor.__new__(Predictor);p.model=Model();p.illumination_recovery=True;p.heading_rules=True
  p.selection={'heading_module':'heading_rules_v3','new_test_result':None};p.metadata=lambda:{}
  views={'full':'Cash paid total','top_0':'Purchase Order'}
  with patch('illumination_ocr.illumination_ocr',return_value=views),patch('inference.sparse_ocr',return_value='\n'.join(['noise']*40)),patch('edge_ocr.edge_ocr',return_value=''):
   result=p.predict_image('unused.jpg')
  self.assertEqual(result['label'],'purchase_order')
  self.assertEqual(p.model.seen,['Cash paid total'])
  self.assertEqual(result['decision_trace']['rule']['ocr_section_index'],3)
if __name__=='__main__':unittest.main()

