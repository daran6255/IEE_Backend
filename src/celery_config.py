import os
import json
import time
import shutil
import requests
import redis
import mysql.connector
from flask import Flask
from celery import Celery
from celery.schedules import crontab
from contextlib import contextmanager
from datetime import datetime, timedelta

from src.db import dbconfig
from src.utility import InvoiceStatus, send_email, generate_request_processed_email


credits_per_page = int(os.getenv("CREDITS_PER_PAGE"))
redis_client = redis.Redis.from_url(os.getenv("CELERY_BROKER_URL"))
upload_dir = os.getenv("UPLOAD_DIR")


@contextmanager
def redis_lock(lock_name):
    """Yield 1 if specified lock_name is not already set in redis. Otherwise returns 0.
    Enables sort of lock functionality.
    """
    status = redis_client.set(lock_name, "lock", nx=True)
    try:
        yield status
    finally:
        redis_client.delete(lock_name)


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=os.getenv("CELERY_RESULT_BACKEND"),
        broker=os.getenv("CELERY_BROKER_URL"),
    )
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


app = Flask(__name__)
app.config.update(
    broker_url=os.getenv("CELERY_RESULT_BACKEND"),
    result_backend=os.getenv("CELERY_BROKER_URL"),
    broker_connection_retry_on_startup=True,
)
celery = make_celery(app)

PROCESS_TASK_LOCK_KEY = "process_request_lock"


@celery.task
def process_request(request_id, user_id):
    with redis_lock(PROCESS_TASK_LOCK_KEY) as acquired:
        if acquired:
            start_time = datetime.now()

            # Check for invoice process endpoint status
            while True:
                try:
                    response = requests.get("http://localhost:5000/health")
                    if response.status_code == 200:
                        break
                except requests.exceptions.ConnectionError:
                    time.sleep(5)

                if datetime.now() - start_time > timedelta(minutes=5):
                    print(
                        "Timeout: Flask server is not available. Exiting process request..."
                    )
                    return

            cnx = None
            cursor = None

            try:
                cnx = mysql.connector.connect(**dbconfig)
                cursor = cnx.cursor()
                cursor.execute(
                    "UPDATE request_info SET status = %s WHERE id = %s",
                    (InvoiceStatus.PROCESSING, request_id),
                )
                cnx.commit()

                request_dir = os.path.join(upload_dir, str(request_id))

                successful_extraction = 0

                for filename in os.listdir(request_dir):
                    file_name, file_ext = os.path.splitext(filename)

                    if not os.path.exists(
                        os.path.join(request_dir, file_name + ".json")
                    ):
                        input_file = os.path.join(request_dir, filename)
                        output_file = os.path.join(
                            request_dir, file_name + ".json")
                        result = {}

                        try:
                            response = requests.post(
                                "http://localhost:5000/celery/process_invoice",
                                json={"input_file": input_file},
                            )

                            entities = response.json()
                            if entities:
                                successful_extraction += 1
                            result = {"filename": filename,
                                      "entities": entities}

                        except Exception as e:
                            print(e)
                        finally:
                            with open(output_file, "w") as f:
                                json.dump(result, f)

                if successful_extraction > 0:
                    totalCreditsUsed = successful_extraction * credits_per_page

                    query = "UPDATE user_info SET availableCredits = availableCredits - %s WHERE id = %s"
                    cursor.execute(query, (totalCreditsUsed, user_id))

                    query = "UPDATE dashboard_stats SET usedCredits = usedCredits + %s, totalInvoiceExtracted = totalInvoiceExtracted + %s WHERE lockId = 1"
                    cursor.execute(
                        query, (totalCreditsUsed, successful_extraction))

                    cnx.commit()

                cursor.execute(
                    "UPDATE request_info SET status = %s, processedAt = NOW() WHERE id = %s",
                    (InvoiceStatus.SUCCESS, request_id),
                )
                cursor.execute(
                    "SELECT name, email FROM user_info WHERE id = %s", (user_id,))
                request = cursor.fetchone()
                cnx.commit()

                name, email = request

                # Send notification email after successfull processing
                email_data = generate_request_processed_email(
                    email_to=email, user_name=name, process_id=request_id)
                send_email(
                    email_to=email,
                    subject=email_data.subject,
                    html_content=email_data.html_content,
                )
            except Exception as e:
                cursor.execute(
                    "UPDATE request_info SET status = %s WHERE id = %s",
                    (InvoiceStatus.FAILURE, request_id),
                )
                cnx.commit()
            finally:
                if cursor is not None:
                    cursor.close()
                if cnx is not None:
                    cnx.close()


@celery.task
def check_and_trigger_process_request():
    with redis_lock(PROCESS_TASK_LOCK_KEY) as acquired:
        if acquired:
            cnx = None
            cursor = None

            try:
                cnx = mysql.connector.connect(**dbconfig)
                cursor = cnx.cursor()
                cursor.execute(
                    "SELECT id, userId FROM request_info WHERE status = %s ORDER BY id ASC LIMIT 1",
                    (InvoiceStatus.UPLOADED,),
                )
                request = cursor.fetchone()
                cnx.commit()

                if request:
                    request_id, user_id = request
                    process_request.delay(request_id, user_id)

            except Exception as e:
                print(e)

            finally:
                if cursor is not None:
                    cursor.close()
                if cnx is not None:
                    cnx.close()


@celery.task
def cleanup_old_records():
    cnx = None
    cursor = None
    retention_in_days = 5

    try:
        cnx = mysql.connector.connect(**dbconfig)
        cursor = cnx.cursor()
        cursor.execute(
            "SELECT id FROM request_info WHERE processedAt < NOW() - INTERVAL %s DAY",
            (retention_in_days,),
        )
        old_requests = cursor.fetchall()
        cnx.commit()

        for request in old_requests:
            request_dir = os.path.join(upload_dir, str(request[0]))

            if os.path.exists(request_dir):
                shutil.rmtree(request_dir)

            cursor.execute(
                "DELETE FROM request_info WHERE id = %s", (request[0],))
            cnx.commit()

    except Exception as e:
        print(e)

    finally:
        if cursor is not None:
            cursor.close()
        if cnx is not None:
            cnx.close()


@celery.task
def cleanup_incomplete_uploads():
    cnx = None
    cursor = None
    last_upload_mins = 30

    try:
        cnx = mysql.connector.connect(**dbconfig)
        cursor = cnx.cursor()
        cursor.execute(
            "SELECT id FROM request_info WHERE imagesUploaded < totalImages AND updatedAt < NOW() - INTERVAL %s MINUTE",
            (last_upload_mins,),
        )
        incomplete_requests = cursor.fetchall()

        for request in incomplete_requests:
            request_dir = os.path.join(upload_dir, str(request[0]))

            if os.path.exists(request_dir):
                shutil.rmtree(request_dir)

            cursor.execute(
                "DELETE FROM request_info WHERE id = %s", (request[0],))
            cnx.commit()

    except Exception as e:
        print(e)

    finally:
        if cursor is not None:
            cursor.close()
        if cnx is not None:
            cnx.close()


celery.conf.beat_schedule = {
    "cleanup-every-3-hour": {
        "task": "src.celery_config.cleanup_incomplete_uploads",
        "schedule": crontab(minute=0, hour="*/3"),
    },
    "cleanup-every-midnight": {
        "task": "src.celery_config.cleanup_old_records",
        "schedule": crontab(minute=0, hour=0),

    },
    "check-and-trigger-process-request-every-30-mins": {
        "task": "src.celery_config.check_and_trigger_process_request",
        "schedule": crontab(minute="*/30"),
    },
}

celery.conf.timezone = "UTC"
