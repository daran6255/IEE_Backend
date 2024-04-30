import io
import os
import json
import uuid
import time
import random
import string
import pandas as pd
from dotenv import load_dotenv
from passlib.hash import sha256_crypt
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import mysql.connector
from datetime import datetime
from datetime import timedelta
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity


from iee_pipeline import IEEPipeline
from request_queue import RequestQueue
from utility import send_email

# template_dir = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
load_dotenv(override=True)

app = Flask(__name__, static_folder='frontend/static',
            template_folder='frontend/templates')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['JWT_SECRET_KEY'] = os.getenv('SECRET_KEY')

jwt = JWTManager(app)

CORS(app)

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

tags_file = r'data/tags.json'
credits_per_page = int(os.getenv('CREDITS_PER_PAGE'))
credits_value = int(os.getenv('CREDITS_VALUE'))

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


def init_db():
    try:
        cursor = db.cursor()
        query = """
            WITH customer_data AS (
                SELECT COUNT(*) AS totalCustomers,
                        SUM(availableCredits) AS totalAvailableCredits
                FROM user_info
                WHERE role = 'customer'
            ),
            credit_data AS (
                SELECT SUM(creditsBought) AS totalCredits,
                        SUM(amountPaid) AS totalAmount
                FROM credits
            ),
            used_credits AS (
                SELECT (credit_data.totalCredits - customer_data.totalAvailableCredits) AS usedCredits
                FROM customer_data, credit_data
            )
            UPDATE dashboard_stats
            SET totalCustomers = (SELECT totalCustomers FROM customer_data),
                totalCredits = (SELECT totalCredits FROM credit_data),
                usedCredits = (SELECT usedCredits FROM used_credits),
                totalInvoiceExtracted = (SELECT usedCredits / %s FROM used_credits),
                totalAmount = (SELECT totalAmount FROM credit_data)
            WHERE lockId = 1;
            """
        cursor.execute(query, (credits_per_page,))
        db.commit()
    except mysql.connector.Error as err:
        print(err)
    finally:
        cursor.close()


@app.route('/login', methods=['POST'])
def login():
    result = {'status': 'error',
              'result': 'An error occurred while processing your request'}

    if request.method == 'POST':
        response = request.get_json()
        email = response['email']
        password = response['password']

        try:
            cursor = db.cursor()
            query = "SELECT id, name, role, company, email, phone, password, verified FROM user_info WHERE email = %s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()
            db.commit()

            if user is not None:
                id, name, role, company, email, phone, stored_password, verified = user

                if not verified:
                    result = {'status': 'error',
                              'result': 'Email verification not done'}
                elif sha256_crypt.verify(password, stored_password):
                    expires = timedelta(days=1)
                    access_token = create_access_token(
                        identity=email, expires_delta=expires)
                    result = {'status': 'success',
                              'result': {
                                  'id': id, 'name': name, 'role': role, 'company': company, 'email': email,
                                  'phone': phone, 'accessToken': access_token,
                              }}
                else:
                    result = {'status': 'error',
                              'result': 'Invalid email or password'}
            else:
                result = {'status': 'error',
                          'result': 'Email not found. Please register'}

        except mysql.connector.Error as err:
            print(err)
        finally:
            cursor.close()

    return jsonify(result)


@app.route('/register', methods=['POST'])
def register():
    result = {'status': 'error',
              'result': 'An error occurred while processing your request'}

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
            db.commit()

            if user:
                result = {'status': 'error',
                          'result': 'User already present. Please login'}
            else:
                verification_code = serializer.dumps(email)
                encrypted_password = sha256_crypt.hash(password)
                insert_query = "INSERT INTO user_info (id, name, role, company, email, phone, password, verificationCode) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(
                    insert_query, (str(uuid.uuid4()), name, role, company, email, phone, encrypted_password, verification_code))
                db.commit()

                send_email(email, verification_code)

                result = {'status': 'success',
                          'result': 'Verification email has been sent to your email'}

        except mysql.connector.Error as err:
            print(err)

        finally:
            cursor.close()

    return jsonify(result)


@app.route('/verify_email/<token>')
def verify_email(token):
    result = {}

    try:
        email = serializer.loads(token, max_age=3600)

        cursor = db.cursor()
        cursor.execute(
            "UPDATE user_info SET verified = TRUE WHERE email = %s", (email,))
        db.commit()

        result = {'status': 'success', 'result': 'Email confirmed!'}

    except mysql.connector.Error as err:
        print(err)

    except SignatureExpired:
        result = {'status': 'error',
                  'result': 'The confirmation link is invalid or has expired'}

    finally:
        cursor.close()

    return jsonify(result)


