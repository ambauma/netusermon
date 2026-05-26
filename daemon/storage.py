import sqlite3
import os
from common import constants

def init_db():
    db_path = constants.DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dns_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            uid INTEGER,
            username TEXT,
            domain TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_dns_query(uid, username, domain):
    conn = sqlite3.connect(constants.DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO dns_logs (uid, username, domain)
        VALUES (?, ?, ?)
    ''', (uid, username, domain))
    conn.commit()
    conn.close()
