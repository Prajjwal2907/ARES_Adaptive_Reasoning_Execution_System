import time
import os, subprocess, pywinauto
import shutil, pyautogui, pyperclip
import sqlite3, json
import config
import datetime
from google.genai import types
from assets.local import local_path
from .client import client
from pathlib import Path
from docx import Document
from openpyxl import Workbook
from pptx import Presentation

permissions = {
    "open_application":"SAFE",
    "focus_application":"SAFE",
    "resize_application":"SAFE",
    "close_application":"SENSITIVE",
    "browser_new_tab":"SAFE",
    "browser_close_tab":"SENSITIVE",
    "search_browser":"SENSITIVE"
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


# App Control
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

def _focus_application(app_name):
    try:
        app = pywinauto.Application(backend = "win32").connect(title_re = f".*{app_name}.*",found_index=0)
        app.top_window().set_focus()
        return ("success", f"{app_name} focused.")
    except Exception as e:
        return ("fail", str(e))
    
def _resize_application(app_name, action):
    try:
        app = pywinauto.Application(backend = "win32").connect(title_re = f".*{app_name}.*",found_index=0)
        if action.lower() == "minimize":
            app.top_window().minimize()
            return ("success", f"{app_name} minimized.")

        elif action.lower() == "maximize":
            app.top_window().maximize()
            return ("success", f"{app_name} maximized.")
        
        elif action.lower() == "left":
            screen_width, screen_height = pyautogui.size()
            app.top_window().move_window(x=0, y=0, width=screen_width//2, height=screen_height)
            return ("success", f"{app_name} moved.")
        
        elif action.lower() == "right":
            screen_width, screen_height = pyautogui.size()
            app.top_window().move_window(x=screen_width//2, y=0, width=screen_width//2, height=screen_height)
            return ("success", f"{app_name} moved.")
        else:
            return ("fail", "invalid action")
    except Exception as e:
        return ("fail", str(e))

def _close_application(app_name):
    try:
        app = pywinauto.Application(backend = "win32").connect(title_re = f".*{app_name}.*",found_index=0)
        app.top_window().close()
        return ("success", f"{app_name} closed.")
    except Exception as e:
        return ("fail", str(e))

def _browser_new_tab():
    try:
        app = pywinauto.Application(backend="win32").connect(title_re=f".*{local_path.DEFAULT_BROWSER}.*", found_index=0)
        app.top_window().set_focus()
        pyautogui.hotkey('ctrl', 't')
        return ("success", "New tab opened.")
    except Exception as e:
        try:
            _open_application(local_path.DEFAULT_BROWSER)
            time.sleep(2)
            app = pywinauto.Application(backend="win32").connect(title_re=f".*{local_path.DEFAULT_BROWSER}.*", found_index=0)
            app.top_window().set_focus()
            pyautogui.hotkey('ctrl', 't')
            return ("success", "New tab opened.")
        except Exception as e2:
            return ("fail", str(e2))
    
def _browser_close_tab():
    try:
        app = pywinauto.Application(backend="win32").connect(title_re=f".*{local_path.DEFAULT_BROWSER}.*", found_index=0)
        app.top_window().set_focus()
        pyautogui.hotkey('ctrl', 'w')
        return ("success", "Tab closed.")
    except Exception as e:
        return ("fail", str(e))
    
def _search_browser(query):
    try:
        _browser_new_tab()
        app = pywinauto.Application(backend="win32").connect(title_re=f".*{local_path.DEFAULT_BROWSER}.*", found_index=0)
        app.top_window().set_focus()
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.5)
        pyperclip.copy(query) 
        pyautogui.hotkey('ctrl', 'v')
        pyautogui.press('enter')
        return ("success", "Navigated successfully.")
    except Exception as e:
        return ("fail", str(e))
    
# def _create_file(filename, content):

_actions = {
    "open_application":_open_application,
    "focus_application":_focus_application,
    "resize_application":_resize_application,
    "close_application":_close_application,
    "browser_new_tab":_browser_new_tab,
    "browser_close_tab":_browser_close_tab,
    "search_browser":_search_browser
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
                                                ),
                        types.FunctionDeclaration(name="focus_application",
                                                  description="Brings an already open application window to the foreground. Use this when the user asks to focus, switch to, bring up, or show an application that is already running.",
                                                  parameters=types.Schema(
                                                      type=types.Type.OBJECT,
                                                      properties={
                                                          "app_name": types.Schema(
                                                              type=types.Type.STRING,
                                                              description="The name of the application to focus, as it would appear in the window title bar."
                                                          )
                                                      },
                                                      required=["app_name"]
                                                    )
                                                ),
                        types.FunctionDeclaration(name="resize_application",
                                                  description="Minimizes, maximizes, or snaps an open application window to the left or right half of the screen. Use this when the user asks to minimize, maximize, snap, or move an application to a side of the screen.",
                                                  parameters=types.Schema(
                                                      type=types.Type.OBJECT,
                                                      properties={
                                                          "app_name": types.Schema(
                                                              type=types.Type.STRING,
                                                              description="The name of the application as it appears in the window title bar."
                                                          ),
                                                          "action": types.Schema(
                                                              type=types.Type.STRING,
                                                              description="The action to perform. Must be exactly one of: 'minimize', 'maximize', 'left', 'right'."
                                                          )
                                                      },
                                                      required=["app_name", "action"]
                                                    )
                                                ),
                        types.FunctionDeclaration(name="close_application",
                                                  description="Closes an open application window. Use this when the user asks to close, quit, or exit an application.",
                                                  parameters=types.Schema(
                                                      type=types.Type.OBJECT,
                                                      properties={
                                                          "app_name": types.Schema(
                                                              type=types.Type.STRING,
                                                              description="The name of the application to close, as it appears in the window title bar."
                                                          )
                                                      },
                                                      required=["app_name"]
                                                  )
                                                ),
                        types.FunctionDeclaration(name="browser_new_tab",
                                                  description="Opens a new tab in the browser. Use this when the user asks to open a new tab.",
                                                  parameters=types.Schema(
                                                      type=types.Type.OBJECT,
                                                      properties={}
                                                  )
                                                ),
                        types.FunctionDeclaration(
                                                  name="browser_close_tab",
                                                  description="Closes the current tab in the browser. Use this when the user asks to close the current tab.",
                                                  parameters=types.Schema(
                                                      type=types.Type.OBJECT,
                                                      properties={}
                                                  )
                                                ),
                        types.FunctionDeclaration(name="search_browser",
                                                  description="Opens a new browser tab and navigates to a URL or performs a search. Use this when the user asks to search for something, go to a website, or open a URL.",
                                                  parameters=types.Schema(
                                                      type=types.Type.OBJECT,
                                                      properties={
                                                          "query": types.Schema(
                                                              type=types.Type.STRING,
                                                              description="The URL to navigate to or the search query to look up. Can be a full URL like 'https://github.com' or plain text like 'Python tutorials'."
                                                          )
                                                      },
                                                      required=["query"]
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
    
