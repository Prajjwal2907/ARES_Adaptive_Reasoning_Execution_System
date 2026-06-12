import os, subprocess
import sqlite3, json
import config
import datetime
from google.genai import types

permissions = {
    "open_application":"SAFE",
    "delete_file":"SENSITIVE"
}

conn = sqlite3.connect(config.ACTION_DB)

def init_action_log():
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS actions(
                id INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                action_name TEXT NOT NULL,
                parameters TEXT NOT NULL,
                permission_level TEXT NOT NULL,
                status TEXT NOT NULL,
                result_or_error TEXT
                )''')
    
    
    conn.commit()

def log_action(action_name, parameters, permission_level, status, result_or_error):
    timestamp = datetime.datetime.now().isoformat()
    param_json = json.dumps(parameters)

    cur = conn.cursor()
    cur.execute("INSERT INTO actions(timestamp, action_name, parameters, permission_level, status, result_or_error) VALUES(?,?,?,?,?,?)", (timestamp, action_name, param_json, permission_level, status, result_or_error))
    conn.commit()