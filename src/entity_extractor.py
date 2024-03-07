import spacy
from collections import defaultdict

class extractEntities:
    spacy_sm = None
    spacy_lg = None
    spacy_tr = None
    
    def __init__(self, model_dir):
        # self.spacy_sm = spacy.load(model_dir + "/spacy_sm")
        # self.spacy_lg = spacy.load(model_dir + "/spacy_lg")
        self.spacy_tr = spacy.load(model_dir + "/spacy_tr")
        pass
    
    
    def extract_entities_spacy_sm(self, input_text):
        doc = self.spacy_sm(input_text)
        entities = {ent.label_: ent.text for ent in doc.ents}
        return entities
    
    
    def extract_entities_spacy_lg(self, input_text):
        doc = self.spacy_lg(input_text)
        entities = {ent.label_: ent.text for ent in doc.ents}
        return entities
    
    
    def extract_entities_spacy_tr(self, input_text):
        doc = self.spacy_tr(input_text)
        
        entity_dict = defaultdict(list)

        for ent in doc.ents:
            entity_dict[ent.label_].append(ent.text)

        entities = dict(entity_dict)
        return entities