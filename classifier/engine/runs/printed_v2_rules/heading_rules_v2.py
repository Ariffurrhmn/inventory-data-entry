"""Versioned explainable document rules with conservative OCR/intent recovery."""
import re,unicodedata
from heading_rules import heading_decision as original
from text_common import edit_distance

def heading_decision(text):
 base=original(text);normalized=unicodedata.normalize('NFKC',text)
 found={label:None for label in base['matches']}
 if base['label']:found[base['label']]=dict(kind='exact_heading',evidence=base['evidence'],matched_terms=[base['evidence']])
 # Long distinctive copy word: allow one OCR insertion/deletion/substitution.
 # No fuzzy merchant, document ID, amount or short "copy" matching.
 for word in re.findall(r'\b[a-zA-Z]{8,10}\b',normalized):
  distance=edit_distance(word.casefold(),'duplicate')
  if 0<distance<=1:
   found.setdefault('customer_copy',dict(kind='ocr_tolerant_copy_marker',evidence=word,matched_terms=[word],canonical_term='duplicate',edit_distance=distance));break
 # A request for future supply needs all three independent printed field groups.
 terms=[]
 for pattern in [r'\border\s+(?:no\.?|number|date)\b',r'\brequired\s+(?:by|date)\b',r'\bplease\s+supply\b|\brequest(?:ed)?\s+(?:goods|items)\b']:
  match=re.search(pattern,normalized,re.I)
  if match:terms.append(match.group(0))
 if len(terms)==3:
  found.setdefault('purchase_order',dict(kind='purchase_request_intent',evidence='; '.join(terms),matched_terms=terms))
 if len(found)==1:
  label=next(iter(found));detail=found[label]
  if detail is None:detail=dict(kind='exact_heading',evidence=base['evidence'],matched_terms=[base['evidence']])
  return dict(label=label,evidence=detail['evidence'],ambiguous=False,matches=list(found),rule=detail)
 return dict(label=None,evidence=None,ambiguous=len(found)>1,matches=list(found),rule=None)

