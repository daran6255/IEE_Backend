import spacy


model_path =r'C:\Users\WVF-DL-90\Desktop\Invoice_Entities_Extraction\ner\output\model-best'
nlp = spacy.load(model_path)
output_dir = r'data\spacy_model'
nlp.to_disk(output_dir)