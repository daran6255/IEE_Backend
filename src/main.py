import io
import os
import json
import uuid
import random
import string
import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file

from iee_pipeline import IEEPipeline
from request_queue import RequestQueue

# template_dir = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

app = Flask(__name__, static_folder='frontend/static', template_folder='frontend/templates')

iee_pipeline = IEEPipeline()
request_queue = RequestQueue(size_limit=20)

TEMP_DIR = 'temp'
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download_excel/<requestId>', methods=['GET'])
def download_excel(requestId):
    data = request_queue[requestId]
    
    if data:
        df = pd.DataFrame(data)

        # Save DataFrame to Excel file
        excel_file = 'data.xlsx'
        df.to_excel(excel_file, index=False)

        return send_file(excel_file, as_attachment=True)
    
    return jsonify({'Error': 'Request has expired'})    

@app.route('/download_json/<requestId>', methods=['GET'])
def download_json(requestId):
    data = request_queue[requestId]
    
    if data:
        mem = io.BytesIO()
        json.dump(data, mem)
        mem.seek(0)
            
        return send_file(mem, attachment_filename=requestId + '_entities.json', as_attachment=True)

    return jsonify({'Error': 'Request has expired'})  

@app.route('/process_invoice', methods=['POST'])
def process_invoice():
    if 'files' not in request.files:
        return jsonify({'Error': 'No file provided'})
    
    files = request.files.getlist['files']
    entities_extracted = []
    
    for file in files:
        if file.filename == '':
            continue
        
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
                entities_output = iee_pipeline.extract_entities(pp_txt_ouput)

                if entities_output:
                    entities_extracted.append({'filename': file.filename, 'enitites': entities_output})
            
            return jsonify({'Error': 'Invoice Format Not Supported'})
       
    if entities_extracted:
        requestId = uuid.uuid4()
        request_queue[requestId] = entities_extracted
        
        return jsonify({'requestId': requestId, 'result': entities_extracted})
    
    return jsonify({'Error': 'No output extracted'})

if __name__ == '__main__':
    app.run(debug=True)
