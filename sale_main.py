import discord
import requests
import json
import os
from datetime import datetime

# ตั้งค่าเบื้องต้น
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
HISTORY_FILE = "sale_history.json" # เปลี่ยนมาใช้ JSON เพื่อเก็บคู่ ID:Price

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

def get_best_deals():
    # ดึงดีลที่คุ้มที่สุด (Rating 9/10 ขึ้นไป) จาก CheapShark
    url = "https://www.cheapshark.com/api/1.0/deals?upperPrice=15&onSale=1&pageSize=5"
    response = requests.get(url)
    return response.json()

# ... (ส่วนส่ง Discord Embed จะคล้ายของเดิมแต่เพิ่มการโชว์ % ส่วนลด)
