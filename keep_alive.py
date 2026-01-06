from flask import Flask
from threading import Thread
import logging

app = Flask('')

# কনসোল ক্লিন রাখার জন্য ফ্লাস্কের অটোমেটিক লগ বন্ধ করা হয়েছে
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def home():
    return {
        "status": "Alive",
        "message": "Swygen Ultra Enhancer Bot is Running Smoothly!",
        "service": "24/7 Online"
    }

def run():
    try:
        # Port 8080 সব সার্ভারের জন্য স্ট্যান্ডার্ড
        app.run(host='0.0.0.0', port=8080)
    except Exception as e:
        print(f"Server Error: {e}")

def keep_alive():
    t = Thread(target=run)
    t.daemon = True # মেইন প্রোগ্রাম বন্ধ হলে এই থ্রেডও বন্ধ হবে
    t.start()
