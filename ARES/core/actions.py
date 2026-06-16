import os, subprocess
import shutil
import sqlite3, json
import config
import datetime
from google.genai import types
from assets.local import local_path
from .client import client
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

def _open_application(app_name):
    try:
        for app_path_name in local_path.APP_PATHS:
            if app_name.lower() in app_path_name:
                subprocess.Popen(local_path.APP_PATHS[app_path_name.lower()])
                return ("success", "Application opened!!")
        which_path = shutil.which(app_name.lower())
        if which_path:
            subprocess.Popen(which_path)
            return ("success", "Application opened!!")
        else:
            return ("fail", "App path not found!!")
        
    except Exception as e:
        return ("fail", "Error..." + str(e))
    
ares_tools = types.FunctionDeclaration.from_callable(client=client, callable=_open_application)

def execute_action(action_name, parameters):
    if action_name in permissions:
        if permissions[action_name] == 'BLOCKED':
            log_action(action_name, parameters, permissions[action_name], 'BLOCKED', None)
            return "Action blocked..."
        elif permissions[action_name] == 'SENSITIVE':
            confirmation = input(f"Requesting permission to {action_name} with parameters {parameters}?(yes/no)")
            if confirmation.lower() == 'yes':
                pass
            else:
                log_action(action_name, parameters, permissions[action_name], 'DENIED', None)
                return "Permission denied..."
    else:
        return f"Cannot do {action_name}"
    
