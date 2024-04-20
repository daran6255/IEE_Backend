import os
from dotenv import load_dotenv
from passlib.hash import sha256_crypt
import mysql.connector

load_dotenv(override=True)

# Connect to MySQL
db = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

cursor = db.cursor()

users = [
    ("user1", "customer", "ABC", "demo1@example.com",
     "1234567890", sha256_crypt.hash("pass123"), "1dfdh456456", True, 250),
    ("user2", "customer", "XYZ", "demo2@example.com",
     "9876543210", sha256_crypt.hash("pass456"), "1dfgsghjyjytj", True, 120),
    ("user3", "customer", "taydens", "demo3@example.com",
     "7603903469", sha256_crypt.hash("pass789"), "1435353fhtrjrtjrt", True, 210)
]

credits = [
    [
        (100, 200.00, 1, "2023-03-01 12:00:00"),
        (50, 100.00, 1, "2023-04-01 12:00:00"),
        (200, 400.00, 1, "2023-05-01 12:00:00"),
        (300, 600.00, 0, "2023-06-01 12:00:00"),
        (300, 600.00, 1, "2023-06-01 12:00:00"),
        (100, 500.00, 1, "2023-07-01 12:00:00"),
        (150, 300.00, 1, "2023-08-01 12:00:00"),

    ],
    [
        (50, 100.00, 1, "2023-03-05 12:00:00"),
        (80, 160.00, 1, "2023-04-09 12:00:00"),
        (120, 240.00, 1, "2023-05-10 12:00:00"),
        (150, 300.00, 1, "2023-06-14 12:00:00"),
        (170, 340.00, 0, "2023-07-18 12:00:00"),
        (170, 340.00, 1, "2023-07-18 12:00:00"),
        (180, 360.00, 1, "2023-08-20 12:00:00"),
    ],
    [
        (60, 120.00, 1, "2023-03-11 12:00:00"),
        (70, 140.00, 0, "2023-04-24 12:00:00"),
        (70, 140.00, 1, "2023-04-24 12:00:00"),
        (110, 220.00, 1, "2023-05-20 12:00:00"),
        (115, 230.00, 1, "2023-06-07 12:00:00"),
        (130, 260.00, 1, "2023-07-16 12:00:00"),
        (175, 350.00, 1, "2023-08-25 12:00:00")
    ]
]

for i in range(len(users)):
    cursor.execute(
        "INSERT INTO user_info (name, role, company, email, phone, password, verificationCode, verified, availableCredits) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", users[i])
    user_id = cursor.lastrowid

    for credit in credits[i]:
        credit_record = (user_id,) + credit
        cursor.execute(
            "INSERT INTO credits (userId, creditsBought, amountPaid, paymentStatus, paymentDate) VALUES (%s, %s, %s, %s, %s)", credit_record)

db.commit()
cursor.close()
db.close()
