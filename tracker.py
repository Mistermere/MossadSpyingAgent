import time
import sqlite3
import win32gui
import win32process
import psutil
from datetime import datetime
import os

BROWSERS = ["brave.exe", "chrome.exe", "msedge.exe", "firefox.exe"]
DB_PATH = r"C:\Users\User\tabwise_usage.db"\

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS app_usage (
        app_name TEXT, window_title TEXT, start_time TEXT, duration_seconds INTEGER
    )
''')
conn.commit()

def get_active_window_info():
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd: return None, None
    window_title = win32gui.GetWindowText(hwnd)
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    try: process_name = psutil.Process(pid).name().lower()
    except psutil.NoSuchProcess: process_name = "unknown"
    return process_name, window_title

def clean_title(app_name, title):
    if app_name in BROWSERS:
        title = title.replace(" - Brave", "").replace(" - Google Chrome", "").replace(" - Microsoft Edge", "").replace(" - Firefox", "")
        if "YouTube Music" in title: return "YouTube Music"
        elif "YouTube" in title: return "YouTube"
        elif "DeepSeek" in title: return "DeepSeek"
        elif "GitHub" in title: return "GitHub"
        elif "Reddit" in title: return "Reddit"
        if not title or title == "New Tab": return "Browser"
        return title
    return app_name

current_app, current_title, start_time = None, None, None

while True:
    try:
        app_name, window_title = get_active_window_info()
        if not app_name:
            time.sleep(1)
            continue

        cleaned_title = clean_title(app_name, window_title)

        if cleaned_title != current_title:
            if current_title is not None and start_time is not None:
                duration = int(time.time() - start_time)
                if duration > 1:
                    formatted_time = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute("INSERT INTO app_usage (app_name, window_title, start_time, duration_seconds) VALUES (?, ?, ?, ?)", 
                                   (current_app, current_title, formatted_time, duration))
                    conn.commit()
            
            current_app = app_name
            current_title = cleaned_title
            start_time = time.time()
            
        time.sleep(1) 
    except Exception:
        time.sleep(1)