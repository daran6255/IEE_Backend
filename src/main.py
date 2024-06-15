import io
import os
import json
import uuid
import time
import shutil
import pandas as pd
from passlib.hash import sha256_crypt
from flask import Flask, jsonify, request, send_file, send_from_directory, make_response
from flask_cors import CORS
import mysql.connector
from datetime import timedelta, datetime
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

from src.db import cnxpool
from src.iee_pipeline import IEEPipeline
from src.utility import InvoiceStatus, send_email, generate_user_verified_email
from src.celery_config import process_request

# template_dir = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

upload_dir = os.getenv("UPLOAD_DIR")

app = Flask(__name__, static_folder=os.path.abspath(upload_dir))
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["JWT_SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config.update(
    broker_url=os.getenv("CELERY_RESULT_BACKEND"),
    result_backend=os.getenv("CELERY_BROKER_URL"),
)

iee_pipeline = IEEPipeline()
jwt = JWTManager(app)
CORS(app)


tags_file = r"data/tags.json"
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
credits_per_page = int(os.getenv("CREDITS_PER_PAGE"))
credits_value = int(os.getenv("CREDITS_VALUE"))
assets_url = os.getenv("HOST")


with open(tags_file, "r") as f:
    tags_data = json.load(f)

itags = [item["name"] for item in tags_data]
items_itags = ["ITEMNAME", "HSN", "QUANTITY", "UNIT", "PRICE", "AMOUNT"]
other_itags = [tag for tag in itags if tag not in items_itags]


if not os.path.exists(upload_dir):
    os.makedirs(upload_dir)


@app.route("/login", methods=["POST"])
def login():
    result = {
        "status": "error",
        "result": "An error occurred while processing your request",
    }

    if request.method == "POST":
        response = request.get_json()
        email = response["email"]
        password = response["password"]

        cnx = None
        cursor = None

        try:
            cnx = cnxpool.get_connection()
            cursor = cnx.cursor()
            query = "SELECT id, name, role, company, email, phone, password, verified FROM user_info WHERE email = %s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()
            cnx.commit()

            if user is not None:
                id, name, role, company, email, phone, stored_password, verified = user

                if not verified:
                    result = {
                        "status": "error",
                        "result": "Email verification not done",
                    }
                elif sha256_crypt.verify(password, stored_password):
                    expires = timedelta(days=1)
                    access_token = create_access_token(
                        identity=email, expires_delta=expires
                    )
                    result = {
                        "status": "success",
                        "result": {
                            "id": id,
                            "name": name,
                            "role": role,
                            "company": company,
                            "email": email,
                            "phone": phone,
                            "accessToken": access_token,
                        },
                    }
                else:
                    result = {"status": "error",
                              "result": "Invalid email or password"}
            else:
                result = {
                    "status": "error",
                    "result": "Email not found. Please register",
                }

        except mysql.connector.Error as err:
            print(err)
        finally:
            if cursor is not None:
                cursor.close()
            if cnx is not None:
                cnx.close()

    return jsonify(result)


@app.route("/register", methods=["POST"])
def register():
    result = {
        "status": "error",
        "result": "An error occurred while processing your request",
    }

    if request.method == "POST":
        response = request.get_json()
        name = response["name"]
        role = response["role"]
        company = response["company"]
        email = response["email"]
        phone = response["phone"]
        password = response["password"]

        cnx = None
        cursor = None

        try:
            cnx = cnxpool.get_connection()
            cursor = cnx.cursor()
            query = "SELECT * FROM user_info WHERE email = %s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()
            cnx.commit()

            if user:
                result = {
                    "status": "error",
                    "result": "User already present. Please login",
                }
            else:
                verification_code = serializer.dumps(email)
                encrypted_password = sha256_crypt.hash(password)
                insert_query = "INSERT INTO user_info (id, name, role, company, email, phone, password, verificationCode) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(
                    insert_query,
                    (
                        str(uuid.uuid4()),
                        name,
                        role,
                        company,
                        email,
                        phone,
                        encrypted_password,
                        verification_code,
                    ),
                )
                cnx.commit()

                email_data = generate_user_verified_email(
                    email_to=email, user_name=name, token=verification_code)
                send_email(
                    email_to=email,
                    subject=email_data.subject,
                    html_content=email_data.html_content,
                )

                result = {
                    "status": "success",
                    "result": "Verification email has been sent to your email",
                }

        except mysql.connector.Error as err:
            print(err)

        finally:
            if cursor is not None:
                cursor.close()
            if cnx is not None:
                cnx.close()

    return jsonify(result)


