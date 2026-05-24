import sqlite3
import os
from common.constants import DB_PATH

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO dns_logs (uid, username, domain)
        VALUES (?, ?, ?)
    ''', (uid, username, domain))
    conn.commit()
    conn.close()
