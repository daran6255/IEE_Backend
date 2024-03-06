import re
from datetime import datetime
from dateutil import parser

class TextPreprocessor:
    def __init__(self):
        pass
    
    def text_clean(self, text):
        if isinstance(text, list):
            text = ' '.join(text)
        cleaned_text = re.sub(r',', '', text)
        cleaned_text_1 = re.sub(r'[^a-zA-Z0-9\s\\\.\-\/]', ' ', cleaned_text)  
        cleaned_text_2 = re.sub(r'\s+', ' ', cleaned_text_1)
        return cleaned_text_2.strip()

    def text_tokenizer(self, text):
        tokens = text.split()
        return tokens

    def text_normalization(self, tokens):
        normalized_tokens = [token.lower() for token in tokens]
        return normalized_tokens

    def _convert_to_dd_mm_yyyy(self, date_string):
        formats = ['%d-%m-%Y', '%d/%m/%Y', '%d %b %Y', '%d %B %Y', '%d-%b-%y' ,'%Y-%m-%d', '%A, %d %B %Y', '%d/%m/%y']
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_string, fmt)
                return parsed_date.strftime('%d/%m/%Y')
            except ValueError:
                pass
        return None

    def date_standardization(self, tokens):
        standardized_tokens = []
        for token in tokens:
            converted_date = self._convert_to_dd_mm_yyyy(token)
            if converted_date:
                standardized_tokens.append(converted_date) 
            else:
                standardized_tokens.append(token)
        return standardized_tokens