@app.route("/verify_email/<token>")
def verify_email(token):
    result = {}
    cnx = None
    cursor = None

    try:
        email = serializer.loads(token, max_age=3600)

        cnx = cnxpool.get_connection()
        cursor = cnx.cursor()
        cursor.execute(
            "UPDATE user_info SET verified = TRUE WHERE email = %s", (email,)
        )
        cnx.commit()

        result = {"status": "success", "result": "Email confirmed!"}

    except mysql.connector.Error as err:
        print(err)

    except SignatureExpired:
        result = {
            "status": "error",
            "result": "The confirmation link is invalid or has expired",
        }

    finally:
        if cursor is not None:
            cursor.close()
        if cnx is not None:
            cnx.close()

    return jsonify(result)


@app.route("/get_customer_data", methods=["GET"])
@jwt_required()
def get_customer_data():
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({"status": "error", "result": "User not authorized"})

    result = {
        "status": "error",
        "result": "An error occurred while processing your request",
    }
    cnx = None
    cursor = None

    try:
        cnx = cnxpool.get_connection()
        cursor = cnx.cursor()
        query = "SELECT availableCredits, totalCredits, totalAmount FROM user_info WHERE role = 'customer' and email = %s"
        cursor.execute(query, (current_user,))
        user = cursor.fetchone()
        cnx.commit()

        if user is not None:
            availableCredits, totalCredits, totalAmount = user

            result = {
                "status": "success",
                "result": {
                    "availableCredits": availableCredits,
                    "totalCredits": totalCredits,
                    "usedCredits": totalCredits - availableCredits,
                    "invoiceExtracted": (totalCredits - availableCredits)
                    / credits_per_page,
                    "remainingInvoices": availableCredits / credits_per_page,
                    "totalAmount": totalAmount,
                },
            }
        else:
            result = {"status": "error",
                      "result": "Email not found. Please register"}

    except mysql.connector.Error as err:
        print(err)

    finally:
        if cursor is not None:
            cursor.close()
        if cnx is not None:
            cnx.close()

    return jsonify(result)


@app.route("/update_password", methods=["POST"])
@jwt_required()
def update_password():
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({"status": "error", "result": "User not authorized"})

    result = {
        "status": "error",
        "result": "An error occurred while processing your request",
    }

    if request.method == "POST":
        response = request.get_json()
        old_password = response["oldPassword"]
        new_password = response["newPassword"]

        cnx = None
        cursor = None

        try:
            cnx = cnxpool.get_connection()
            cursor = cnx.cursor()
            query = "SELECT password FROM user_info WHERE email = %s"
            cursor.execute(query, (current_user,))
            user = cursor.fetchone()
            cnx.commit()

            if user is not None:
                stored_password = user[0]

                if sha256_crypt.verify(old_password, stored_password):
                    encrypted_password = sha256_crypt.hash(new_password)
                    cursor.execute(
                        "UPDATE user_info SET password = %s WHERE email = %s",
                        (encrypted_password, current_user),
                    )
                    cnx.commit()
                    result = {
                        "status": "success",
                        "result": "Password updated successfully",
                    }
                else:
                    result = {"status": "error",
                              "result": "Wrong password entered"}
            else:
                result = {"status": "error", "result": "User not found!"}

        except mysql.connector.Error as err:
            print(err)

        finally:
            if cursor is not None:
                cursor.close()
            if cnx is not None:
                cnx.close()

    return jsonify(result)


