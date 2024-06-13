import os
import mysql.connector

# Connect to MySQL
dbconfig = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

cnxpool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="iee_pool", pool_size=32, **dbconfig
)
