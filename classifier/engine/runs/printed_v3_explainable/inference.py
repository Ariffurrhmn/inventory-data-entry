"""Shared saved-model inference for the local printed classifier."""
import json
from pathlib import Path
import joblib
from text_common import HERE,CLASSES,clean_text,ocr_image,sha
from ocr_v2 import sparse_ocr,combine_outputs

def heading_for_selection(selection,text):
    from importlib import import_module
    module=selection.get('heading_module','heading_rules')
    if module not in ['heading_rules','heading_rules_v2','heading_rules_v3']:raise ValueError('Unknown document-rule module')
    return import_module(module).heading_decision(text)

class Predictor:
    def __init__(self,run=None):
        active_path=HERE/'active_text_model.json'
        active=json.loads(active_path.read_text(encoding='utf-8')) if active_path.exists() and run is None else None
        self.run=run or (active['run'] if active else 'text_preliminary')
        directory=HERE/'runs'/self.run
        if not directory.resolve().is_relative_to((HERE/'runs').resolve()):raise ValueError('Invalid run path')
        self.selection=json.loads((directory/'selection.json').read_text(encoding='utf-8'))
        self.name=self.selection.get('selected') or self.selection['candidate']
        self.path=directory/(self.name+'.joblib')
        self.model_hash=sha(self.path)
        if active and active['model_sha256']!=self.model_hash:raise ValueError('Active model hash mismatch')
        self.policy=self.selection.get('ocr_policy','baseline')
        self.heading_rules=bool(self.selection.get('heading_rules'))
        self.edge_recovery=bool(self.selection.get('edge_recovery'))
        if self.edge_recovery and sha(HERE/'edge_ocr.py')!=self.selection['edge_code_sha256']:raise ValueError('Edge OCR version mismatch')
        self.heading_module=self.selection.get('heading_module','heading_rules')
        if self.heading_module not in ['heading_rules','heading_rules_v2','heading_rules_v3']:raise ValueError('Invalid heading module')
        if self.heading_rules and sha(HERE/(self.heading_module+'.py'))!=self.selection['heading_rule_sha256']:raise ValueError('Heading rule version does not match saved selection')
        if self.selection.get('heading_base_sha256') and sha(HERE/'heading_rules.py')!=self.selection['heading_base_sha256']:raise ValueError('Base heading rule version mismatch')
        for filename,digest in self.selection.get('rule_dependencies',{}).items():
            if filename not in ['heading_rules.py','heading_rules_v2.py'] or sha(HERE/filename)!=digest:raise ValueError('Rule dependency version mismatch')
        self.illumination_recovery=bool(self.selection.get('illumination_recovery'))
        if self.illumination_recovery and sha(HERE/'illumination_ocr.py')!=self.selection['illumination_code_sha256']:raise ValueError('Illumination OCR version mismatch')
        if self.selection.get('backend')=='minilm' and sha(HERE/'transformer_models.py')!=self.selection['transformer_code_sha256']:raise ValueError('Transformer inference version mismatch')
        self.model=joblib.load(self.path)
        if self.selection.get('backend')=='minilm':self.model.load()
        if set(self.model.classes_)!=set(CLASSES):raise ValueError('Model must contain the four document classes')

    def metadata(self):
        return dict(run=self.run,model=self.name,backend=self.selection.get('backend','tfidf'),model_sha256=self.model_hash,scope_version=self.selection.get('scope_version','legacy'),ocr_policy=self.policy,heading_rules=self.heading_rules,edge_recovery=self.edge_recovery,classes=CLASSES,experimental=True,heading_module=self.heading_module,illumination_recovery=self.illumination_recovery)

    def extract(self,path):
        path=Path(path)
        if path.suffix.lower() in ['.heic','.heif']:
            from pillow_heif import register_heif_opener
            register_heif_opener()
        if self.policy in ['sparse','combined']:
            sparse=sparse_ocr(path)
            return sparse if self.policy=='sparse' else combine_outputs(ocr_image(path),sparse)
        return ocr_image(path)

    def predict_text(self,text,origin='provided_text',heading_text=None):
        cleaned=clean_text(text)
        if not cleaned:raise ValueError('No readable printed text was found. Try a clearer image or paste OCR text.')
        scores=self.model.predict_proba([cleaned])[0]
        fallback=str(self.model.classes_[scores.argmax()]);cue=dict(label=None,evidence=None,ambiguous=False,matches=[])
        if self.heading_rules:
            cue=heading_for_selection(self.selection,heading_text if heading_text is not None else text)
        source='document_intent_rule' if (cue.get('rule') or {}).get('kind')=='purchase_request_intent' else 'printed_heading' if cue['label'] else 'trained_classifier'
        alternative=next(str(self.model.classes_[i]) for i in scores.argsort()[::-1] if str(self.model.classes_[i])!=fallback)
        trace=dict(selected_component=source if cue['label'] else 'learned_fallback',heading_matches=cue['matches'],ambiguous_heading=cue['ambiguous'],normalized_heading_evidence=cue['evidence'],learned_top_class=fallback,learned_alternative_class=alternative,learned_score_margin=float(scores.max()-scores[list(map(str,self.model.classes_)).index(alternative)]),scores_calibrated=False,rule=cue.get('rule'),explanation_method='Deterministic rule trace or exact n-gram contributions; transformers use fixed-model text omissions')
        return dict(decision_trace=trace,label=cue['label'] or fallback,decision_source=source,heading_evidence=cue['evidence'],ambiguous_heading=cue['ambiguous'],statistical_label=fallback,scores_kind='statistical_fallback_scores',scores=dict(zip(map(str,self.model.classes_),map(float,scores))),scores_calibrated=False,ocr_empty=False,text_characters=len(cleaned),input_origin=origin,ocr_text=text,heading_ocr_text=heading_text,validation_only=self.selection.get('new_test_result','legacy') is None,**self.metadata())

    def predict_image(self,path):
        if self.illumination_recovery:
            from illumination_ocr import illumination_ocr
            from edge_ocr import edge_ocr
            views=illumination_ocr(path);sparse=sparse_ocr(path);edge=edge_ocr(path)
            context='\f'.join([sparse,edge]+list(views.values()))
            return self.predict_text(views['full'] if clean_text(views['full']) else context,'Tesseract_corrected_OCR',heading_text=context)
        text=self.extract(path)
        if self.edge_recovery:
            from edge_ocr import edge_ocr
            context=text+'\n'+edge_ocr(path)
            return self.predict_text(text if clean_text(text) else context,'Tesseract_OCR',heading_text=context)
        return self.predict_text(text,'Tesseract_OCR')