@app.route('/get_customer_data', methods=['GET'])
@jwt_required()
def get_customer_data():
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({'status': 'error', 'result': 'User not authorized'})

    result = {'status': 'error',
              'result': 'An error occurred while processing your request'}

    try:
        cursor = db.cursor()
        query = "SELECT availableCredits, totalCredits, totalAmount FROM user_info WHERE role = 'customer' and email = %s"
        cursor.execute(query, (current_user,))
        user = cursor.fetchone()
        db.commit()

        if user is not None:
            availableCredits, totalCredits, totalAmount = user

            result = {'status': 'success',
                      'result': {
                          'availableCredits': availableCredits,
                          'totalCredits': totalCredits,
                          'usedCredits': totalCredits - availableCredits,
                          'invoiceExtracted': (totalCredits - availableCredits) / credits_per_page,
                          'remainingInvoices': availableCredits / credits_per_page,
                          'totalAmount': totalAmount,
                      }}
        else:
            result = {'status': 'error',
                      'result': 'Email not found. Please register'}

    except mysql.connector.Error as err:
        print(err)

    finally:
        cursor.close()

    return jsonify(result)


@app.route('/update_password', methods=['POST'])
@jwt_required()
def update_password():
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({'status': 'error', 'result': 'User not authorized'})

    result = {'status': 'error',
              'result': 'An error occurred while processing your request'}

    if request.method == 'POST':
        response = request.get_json()
        old_password = response['oldPassword']
        new_password = response['newPassword']

        try:
            cursor = db.cursor()
            query = "SELECT password FROM user_info WHERE email = %s"
            cursor.execute(query, (current_user,))
            user = cursor.fetchone()
            db.commit()

            if user is not None:
                stored_password = user[0]

                if sha256_crypt.verify(old_password, stored_password):
                    encrypted_password = sha256_crypt.hash(new_password)
                    cursor.execute(
                        "UPDATE user_info SET password = %s WHERE email = %s", (encrypted_password, current_user))
                    db.commit()
                    result = {'status': 'success',
                              'result': 'Password updated successfully'}
                else:
                    result = {'status': 'error',
                              'result': 'Wrong password entered'}
            else:
                result = {'status': 'error', 'result': 'User not found!'}

        except mysql.connector.Error as err:
            print(err)

        finally:
            cursor.close()

    return jsonify(result)


@app.route('/download_excel/<requestId>', methods=['GET'])
@jwt_required()
def download_excel(requestId):
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({'status': 'error', 'result': 'User not authorized'})

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
@jwt_required()
def download_json(requestId):
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({'status': 'error', 'result': 'User not authorized'})

    data = request_queue.get(requestId)

    if data:
        mem = io.BytesIO()
        json_data = json.dumps(data)
        mem.write(json_data.encode())
        mem.seek(0)
        return send_file(mem, download_name='entities.json', as_attachment=True)

    return jsonify({'Error': 'Request has expired'})


@app.route('/process_invoice', methods=['POST'])
@jwt_required()
def process_invoice():
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({'status': 'error', 'result': 'User not authorized'})

    if 'files[]' not in request.files:
        return jsonify({'Error': 'No file provided'})

    result = {'status': 'error',
              'result': 'An error occurred while processing your request'}

    try:
        cursor = db.cursor()
        query = "SELECT availableCredits FROM user_info WHERE email = %s"
        cursor.execute(query, (current_user,))
        user = cursor.fetchone()
        db.commit()

        if user is not None:
            availableCredits = int(user[0])
            files = request.files.getlist('files[]')

            if (availableCredits >= credits_per_page) and (availableCredits / credits_per_page) >= len(files):
                entities_extracted = []
                api_result = []
                successful_extraction = 0

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
                            pp_output_path = iee_pipeline.image_preprocessing(
                                input_file)
                            ocr_output = iee_pipeline.extract_text(
                                pp_output_path)
                            pp_txt_ouput = iee_pipeline.text_preprocessing(
                                ocr_output)
                            entities_output = iee_pipeline.extract_entities(
                                pp_txt_ouput)
                            items_output = iee_pipeline.extract_table_items(
                                input_file)

                            mapped_headings = iee_pipeline.table_extractor.map_table_columns(
                                table=items_output, ner_output=entities_output)

                            # Get table items for mapped headings
                            if mapped_headings:
                                indices = {k: items_output[0].index(v) for k, v in mapped_headings.items(
                                ) if v is not None and v != "N.E.R.Default"}

                                for k, idx in indices.items():
                                    entities_output[k] = [row[idx]
                                                          for row in items_output[1:]]

                            if len(entities_output) > 0:
                                successful_extraction += 1

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

                if len(entities_extracted) > 0:
                    requestId = str(uuid.uuid4())
                    request_queue[requestId] = entities_extracted

                    totalCreditsUsed = (
                        successful_extraction * credits_per_page)
                    availableCredits -= totalCreditsUsed

                    query = "UPDATE user_info SET availableCredits = %s WHERE email = %s"
                    cursor.execute(query, (availableCredits, current_user))

                    query = "UPDATE dashboard_stats SET usedCredits = usedCredits + %s, totalInvoiceExtracted = totalInvoiceExtracted + %s WHERE lockId = 1"
                    cursor.execute(
                        query, (totalCreditsUsed, successful_extraction))

                    db.commit()

                    result = {'status': 'success', 'result': {
                        'requestId': requestId, 'output': api_result}}
            else:
                result = {'status': 'error',
                          'result': 'Not enough credits to process invoices'}

    except Exception as err:
        print(err)

    finally:
        cursor.close()

    return jsonify(result)


