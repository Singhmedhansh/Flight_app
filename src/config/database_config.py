import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="educative",
        password="BMWfav3$",
        database="flight"
    )