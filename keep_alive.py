import time
import requests
import os
from threading import Thread
from datetime import datetime

RENDER_URL = "https://bot-dlg6.onrender.com"

def get_time():
    """الحصول على الوقت الحالي بتنسيق مناسب"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def keep_alive():
    ping_count = 0
    while True:
        try:
            ping_count += 1
            response = requests.get(RENDER_URL)
            if response.status_code == 200:
                print(f"✅ [{get_time()}] Ping #{ping_count} successful - Status: {response.status_code}")
            else:
                print(f"⚠️ [{get_time()}] Ping #{ping_count} warning - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ [{get_time()}] Ping #{ping_count} failed - Error: {str(e)}")
        
        # انتظار 5 دقائق
        time.sleep(300)

def start_keep_alive():
    print(f"🚀 [{get_time()}] Starting keep-alive service...")
    keep_alive_thread = Thread(target=keep_alive)
    keep_alive_thread.daemon = True
    keep_alive_thread.start()
    print(f"✨ [{get_time()}] Keep-alive service started successfully")
