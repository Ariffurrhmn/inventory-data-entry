"""Apply the same conservative rules independently to each named OCR view."""
from heading_rules_v2 import heading_decision as recover

def heading_decision(text):
 sections=text.split('\f');found={}
 # Keep cross-view intent/copy recovery, and independently inspect each view's titles.
 for index,section in [(-1,text)]+list(enumerate(sections)):
  cue=recover(section)
  for label in cue['matches']:
   detail=dict(cue['rule'],ocr_section_index=index) if cue['label']==label and cue.get('rule') else None
   if label not in found or found[label] is None:found[label]=detail
 if len(found)==1:
  label=next(iter(found));detail=found[label]
  return dict(label=label,evidence=detail['evidence'],ambiguous=False,matches=list(found),rule=detail)
 return dict(label=None,evidence=None,ambiguous=len(found)>1,matches=list(found),rule=None)