@app.route("/download_excel/<requestId>", methods=["GET"])
@jwt_required()
def download_excel(requestId):
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({"status": "error", "result": "User not authorized"})

    data = []
    request_dir = os.path.join(upload_dir, str(requestId))

    for filename in sorted(os.listdir(request_dir)):
        if filename.endswith(".json"):
            with open(os.path.join(request_dir, filename), "r") as f:
                json_data = json.load(f)
                data.append(json_data)

    if data:
        serial_no = 1
        df = pd.DataFrame(columns=["SL. NO"] + itags + ["FILENAME"])

        for invoice in data:
            entities = invoice["entities"]
            max_items = len(entities[items_itags[0]])

            invoice_data = {}

            for tag in itags:
                if tag in items_itags:
                    invoice_data[tag] = [ent["value"] for ent in entities[tag]]
                elif tag in other_itags:
                    invoice_data[tag] = [entities[tag]["value"]] * max_items

            invoice_df = pd.DataFrame(invoice_data, columns=itags)
            invoice_df.insert(0, "SL. NO", serial_no)
            invoice_df.insert(len(itags), "FILENAME", invoice["filename"])

            serial_no += 1
            df = pd.concat([df, invoice_df], ignore_index=True)

        mem = io.BytesIO()
        with pd.ExcelWriter(mem, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        mem.seek(0)

        return send_file(mem, download_name="entities.xlsx", as_attachment=True)

    return jsonify({"Error": "Request has expired"})


@app.route("/download_json/<requestId>", methods=["GET"])
@jwt_required()
def download_json(requestId):
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({"status": "error", "result": "User not authorized"})

    data = []
    request_dir = os.path.join(upload_dir, str(requestId))

    for filename in sorted(os.listdir(request_dir)):
        if filename.endswith(".json"):
            with open(os.path.join(request_dir, filename), "r") as f:
                json_data = json.load(f)
                for tag in itags:
                    if tag in items_itags:
                        json_data["entities"][tag] = [
                            item["value"] for item in json_data["entities"][tag]
                        ]
                    elif tag in other_itags:
                        json_data["entities"][tag] = json_data["entities"][tag]["value"]
                data.append(json_data)

    if data:
        mem = io.BytesIO()
        json_data = json.dumps(data)
        mem.write(json_data.encode())
        mem.seek(0)
        return send_file(mem, download_name="entities.json", as_attachment=True)

    return jsonify({"Error": "Request has expired"})


@app.route("/init_upload", methods=["POST"])
@jwt_required()
def initialize_upload():
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({"status": "error", "result": "User not authorized"})

    cnx = None
    cursor = None

    try:
        total_images = int(request.get_json()["total_images"])
        if not total_images or total_images <= 0:
            return jsonify({"message": "Total images must be greater than zero"}), 400

        cnx = cnxpool.get_connection()
        cursor = cnx.cursor()
        cursor.execute(
            "SELECT id, availableCredits FROM user_info WHERE email = %s",
            (current_user,),
        )
        user = cursor.fetchone()
        cnx.commit()

        userId, available_credits = user

        if (available_credits >= credits_per_page) and (
            available_credits / credits_per_page
        ) >= total_images:
            pass
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "result": "Not enough credits to process invoices",
                    }
                ),
                400,
            )

        cursor.execute(
            "INSERT INTO request_info (userId, totalImages) VALUES (%s, %s)",
            (userId, total_images),
        )
        request_id = cursor.lastrowid
        cnx.commit()

        request_dir = os.path.join(upload_dir, str(request_id))
        os.makedirs(request_dir, exist_ok=True)

        return jsonify({"request_id": request_id})

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if cnx is not None:
            cnx.close()


