import io
import os
import json
import uuid
import random
import string
import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file, redirect, url_for
from flask_cors import CORS
import mysql.connector
from sympy import false

from iee_pipeline import IEEPipeline
from request_queue import RequestQueue

# template_dir = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

app = Flask(__name__, static_folder='frontend/static',
            template_folder='frontend/templates')
CORS(app)
tags_file = r'data/tags.json'

iee_pipeline = IEEPipeline()
request_queue = RequestQueue(size_limit=20)

TEMP_DIR = 'temp'
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# MySQL Configuration
DB_HOST = 'localhost'
DB_USER = 'winvinaya_iee'
DB_PASSWORD = 'wvi@iee123&'
DB_NAME = 'invoice_extraction'
DB_PORT = 3306

# Connect to MySQL
db = mysql.connector.connect(
    host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/home')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            cursor = db.cursor()
            query = "SELECT * FROM user_info WHERE email = %s AND password = %s"
            cursor.execute(query, (email, password))
            user = cursor.fetchone()
            cursor.close()

            if user:
                return redirect(url_for('home'))
            else:
                return redirect(url_for('login', error='Invalid email or password'))

        except mysql.connector.Error as err:
            cursor.close()
            return render_template('login.html', error='An error occurred while processing your request')

    return render_template('login.html')


@app.route('/logout')
def logout():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        response = request.form.to_dict()
        name = response['name']
        company = response['company']
        email = response['email']
        phone = response['phone']
        password = response['password']

        try:
            # Check if the email already exists
            cursor = db.cursor()
            query = "SELECT * FROM user_info WHERE email = %s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()

            if user:
                print(user)
                return render_template('register.html', error='Email already exists')

            cursor = db.cursor()
            insert_query = "INSERT INTO user_info (name, company, email, phone, password) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(
                insert_query, (name, company, email, phone, password))
            db.commit()
            cursor.close()

            return redirect(url_for('login'))

        except mysql.connector.Error as err:
            cursor.close()
            print(err)
            return render_template('register.html', error='An error occurred while processing your request')

    return render_template('register.html')


@app.route('/download_excel/<requestId>', methods=['GET'])
def download_excel(requestId):
    data = request_queue.get(requestId)

    if data:
        with open(tags_file, 'r') as f:
            tags_data = json.load(f)

        tags = [item['name'] for item in tags_data]
        items_tags = ['ITEMNAME', 'HSN', 'QUANTITY',
                      'UNIT', 'PRICE', 'AMOUNT']  # Multi items
        other_tags = [tag for tag in tags if tag not in items_tags]

        serial_no = 1
        df = pd.DataFrame(columns=['SL. NO'] + tags + ['FILENAME'])

        for invoice in data:
            entities = invoice['entities']
            max_items = max(len(v) for v in entities.values())

            invoice_data = {}

            for tag in tags:
                if tag in entities:
                    if tag in items_tags:
                        invoice_data[tag] = entities[tag] + \
                            ['VERIFY IMAGE'] * (max_items - len(entities[tag]))
                    elif tag in other_tags:
                        invoice_data[tag] = [entities[tag][0]] * max_items
                else:
                    invoice_data[tag] = ['VERIFY IMAGE'] * max_items

            invoice_df = pd.DataFrame(invoice_data, columns=tags)
            invoice_df.insert(0, 'SL. NO', serial_no)
            invoice_df.insert(len(tags), 'FILENAME', invoice['filename'])

            serial_no += 1
            df = pd.concat([df, invoice_df], ignore_index=True)

        mem = io.BytesIO()
        with pd.ExcelWriter(mem, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        mem.seek(0)

        return send_file(mem, download_name='entities.xlsx', as_attachment=True)

    return jsonify({'Error': 'Request has expired'})


@app.route('/download_json/<requestId>', methods=['GET'])
def download_json(requestId):
    data = request_queue.get(requestId)

    if data:
        mem = io.BytesIO()
        json_data = json.dumps(data)
        mem.write(json_data.encode())
        mem.seek(0)
        return send_file(mem, download_name='entities.json', as_attachment=True)

    return jsonify({'Error': 'Request has expired'})


@app.route('/process_invoice', methods=['POST'])
def process_invoice():
    if 'files[]' not in request.files:
        return jsonify({'Error': 'No file provided'})

    files = request.files.getlist('files[]')
    entities_extracted = []
    api_result = []

    for file in files:
        if file.filename == '':
            continue

        if file:
            random_filename = ''.join(random.choices(
                string.ascii_letters + string.digits, k=10))
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
                items_output = iee_pipeline.extract_table_items(input_file)

                mapped_headings = iee_pipeline.table_extractor.map_table_columns(
                    table=items_output, ner_output=entities_output)

                # Get table items for mapped headings
                if mapped_headings:
                    indices = {k: items_output[0].index(v) for k, v in mapped_headings.items(
                    ) if v is not None and v != "N.E.R.Default"}

                    for k, idx in indices.items():
                        entities_output[k] = [row[idx]
                                              for row in items_output[1:]]

                # Add items to output
                entities_output['items'] = items_output

                # Remove item entities only for api
                items_tags = ['ITEMNAME', 'HSN', 'QUANTITY',
                              'UNIT', 'PRICE', 'AMOUNT']
                final_result = {key: entities_output[key]
                                for key in entities_output if key not in items_tags}

                if entities_output:
                    entities_extracted.append(
                        {'filename': file.filename, 'entities': entities_output})
                    api_result.append(
                        {'filename': file.filename, 'entities': final_result})

            else:
                continue

    if entities_extracted:
        requestId = str(uuid.uuid4())
        request_queue[requestId] = entities_extracted

        return jsonify({'requestId': requestId, 'result': api_result})

    return jsonify({'Error': 'No output extracted'})


if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5000)
    app.run(host='0.0.0.0', port=5000, debug=True)
