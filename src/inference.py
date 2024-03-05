import spacy
import json
input_text ='adithya trade links near rameshwara circle 3rd cross s n nagara tel. 9632723766 email adithyatradel gmail.com by gstin 29cxbpk6398h1zw tax invoice party rawgranules private limit invoice no. atl-1774 no 9 kerekai talavata dated 01/09/2023 talaguppa sagara vehicle no gstin 29aalcro358l1zu destination .n. description of goods hsn gst qty. unit price amount 7 1. exo safai small 10/- 68053000 18 90.00 pcs. 8.25 742.50 add rounded off 0.50 grand total z 743.00 tax rate taxableamt. cgstamt. sgstamt. total tax 18 629.24 56.63 56.63 113.26 rupees seven hundred forty three only bank name axis bank for adithya trade links branch ashok road sagara a/c no 921020038859030 ifsc code utib0002024 authorised signatory'
model_path = r'data\spacy_model'
nlp = spacy.load(model_path)
doc = nlp(input_text)
# entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
entities = {ent.label_: ent.text for ent in doc.ents}
print(entities)
json_str = json.dumps(entities, indent=4)
print(json_str)
with open("ner_entities.json", "w") as f:
    f.write(json_str)