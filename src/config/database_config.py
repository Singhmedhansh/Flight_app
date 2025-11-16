try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except Exception:
    mysql = None
    MYSQL_AVAILABLE = False
import sqlite3
from pathlib import Path

_DB_PATH = Path(__file__).resolve().parents[1] / 'data' / 'dev.db'

def _ensure_sqlite_db():
    # Ensure directory exists
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Create minimal tables used by the app if they don't exist
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Account (
            account_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS airline (
            code TEXT PRIMARY KEY,
            name TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS Flight (
            flight_no INTEGER PRIMARY KEY AUTOINCREMENT,
            airline_code TEXT,
            dep_port TEXT,
            arri_port TEXT,
            dep_time TEXT,
            arri_time TEXT,
            booked_seats INTEGER
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS FlightReservation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            flight_no INTEGER,
            creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def get_db_connection():
    if MYSQL_AVAILABLE:
        return mysql.connector.connect(
            host="localhost",
            user="educative",
            password="BMWfav3$",
            database="flight"
        )
    # Use a file-backed sqlite DB for dev/testing so tables persist between requests
    return _ensure_sqlite_db()