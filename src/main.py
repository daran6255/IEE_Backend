import io
import os
import json
import uuid
import random
import string
import pandas as pd
from dotenv import load_dotenv
from passlib.hash import sha256_crypt
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import mysql.connector
from itsdangerous import URLSafeTimedSerializer, SignatureExpired

from iee_pipeline import IEEPipeline
from request_queue import RequestQueue
from utility import send_email

# template_dir = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
load_dotenv(override=True)

app = Flask(__name__, static_folder='frontend/static',
            template_folder='frontend/templates')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

CORS(app)

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

tags_file = r'data/tags.json'

iee_pipeline = IEEPipeline()
request_queue = RequestQueue(size_limit=20)

TEMP_DIR = 'temp'
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Connect to MySQL
db = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        response = request.get_json()
        email = response['email']
        password = response['password']

        try:
            cursor = db.cursor()
            query = "SELECT id, name, role, company, email, phone, password, availableCredits, totalCredits, verified FROM user_info WHERE email = %s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()

            cursor.close()

            if user is not None:
                id, name, role, company, email, phone, stored_password, availableCredits, totalCredits, verified = user

                if not verified:
                    return jsonify({'status': 'error', 'result': 'Email verification not done'})
                elif sha256_crypt.verify(password, stored_password):
                    return jsonify(
                        {'status': 'success',
                         'result': {
                             'id': id, 'name': name, 'role': role, 'company': company, 'email': email,
                             'phone': phone, 'creditsavailable': availableCredits, 'totalcredits': totalCredits
                         }}
                    )
                else:
                    return jsonify({'status': 'error', 'result': 'Invalid email or password'})
            else:
                return jsonify({'status': 'error', 'result': 'Email not found. Please register'})

        except mysql.connector.Error as err:
            cursor.close()
            print(err)

    return jsonify({'status': 'error', 'result': 'An error occurred while processing your request'})


@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        response = request.get_json()
        name = response['name']
        role = response['role']
        company = response['company']
        email = response['email']
        phone = response['phone']
        password = response['password']

        try:
            cursor = db.cursor()
            query = "SELECT * FROM user_info WHERE email = %s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()

            if user:
                return jsonify({'status': 'error', 'result': 'User already present. Please login'})

            cursor = db.cursor()
            verification_code = serializer.dumps(email)
            encrypted_password = sha256_crypt.hash(password)
            insert_query = "INSERT INTO user_info (id, name, role, company, email, phone, password, verificationCode) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(
                insert_query, (str(uuid.uuid4()), name, role, company, email, phone, encrypted_password, verification_code))
            db.commit()
            cursor.close()

            send_email(email, verification_code)

            return jsonify({'status': 'success', 'result': 'Verification email has been sent to your email'})

        except mysql.connector.Error as err:
            cursor.close()
            print(err)

    return jsonify({'status': 'error', 'result': 'An error occurred while processing your request'})


@app.route('/update_password', methods=['POST'])
def update_password():
    if request.method == 'POST':
        response = request.get_json()
        email = response['email']
        old_password = response['oldPassword']
        new_password = response['newPassword']

        try:
            cursor = db.cursor()
            query = "SELECT password FROM user_info WHERE email = %s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()

            cursor.close()

            if user is not None:
                stored_password = user[0]

                if sha256_crypt.verify(old_password, stored_password):
                    encrypted_password = sha256_crypt.hash(new_password)
                    cursor = db.cursor()
                    cursor.execute(
                        "UPDATE user_info SET password = %s WHERE email = %s", (encrypted_password, email))
                    db.commit()
                    cursor.close()
                    return jsonify({'status': 'success', 'result': 'Password updated successfully'})
                else:
                    return jsonify({'status': 'error', 'result': 'Wrong password entered'})
            else:
                return jsonify({'status': 'error', 'result': 'Wrong email provided!'})

        except mysql.connector.Error as err:
            cursor.close()
            print(err)

    return jsonify({'status': 'error', 'result': 'An error occurred while processing your request'})


@app.route('/verify_email/<token>')
def verify_email(token):
    try:
        email = serializer.loads(token, max_age=3600)
    except SignatureExpired:
        return jsonify({'status': 'error', 'result': 'The confirmation link is invalid or has expired'})

    cursor = db.cursor()
    cursor.execute(
        "UPDATE user_info SET verified = TRUE WHERE email = %s", (email,))
    db.commit()
    cursor.close()

    return jsonify({'status': 'success', 'result': 'Email confirmed!'})


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
            only_entities = {k: v for k, v in entities.items() if k not in [
                'items']}
            max_items = max(len(v) for v in only_entities.values())

            invoice_data = {}

            for tag in tags:
                if tag in only_entities:
                    if tag in items_tags:
                        invoice_data[tag] = only_entities[tag] + \
                            ['VERIFY IMAGE'] * \
                            (max_items - len(only_entities[tag]))
                    elif tag in other_tags:
                        invoice_data[tag] = [only_entities[tag][0]] * max_items
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


@app.route('/get_customers', methods=['GET'])
def get_customers():
    try:
        cursor = db.cursor()
        query = "SELECT id, name, company, email, phone, verified, availableCredits, totalCredits, createdAt FROM user_info WHERE role = 'customer'"
        cursor.execute(query)
        customers = cursor.fetchall()
        cursor.close()

        result = [dict(zip([column[0] for column in cursor.description], row))
                  for row in customers]

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/credits_history/<user_id>', methods=['GET'])
def get_credits_history(user_id):

    try:
        cursor = db.cursor()
        query = "SELECT userId, addedBy, creditsBought, amountPaid, paymentStatus, paymentDate, createdDate FROM credits WHERE userId = %s"
        cursor.execute(query, (user_id,))
        credits_history = cursor.fetchall()
        cursor.close()

        result = []
        for row in credits_history:
            result.append({
                'userId': row[0],
                'addedBy': row[1],
                'creditsBought': row[2],
                'amountPaid': float(row[3]),
                'paymentStatus': bool(row[4]),
                'paymentDate': row[5].isoformat() if row[5] else None,
                'createdDate': row[6]    
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})
    
@app.route('/dashboard_stats', methods=['GET'])
def get_dashboard_stats():

    try:
        cursor = db.cursor()
        query = "SELECT lockId, totalCustomers, totalCredits, usedCredits, totalInvoiceExtracted, totalAmount FROM dashboard_stats"
        cursor.execute(query)
        credits_history = cursor.fetchall()
        cursor.close()

        result = []
        for row in credits_history:
            result.append({
                'lockId': row[0],
                'totalCustomers': row[1],
                'totalCredits': float(row[2]),
                'usedCredits': bool(row[3]),
                'totalInvoiceExtracted': row[4],
                'totalAmount': str(row[5]) if row[4] is not None else None
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    if os.getenv('ENV') == 'prod':
        app.run(host='0.0.0.0', port=5000)
    else:
        app.run(host='0.0.0.0', port=5000, debug=True)
