from random import random
from flask import Flask, jsonify, render_template, request, send_file
import json
import pandas as pd
import os

from iee_pipeline import IEEPipeline

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
    # Create sample Excel data (you can replace this with your data)
    data = {'Name': ['John', 'Anna', 'Peter', 'Linda'],
            'Age': [28, 35, 42, 25],
            'City': ['New York', 'Paris', 'Berlin', 'London']}
    df = pd.DataFrame(data)

    # Save DataFrame to Excel file
    excel_file = 'data.xlsx'
    df.to_excel(excel_file, index=False)

    return send_file(excel_file, as_attachment=True)

@app.route('/download_json')
def download_json():
    # Create sample JSON data (you can replace this with your data)
    data = {'Name': ['John', 'Anna', 'Peter', 'Linda'],
            'Age': [28, 35, 42, 25],
            'City': ['New York', 'Paris', 'Berlin', 'London']}
    json_data = json.dumps(data)

    # Save JSON data to file
    json_file = 'data.json'
    with open(json_file, 'w') as file:
        file.write(json_data)

    return send_file(json_file, as_attachment=True)

@app.route('/process_invoice', methods=['POST'])
def process_invoice():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'})
    file = request.files['file']
    file_path = os.path.join(TEMP_DIR, 'temp_file_' + random())
    file.save(file_path)
    
    pp_output = iee_pipeline.image_preprocessing(file_path)
    ocr_output = iee_pipeline.extract_text(pp_output)
    txt_pp_ouput = iee_pipeline.text_preprocessing(ocr_output)
    entities_extracted = iee_pipeline.extract_entities(txt_pp_ouput)
    
    return jsonify(entities_extracted)
    
if __name__ == '__main__':
    app.run(debug=True)
