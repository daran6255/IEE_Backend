import random
import string
from flask import Flask, jsonify, render_template, request, send_file
import os
import json
import pandas as pd
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
