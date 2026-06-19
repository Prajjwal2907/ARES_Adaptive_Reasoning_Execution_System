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


def _is_path_allowed(path, allowed_paths):
    abs_path = os.path.abspath(path)
    for dir in allowed_paths:
        if os.path.commonpath([abs_path,dir]) == dir:
            return True
    return False

def _open_application(app_name):
    try:
        for app_path_name in local_path.APP_PATHS:
            if app_name.lower() in app_path_name:
                app_path = local_path.APP_PATHS[app_path_name]
                if "!" in app_path:
                    subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{app_path}"])
                else:
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

_actions = {
    "open_application":_open_application,
    
}

_action_declarations = [types.FunctionDeclaration(name="open_application", 
                                                  description="Opens an application on the user's PC. Use this when the user asks to open, launch, or start any application or program.", 
                                                  parameters=types.Schema(
                                                      type=types.Type.OBJECT,
                                                      properties={
                                                          "app_name":types.Schema(
                                                              type=types.Type.STRING,
                                                              description="The name of the application to open, exactly as it appears in the Start Menu or Desktop, without the file extension."
                                                              )
                                                      },
                                                      required=["app_name"]
                                                      )   
                                                )
                        ]

ares_tools = types.Tool(function_declarations=_action_declarations)

def execute_action(action_name, parameters):
    if action_name in permissions:
        if permissions[action_name] == 'BLOCKED':
            log_action(action_name, parameters, permissions[action_name], 'BLOCKED', None)
            return "Action blocked..."
        elif permissions[action_name] == 'SENSITIVE':
            confirmation = input(f"Requesting permission to {action_name} with parameters {parameters}?(yes/no)")
            if confirmation.lower() == 'yes':
                func = _actions.get(action_name)
                result = func(**parameters)
                log_action(action_name, parameters, permissions[action_name], result[0], result[1])
                return result[1]
            else:
                log_action(action_name, parameters, permissions[action_name], 'DENIED', None)
                return "Permission denied..."
        elif permissions[action_name] == 'SAFE':
            func = _actions.get(action_name)
            result = func(**parameters)
            log_action(action_name, parameters, permissions[action_name], result[0], result[1])
            return result[1]
    else:
        return f"Cannot do {action_name}"
    
