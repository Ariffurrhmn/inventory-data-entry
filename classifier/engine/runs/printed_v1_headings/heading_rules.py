"""Deterministic document-title cues; no merchant names or sample IDs."""
import re,unicodedata
PATTERNS={
 'purchase_order':r'^\s*(?:purchase\s*order|order\s*(?:form|slip))\b',
 'delivery_note':r'^\s*(?:delivery\s*(?:note|challan)|packing\s*slip|challan\b)',
}
COPY=re.compile(r'\b(?:customer|cardholder|guest|office)\s*(?:receipt\s*)?copy\b|\bduplicate\b',re.I)

def heading_decision(text):
 normalized=unicodedata.normalize('NFKC',text)
 lines=[re.sub(r'[^\w\s#:-]',' ',line).strip() for line in normalized.splitlines() if line.strip()]
 titles=lines[:30]+[' '.join(lines[i:i+2]) for i in range(min(len(lines)-1,30))]
 found={}
 for label,pattern in PATTERNS.items():
  for line in titles:
   if len(line)<=100 and re.search(pattern,line,re.I):found[label]=line;break
 match=COPY.search(normalized)
 if match:found['customer_copy']=match.group(0)
 # A copy-marked order/delivery hybrid needs taxonomy review, not an invented precedence rule.
 if len(found)==1:
  label=next(iter(found));return dict(label=label,evidence=found[label],ambiguous=False,matches=list(found))
 return dict(label=None,evidence=None,ambiguous=len(found)>1,matches=list(found))