@app.route("/upload_invoice", methods=["POST"])
@jwt_required()
def upload_images():
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({"status": "error", "result": "User not authorized"})

    cnx = None
    cursor = None

    try:
        request_id = request.form["request_id"]

        cnx = cnxpool.get_connection()
        cursor = cnx.cursor()
        cursor.execute(
            "SELECT userId, status, totalImages, imagesUploaded FROM request_info WHERE id = %s",
            (request_id,),
        )
        request_info = cursor.fetchone()
        cnx.commit()

        user_id, status, total_images, images_uploaded = request_info

        if not request_info or status != InvoiceStatus.UPLOADING:
            return jsonify({"message": "Invalid request ID"}), 400

        request_dir = os.path.join(upload_dir, str(request_id))
        images = request.files.getlist("images")

        for image in images:
            image.save(os.path.join(request_dir, image.filename))

        new_images_uploaded = images_uploaded + len(images)
        cursor.execute(
            "UPDATE request_info SET imagesUploaded = %s, updatedAt = NOW() WHERE id = %s",
            (new_images_uploaded, request_id),
        )
        cnx.commit()

        if new_images_uploaded == total_images:
            cursor.execute(
                "UPDATE request_info SET status = %s WHERE id = %s",
                (InvoiceStatus.UPLOADED, request_id),
            )
            cnx.commit()

            process_request.delay(request_id, user_id)

        return jsonify({"message": "Upload successful"})
    except Exception as e:
        print(e)
        cursor.execute(
            "UPDATE request_info SET status = %s WHERE id = %s",
            (InvoiceStatus.FAILURE, request_id),
        )
        cnx.commit()
        return jsonify({"error": str(e)})

    finally:
        if cursor is not None:
            cursor.close()
        if cnx is not None:
            cnx.close()


@app.route("/get_customers", methods=["GET"])
@jwt_required()
def get_customers():
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({"status": "error", "result": "User not authorized"})

    cnx = None
    cursor = None

    try:
        cnx = cnxpool.get_connection()
        cursor = cnx.cursor()
        query = "SELECT id, name, company, email, phone, verified, availableCredits, totalCredits, totalAmount, createdAt FROM user_info WHERE role = 'customer'"
        cursor.execute(query)
        customers = cursor.fetchall()
        cnx.commit()

        result = [
            dict(zip([column[0] for column in cursor.description], row))
            for row in customers
        ]

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        if cursor is not None:
            cursor.close()
        if cnx is not None:
            cnx.close()


@app.route("/credits_history/<user_id>", methods=["GET"])
@jwt_required()
def get_credits_history(user_id):
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({"status": "error", "result": "User not authorized"})

    cnx = None
    cursor = None

    try:
        cnx = cnxpool.get_connection()
        cursor = cnx.cursor()
        query = "SELECT userId, creditsBought, amountPaid, paymentStatus, addedBy, paymentDate, createdAt FROM credits WHERE userId = %s"
        cursor.execute(query, (user_id,))
        credits_history = cursor.fetchall()
        cnx.commit()

        result = []
        for row in credits_history:
            result.append(
                {
                    "userId": row[0],
                    "creditsBought": row[1],
                    "amountPaid": float(row[2]),
                    "paymentStatus": bool(row[3]),
                    "addedBy": row[4],
                    "paymentDate": row[5].isoformat() if row[5] else None,
                    "createdDate": row[6],
                }
            )

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        if cursor is not None:
            cursor.close()
        if cnx is not None:
            cnx.close()


@app.route("/dashboard_stats", methods=["GET"])
@jwt_required()
def get_dashboard_stats():
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({"status": "error", "result": "User not authorized"})

    cnx = None
    cursor = None

    try:
        cnx = cnxpool.get_connection()
        cursor = cnx.cursor(dictionary=True)
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
        cnx.commit()

        query = "SELECT totalCustomers, totalCredits, usedCredits, totalInvoiceExtracted, totalAmount FROM dashboard_stats WHERE lockId = 1"
        cursor.execute(query)
        credits_history = cursor.fetchone()
        cnx.commit()

        return jsonify(credits_history)

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        if cursor is not None:
            cursor.close()
        if cnx is not None:
            cnx.close()


