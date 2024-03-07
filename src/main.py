import random
import string
from flask import Flask, jsonify, render_template, request, send_file
import os
import json
import pandas as pd
from iee_pipeline import IEEPipeline

entities_extracted = {}
# template_dir = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))


app = Flask(__name__, static_folder='frontend/static', template_folder='frontend/templates')

iee_pipeline = IEEPipeline()

TEMP_DIR = 'temp'
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download_excel')
def download_excel():
    data = entities_extracted
    df = pd.DataFrame(data)

    # Save DataFrame to Excel file
    excel_file = 'data.xlsx'
    df.to_excel(excel_file, index=False)

    return send_file(excel_file, as_attachment=True)

@app.route('/download_json')
def download_json():
      
    global entities_extracted
    if not entities_extracted:
        return jsonify({'error': 'No data to download'})
    output_directory = r'c:\Users\WVF-DL-90\Desktop\Invoice_Entities_Extraction\src\json_files'
    json_file_path = 'extracted_entities.json'
    json_file_path = os.path.join(output_directory, 'extracted_entities.json')
    
    with open(json_file_path, 'w') as f:
        json.dump(entities_extracted, f)
        
    return send_file(json_file_path, as_attachment=True)

@app.route('/process_invoice', methods=['POST'])
def process_invoice():
    global entities_extracted
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file:
        random_filename = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        file_ext = os.path.splitext(file.filename)[1]
        filename = random_filename + file_ext
        filepath = os.path.join(TEMP_DIR, filename)
        input_file = os.path.abspath(filepath)
        file.save(input_file)
        
        if file_ext == ".jpg" or file_ext == ".jpeg": 
            pp_output_path = iee_pipeline.image_preprocessing(input_file)
            ocr_output = iee_pipeline.extract_text(pp_output_path)
            pp_txt_ouput = iee_pipeline.text_preprocessing(ocr_output)
            entities_extracted = iee_pipeline.extract_entities(pp_txt_ouput)

            return jsonify(entities_extracted)
        
        return jsonify({'Error': 'Invoice Format Not Supported'})

if __name__ == '__main__':
    app.run(debug=True)
