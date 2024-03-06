import spacy
import json

class extractEntities:
    
    def __init__(self, model_dir):
        self.spacy_sm = spacy.load(model_dir + "model_path")
        pass
    
    def extract_entities_spacy_sm(self, input_text):
        doc = self.spacy_sm(input_text)
        entities = {ent.label_: ent.text for ent in doc.ents}
        # json_str = json.dumps(entities, indent=4)
        # print(json_str)
        # with open("ner_entities.json", "w") as f:
        #     f.write(json_str)
        return entities
    def extract_entities_spacy_lg(self, input_text):
        doc = self.spacy_sm(input_text)
        entities = {ent.label_: ent.text for ent in doc.ents}
        return entities
    def extract_entities_spacy_tr(self, input_text):
        doc = self.spacy_sm(input_text)
        entities = {ent.label_: ent.text for ent in doc.ents}
        return entities