@app.route("/add_credits", methods=["POST"])
@jwt_required()
def add_credits():
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({"status": "error", "result": "User not authorized"})

    result = {}
    cnx = None
    cursor = None

    try:
        cnx = cnxpool.get_connection()
        cursor = cnx.cursor()
        start_time = time.time()

        while cnx.in_transaction:
            if time.time() - start_time > 10:
                raise Exception("Transaction is taking too long!")
            time.sleep(0.1)

        cnx.start_transaction()

        response = request.get_json()
        userId = response["userId"]
        credits = int(response["credits"])
        addedBy = "admin"

        amountPaid = credits * credits_value
        paymentDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query = "INSERT INTO credits(userId, creditsBought, amountPaid, paymentStatus, addedBy, paymentDate) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(
            query, (userId, credits, amountPaid, 1, addedBy, paymentDate))

        update_user_info = "UPDATE user_info SET availableCredits = availableCredits + %s, totalCredits = totalCredits + %s, totalAmount = totalAmount + %s WHERE id = %s"
        cursor.execute(update_user_info,
                       (credits, credits, amountPaid, userId))

        update_dashboard_stats = "UPDATE dashboard_stats SET totalCredits = totalCredits + %s, totalAmount = totalAmount + %s WHERE lockId = 1"
        cursor.execute(update_dashboard_stats, (credits, amountPaid))

        cnx.commit()
        result = {"status": "success", "result": "Credits added successfully"}

    except Exception as err:
        print(err)
        cnx.rollback()
        result = {"status": "error", "result": "Failed to add credits"}

    finally:
        if cursor is not None:
            cursor.close()
        if cnx is not None:
            cnx.close()

    return jsonify(result)


@app.route("/invoice_requests", methods=["GET"])
@jwt_required()
def get_request_history():
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({"status": "error", "result": "User not authorized"})

    cnx = None
    cursor = None

    try:
        cnx = cnxpool.get_connection()
        cursor = cnx.cursor()
        query = "SELECT id, status, totalImages, createdAt, processedAt FROM request_info WHERE userId = (SELECT id FROM user_info WHERE email = %s) ORDER BY createdAt DESC"
        cursor.execute(query, (current_user,))
        result = cursor.fetchall()
        cnx.commit()

        if result:
            keys = ["id", "status", "totalImages", "createdAt", "processedAt"]
            result_dict = [dict(zip(keys, res)) for res in result]
            return jsonify(result_dict)
        else:
            return jsonify([])

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        if cursor is not None:
            cursor.close()
        if cnx is not None:
            cnx.close()


@app.route("/invoice_requests/<request_id>", methods=["DELETE"])
@jwt_required()
def delete_request(request_id):
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({"status": "error", "result": "User not authorized"})

    cnx = None
    cursor = None

    try:
        cnx = cnxpool.get_connection()
        cursor = cnx.cursor()
        query = "SELECT id FROM request_info WHERE id = %s"
        cursor.execute(query, (request_id,))
        result = cursor.fetchone()
        cnx.commit()

        if result:
            request_dir = os.path.join(upload_dir, request_id)
            if os.path.exists(request_dir):
                shutil.rmtree(request_dir)
            cursor.execute(
                "DELETE FROM request_info WHERE id = %s", (request_id,))
            cnx.commit()
        else:
            return jsonify({"status": "error", "result": "Invoice Request not found"})

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        if cursor is not None:
            cursor.close()
        if cnx is not None:
            cnx.close()

    return jsonify(
        {"status": "success", "result": "Invoice Request deleted successfully"}
    )


