import os
import re
from datetime import datetime
from dateutil import parser

input_folder = r'C:\Users\WVF-DL-90\Desktop\Invoice_Entities_Extraction\data\dataset\invoice_ocr'
output_folder = r'C:\Users\WVF-DL-90\Desktop\Invoice_Entities_Extraction\data\dataset\invoice_final'

def text_clean(text):
    if isinstance(text, list):
        text = ' '.join(text)
    cleaned_text = re.sub(r',', '', text)
    # print(cleaned_text)
    cleaned_text_1 = re.sub(r'[^a-zA-Z0-9\s\\\.\-\/]', ' ', cleaned_text)  
    cleaned_text_2 = re.sub(r'\s+', ' ', cleaned_text_1)
    return cleaned_text_2.strip()

def text_tokenizer(text):
    tokens = text.split()
    return tokens

def text_normalization(tokens):
    normalized_tokens = [token.lower() for token in tokens]
    return normalized_tokens

def convert_to_dd_mm_yyyy(date_string):
    formats = ['%d-%m-%Y', '%d/%m/%Y', '%d %b %Y', '%d %B %Y', '%d-%b-%y' ,'%Y-%m-%d', '%A, %d %B %Y', '%d/%m/%y']
    for fmt in formats:
        try:
            # Attempt to parse the date string
            parsed_date = datetime.strptime(date_string, fmt)
            # Convert the parsed date to 'dd/mm/yyyy' format
            return parsed_date.strftime('%d/%m/%Y')
        except ValueError:
            pass  # If ValueError is raised, try the next format
    return None  # If none of the formats match, return None

def date_standardization(tokens):
    standardized_tokens = []
    for token in tokens:
        # if re.match(r'\d{1,2}/\d{1,2}/\d{2,4}', token) or re.match(r'\d{1,2}-[a-zA-Z]{3}-\d{2,4}', token):
        converted_date = convert_to_dd_mm_yyyy(token)
        if converted_date:
            standardized_tokens.append(converted_date) 
        else:
            # print(f"{converted_date} is not in Indian date format.")
            standardized_tokens.append(token)
    return standardized_tokens

def process_invoices(input_folder, output_folder):
    # os.remove(output_folder)
    files = os.listdir(input_folder)
    files.sort(key=lambda f: int(re.sub('\D', '', f)))
    print(files)
    for index, invoice_file in enumerate(files, 1):
        input_file = os.path.join(input_folder, invoice_file)
        with open(input_file, 'r') as file:
            invoice_text = file.read()
        
        output1 = text_clean(invoice_text)
        output2 = text_tokenizer(output1)
        output3 = text_normalization(output2)
        output4 = date_standardization(output3)
        output_paragraph = ' '.join(output4)
        
        output_file = os.path.join(output_folder, f'final_text_annotations_{index}.txt')
        with open(output_file, 'w') as file:
            file.write(output_paragraph)
        
        print(f'Processed {invoice_file} and saved output to {output_file}')

if __name__ == "__main__":
    process_invoices(input_folder, output_folder)
