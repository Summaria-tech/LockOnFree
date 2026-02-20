import discord
import requests
import json
import os
from datetime import datetime, timedelta

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_SALE_CHANNEL_ID'))
HISTORY_FILE = "sale_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def get_sales():
    url = "https://www.cheapshark.com/api/1.0/deals?upperPrice=15&onSale=1&pageSize=10"
    try:
        return requests.get(url).json()
    except: return []

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        await client.close()
        return

    history = load_history()
    deals = get_sales()
    new_history = history.copy()
    
    now_th = datetime.utcnow() + timedelta(hours=7)
    time_str = now_th.strftime("%H:%M")
    
    # --- ระบบแบ่งประเภทเกม ---
    categorized_games = {
        "🔥 ดีลลดหนัก (80% ขึ้นไป)": [],
        "📉 ดีลใหม่น่าสนใจ": []
    }

    for deal in deals:
        game_id = deal['gameID']
        current_price = float(deal['salePrice'])
        savings = float(deal['savings'])
        old_price = float(history.get(game_id, 999.99))

        if game_id not in history or current_price < old_price:
            # แยกเข้ากลุ่มตาม % ส่วนลด
            if savings >= 80:
                categorized_games["🔥 ดีลลดหนัก (80% ขึ้นไป)"].append(deal)
            else:
                categorized_games["📉 ดีลใหม่น่าสนใจ"].append(deal)
            new_history[game_id] = current_price

    # --- ส่วนการส่ง Embed ---
    sent_any = False
    for category, games in categorized_games.items():
        for game in games:
            sent_any = True
            embed = discord.Embed(
                title=game['title'],
                description=f"**หมวดหมู่:** {category}\nลดราคาพิเศษบน Steam/Epic",
                color=0xFF4500 if "ลดหนัก" in category else 0x3498