@app.route("/invoice_requests/<request_id>/data", methods=["GET"])
@jwt_required()
def get_all_image_urls(request_id):
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({"status": "error", "result": "User not authorized"})

    cnx = None
    cursor = None

    try:
        cnx = cnxpool.get_connection()
        cursor = cnx.cursor()
        query = "SELECT id FROM request_info WHERE id = %s"
        cursor.execute(query, (request_id,))
        result = cursor.fetchone()
        cnx.commit()

        if result:
            base_path = os.path.join(upload_dir, request_id)
            image_files = sorted(
                [f for f in os.listdir(base_path) if f.endswith(
                    (".png", ".jpg", ".jpeg"))]
            )

            image_urls = [f"{image}" for image in image_files]
            return jsonify({"files": image_urls})
        else:
            return jsonify({"status": "error", "result": "Invoice Request not found"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if cnx is not None:
            cnx.close()


@app.route("/invoice_requests/file/<path:file_name>", methods=["GET"])
@jwt_required()
def serve_image(file_name):
    response = make_response(send_from_directory(
        app.static_folder, file_name))
    response.cache_control.max_age = timedelta(days=2).total_seconds()
    return response


@app.route("/invoice_requests/<request_id>/data/<image_name>", methods=["GET"])
@jwt_required()
def get_image_and_json_by_name(request_id, image_name):
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({"status": "error", "result": "User not authorized"})

    json_data = {}
    base_path = os.path.join(upload_dir, request_id)
    json_file = os.path.splitext(image_name)[0] + ".json"
    json_path = os.path.join(base_path, json_file)

    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            json_data = json.load(f)

    return jsonify(json_data)


@app.route("/invoice_requests/<request_id>/data", methods=["PUT"])
@jwt_required()
def update_json_by_name(request_id):
    current_user = get_jwt_identity()

    if current_user is None:
        return jsonify({"status": "error", "result": "User not authorized"})

    base_path = os.path.join(upload_dir, request_id)
    json_data = request.get_json()
    image_name = json_data["filename"]

    if not image_name:
        return jsonify({"message": "Bad request"}), 400

    json_path = os.path.join(
        base_path, os.path.splitext(image_name)[0] + ".json")

    if os.path.exists(json_path):
        with open(json_path, "w") as f:
            json.dump(json_data, f)
    else:
        return jsonify({"message": "Bad request"}), 400

    return jsonify({"status": "JSON data updated successfully"})


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "UP"}), 200


@app.route("/celery/process_invoice", methods=["POST"])
def process_invoice():
    input_file = request.get_json()["input_file"]

    if not input_file:
        return jsonify({"message": "Bad input"}), 400

    result = {"message": "An error occurred while processing your request"}

    try:
        pp_output_image = iee_pipeline.image_preprocessing(input_file)
        ocr_response, ocr_output = iee_pipeline.extract_text(pp_output_image)
        pp_txt_ouput = iee_pipeline.text_preprocessing(ocr_output)
        entities_output = iee_pipeline.extract_entities(pp_txt_ouput)
        items_output = iee_pipeline.extract_table_items(
            input_file, ocr_response)

        mapped_headings = iee_pipeline.table_extractor.map_table_columns(
            table=items_output, ner_output=entities_output
        )

        # Add missing entities
        result = {
            key: {
                "value": entities_output.get(key)[0] if entities_output.get(key) else ""
            }
            for key in itags
        }

        # Get table items for mapped headings
        if mapped_headings:
            indices = {
                tag: (
                    items_output[0].index(mapped_headings.get(tag))
                    if mapped_headings.get(tag)
                    and mapped_headings.get(tag) != "N.E.R.Default"
                    else None
                )
                for tag in items_itags
            }

            mapped_dict = {
                tag: [
                    (
                        {"value": items_output[i][indices[tag]]}
                        if indices[tag] is not None
                        else (
                            {"value": entities_output[tag][i - 1]}
                            if mapped_headings.get(tag) == "N.E.R.Default"
                            else {"value": ""}
                        )
                    )
                    for i in range(1, len(items_output))
                ]
                for tag in items_itags
            }

            result.update(mapped_dict)

        # Add items to output
        # result['items'] = items_output

    except Exception as err:
        print(err)
        return jsonify(result), 500

    return jsonify(result), 200


if __name__ == "__main__":
    if os.getenv("ENV") == "prod":
        app.run(host="0.0.0.0", port=5000)
    else:
        app.run(host="0.0.0.0", port=5000, debug=True)
