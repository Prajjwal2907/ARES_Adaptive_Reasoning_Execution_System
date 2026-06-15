import os
import win32com.client

APP_PATHS = {}

def build_app_path():
    win_client = win32com.client.Dispatch("WScript.Shell")

    user_search_path = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs")
    system_search_path = os.path.join(os.environ.get("PROGRAMDATA"), "Microsoft", "Windows", "Start Menu", "Programs")
    search_dirs = [user_search_path, system_search_path, os.path.join(os.environ.get("PUBLIC"), "Desktop"), os.path.join(os.path.expanduser("~"), "Desktop")]

    for search_path in search_dirs:
        for dirpath, dirnames, files in os.walk(search_path):
            for file in files:
                if file.endswith(".lnk") and "unins" not in file.lower():
                    file_path = os.path.join(dirpath, file)
                    exe_path = win_client.CreateShortcut(file_path).Targetpath
                    if exe_path and exe_path.lower().endswith(".exe"):
                        APP_PATHS[file[:-4].lower()] = exe_path

build_app_path()