@app.route('/get_customers', methods=['GET'])
@jwt_required()
def get_customers():
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({'status': 'error', 'result': 'User not authorized'})

    try:
        cursor = db.cursor()
        query = "SELECT id, name, company, email, phone, verified, availableCredits, totalCredits, totalAmount, createdAt FROM user_info WHERE role = 'customer'"
        cursor.execute(query)
        customers = cursor.fetchall()
        db.commit()

        result = [dict(zip([column[0] for column in cursor.description], row))
                  for row in customers]

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)})

    finally:
        cursor.close()


@app.route('/credits_history/<user_id>', methods=['GET'])
@jwt_required()
def get_credits_history(user_id):
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({'status': 'error', 'result': 'User not authorized'})

    try:
        cursor = db.cursor()
        query = "SELECT userId, creditsBought, amountPaid, paymentStatus, addedBy, paymentDate, createdAt FROM credits WHERE userId = %s"
        cursor.execute(query, (user_id,))
        credits_history = cursor.fetchall()
        db.commit()

        result = []
        for row in credits_history:
            result.append({
                'userId': row[0],
                'creditsBought': row[1],
                'amountPaid': float(row[2]),
                'paymentStatus': bool(row[3]),
                'addedBy': row[4],
                'paymentDate': row[5].isoformat() if row[5] else None,
                'createdDate': row[6]
            })

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)})

    finally:
        cursor.close()


@app.route('/dashboard_stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({'status': 'error', 'result': 'User not authorized'})

    try:
        cursor = db.cursor()
        query = "SELECT totalCustomers, totalCredits, usedCredits, totalInvoiceExtracted, totalAmount FROM dashboard_stats"
        cursor.execute(query)
        credits_history = cursor.fetchall()
        db.commit()

        result = []
        for row in credits_history:
            result.append({
                'totalCustomers': row[0],
                'totalCredits': float(row[1]),
                'usedCredits': row[2],
                'totalInvoiceExtracted': row[3],
                'totalAmount': str(row[4]) if row[4] is not None else None
            })

        return jsonify(result[0])

    except Exception as e:
        return jsonify({'error': str(e)})

    finally:
        cursor.close()


@app.route('/add_credits', methods=['POST'])
@jwt_required()
def add_credits():
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({'status': 'error', 'result': 'User not authorized'})

    result = {}

    try:
        cursor = db.cursor()
        start_time = time.time()

        response = request.get_json()

        while db.in_transaction:
            if time.time() - start_time > 10:
                raise Exception("Transaction is taking too long!")
            time.sleep(0.1)

        db.start_transaction()

        response = request.get_json()
        userId = response['userId']
        credits = int(response['credits'])
        addedBy = 'admin'

        amountPaid = credits * credits_value
        paymentDate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        query = "INSERT INTO credits(userId, creditsBought, amountPaid, paymentStatus, addedBy, paymentDate) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(
            query, (userId, credits, amountPaid, 1, addedBy, paymentDate))

        update_user_info = "UPDATE user_info SET availableCredits = availableCredits + %s, totalCredits = totalCredits + %s, totalAmount = totalAmount + %s WHERE id = %s"
        cursor.execute(update_user_info,
                       (credits, credits, amountPaid, userId))

        update_dashboard_stats = "UPDATE dashboard_stats SET totalCredits = totalCredits + %s, totalAmount = totalAmount + %s WHERE lockId = 1"
        cursor.execute(update_dashboard_stats, (credits, amountPaid))

        db.commit()
        result = {'status': 'success', 'result': 'Credits added successfully'}

    except Exception as err:
        print(err)
        db.rollback()
        result = {'status': 'error', 'result': 'Failed to add credits'}

    finally:
        cursor.close()

    return jsonify(result)


if __name__ == '__main__':
    init_db()

    if os.getenv('ENV') == 'prod':
        app.run(host='0.0.0.0', port=5000)
    else:
        app.run(host='0.0.0.0', port=5000, debug=True)
