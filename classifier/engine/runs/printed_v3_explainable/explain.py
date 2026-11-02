"""Faithful decision trace and model-score perturbations; no generated rationales."""
import math,re
import numpy as np
from text_common import clean_text

def exact_linear_evidence(model,cleaned,target_label):
 steps=getattr(model,'named_steps',{})
 if 'features' not in steps or 'classifier' not in steps:return None
 features=steps['features'];clf=steps['classifier']
 if not hasattr(features,'get_feature_names_out'):return None
 if hasattr(clf,'coef_') and clf.coef_.shape[0]==len(clf.classes_):
  weights=clf.coef_;intercept=clf.intercept_;decision=np.asarray(model.decision_function([cleaned]))[0]
 elif clf.__class__.__name__=='ComplementNB' and len(clf.classes_)>1:
  weights=clf.feature_log_prob_;intercept=np.zeros(len(clf.classes_));decision=np.asarray(model.predict_log_proba([cleaned]))[0]
 else:return None
 classes=list(map(str,clf.classes_));target=classes.index(target_label)
 x=features.transform([cleaned]).tocsr()
 alternative=max((i for i in range(len(classes)) if i!=target),key=lambda i:decision[i])
 delta=weights[target]-weights[alternative];bias=float(intercept[target]-intercept[alternative])
 names=features.get_feature_names_out();row=x.getrow(0);contrib=row.data*delta[row.indices]
 margin=float(decision[target]-decision[alternative]);reconstructed=float(contrib.sum()+bias)
 if not np.isclose(margin,reconstructed,atol=1e-6):raise ValueError('Linear explanation failed margin reconstruction')
 terms=[dict(feature=str(names[i]),contribution=float(c),feature_value=float(v)) for i,c,v in zip(row.indices,contrib,row.data)]
 return dict(method='exact_ngram_log_score_contributions',component='learned_fallback_only',alternative_class=classes[alternative],logit_margin=margin,intercept_contribution=bias,sum_feature_contributions=float(contrib.sum()),reconstructed_logit_margin=reconstructed,reconstruction_error=abs(margin-reconstructed),supporting_features=sorted([t for t in terms if t['contribution']>0],key=lambda t:t['contribution'],reverse=True)[:12],opposing_features=sorted([t for t in terms if t['contribution']<0],key=lambda t:t['contribution'])[:6],active_feature_count=len(terms),interpretation='Feature value times the learned coefficient difference exactly reconstructs the target-versus-alternative logit margin, including the intercept. Contributions are not probability percentages.',limitations=['Correlated word/character n-grams can share evidence.','A learned association is not proof of document type or real-world causation.','This explains the learned fallback only; any heading rules are held fixed.'])

def explain_prediction(predictor,text,heading_text=None,max_blocks=24,result=None):
 result=result or predictor.predict_text(text,heading_text=heading_text)
 trace=dict(label=result['label'],decision_source=result['decision_source'],model_run=result.get('run'),scores_calibrated=False)
 if result['decision_source'] in ['printed_heading','document_intent_rule']:
  from inference import heading_for_selection
  cue=heading_for_selection(getattr(predictor,'selection',{}),heading_text if heading_text is not None else text)
  trace.update(method='deterministic_rule_trace' if result['decision_source']=='document_intent_rule' else 'deterministic_heading_trace',rule=cue.get('rule'),normalized_matched_text=cue['evidence'],matched_classes=cue['matches'],ambiguous=False,learned_fallback_label=result['statistical_label'],reason='The unique matched printed-text rule selected the class. The learned model did not determine the final label.',limitations=['This explains the decision rule, not whether OCR correctly read the source image.','Heading evidence may come from separate page-region OCR.'])
  return trace
 cleaned=clean_text(text)
 linear=exact_linear_evidence(predictor.model,cleaned,result['label'])
 if linear is not None:
  trace.update(linear);return trace
 words=list(re.finditer(r'\S+',cleaned))
 if len(words)<2:
  trace.update(method='token_block_occlusion',available=False,reason='At least two readable tokens are needed for a useful omission comparison.');return trace
 classes=list(map(str,predictor.model.classes_));base=np.array([result['scores'][c] for c in classes])
 target=classes.index(result['label']);rank=np.argsort(base)[::-1];alternative=int(next(i for i in rank if i!=target))
 width=max(1,math.ceil(len(words)/max_blocks));blocks=[];perturbed=[]
 for start in range(0,len(words),width):
  stop=min(start+width,len(words));a=words[start].start();b=words[stop-1].end()
  remaining=clean_text(cleaned[:a]+' '+cleaned[b:])
  if not remaining:continue
  blocks.append(dict(start=a,end=b,text=cleaned[a:b],removed_tokens=stop-start))
  perturbed.append(remaining)
 # The model is fixed: never train or fit an explainer on this document.
 scores=predictor.model.predict_proba(perturbed)
 effects=[]
 margin=float(base[target]-base[alternative])
 for block,row in zip(blocks,scores):
  effect=dict(block,target_score_drop=float(base[target]-row[target]),target_vs_alternative_margin_drop=float(margin-(row[target]-row[alternative])),label_without_block=classes[int(np.argmax(row))],label_changed_without_block=classes[int(np.argmax(row))]!=result['label'])
  effects.append(effect)
 trace.update(method='token_block_occlusion',available=True,component='learned_fallback_only',target_score=float(base[target]),alternative_class=classes[alternative],alternative_score=float(base[alternative]),score_margin=margin,ambiguous_heading=bool(result.get('ambiguous_heading')),input_tokens=len(words),blocks_evaluated=len(effects),supporting_blocks=sorted([e for e in effects if e['target_score_drop']>1e-8],key=lambda e:e['target_score_drop'],reverse=True)[:6],opposing_blocks=sorted([e for e in effects if e['target_score_drop']< -1e-8],key=lambda e:e['target_score_drop'])[:3],all_effects=effects,interpretation='A positive score drop means omitting this block lowered the fixed model score for the reported class. Scores are model preferences, not calibrated confidence.',limitations=['Omission measures sensitivity of this model on this input, not real-world causation or ground truth.','Blocks can interact; effects do not sum to the prediction.','Deletion can create unnatural inputs and alter which tokens fit the encoder window.','For conflicting headings, these omissions explain only the learned fallback; heading rules are held fixed.'])
 return trace

def main():
 import argparse,json
 from pathlib import Path
 from inference import Predictor
 parser=argparse.ArgumentParser();parser.add_argument('--text-file',required=True);parser.add_argument('--heading-file');parser.add_argument('--run');parser.add_argument('--output');args=parser.parse_args()
 text=Path(args.text_file).read_text(encoding='utf-8-sig');context=Path(args.heading_file).read_text(encoding='utf-8-sig') if args.heading_file else None
 explanation=explain_prediction(Predictor(args.run),text,heading_text=context)
 raw=json.dumps(explanation,ensure_ascii=False,indent=2)
 if args.output:Path(args.output).write_text(raw,encoding='utf8')
 else:print(raw)
if __name__=='__main__':main()

