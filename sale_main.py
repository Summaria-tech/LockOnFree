import discord
import requests
import json
import os
import re
from datetime import datetime, timedelta

# ดึงข้อมูลจาก GitHub Secrets
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_SALE_CHANNEL_ID'))
RAWG_API_KEY = os.getenv('RAWG_API_KEY')
HISTORY_FILE = "sale_history.json"

def get_genres_from_rawg(game_name):
    if not RAWG_API_KEY: return []
    try:
        clean_name = re.sub(r'\(.*?\)|(?i)giveaway|free|download|pack', '', game_name)
        clean_name = re.sub(r'[^\w\s]', '', clean_name).strip()
        url = f"https://api.rawg.io/api/games?key={RAWG_API_KEY}&search={clean_name}&page_size=1"
        res = requests.get(url, timeout=10).json()
        if res.get('results'):
            return [g['name'] for g in res['results'][0].get('genres', [])]
    except: return []
    return []

def get_detailed_genres(game_title):
    rawg_genres = get_genres_from_rawg(game_title)
    backup_genres = []
    keywords = {
        "Action": ["action", "fighting", "hack", "jedi", "warrior"],
        "Adventure": ["adventure", "exploration", "survivor", "journey"],
        "RPG": ["rpg", "role-playing", "fantasy"],
        "Strategy": ["strategy", "tactic", "sim", "management"],
        "Shooting": ["shooting", "fps", "shooter", "sniper"],
        "Platformer": ["platformer", "2d", "retro"],
        "Indie": ["indie"]
    }
    title_lower = game_title.lower()
    for genre, keys in keywords.items():
        if any(key in title_lower for key in keys):
            backup_genres.append(genre)
    combined = rawg_genres + backup_genres
    final_list = []
    for item in combined:
        if item not in final_list: final_list.append(item)
    return " | ".join(final_list[:5]) if final_list else "Action | Adventure"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        await client.close()
        return

    history = load_history()
    new_history = history.copy()
    
    # ดึงข้อมูลดีลจาก Steam (StoreID=1) สูงสุด 60 เกม
    url = "https://www.cheapshark.com/api/1.0/deals?storeID=1&upperPrice=15&pageSize=60"
    try:
        res = requests.get(url)
        deals = res.json()
    except:
        await client.close()
        return

    now_th = datetime.utcnow() + timedelta(hours=7)
    time_str = now_th.strftime("%H:%M")
    date_str = now_th.strftime("%d/%m/%Y")
    
    sent_count = 0

    for deal in deals:
        game_id = deal['gameID']
        current_price_usd = float(deal['salePrice'])
        savings = float(deal['savings'])
        price_thb = current_price_usd * 35 # แปลงค่าเงินบาทคร่าวๆ

        # เงื่อนไข: ลด 70% ขึ้นไป OR ราคาไทยไม่เกิน 300 บาท
        if savings >= 70 or price_thb < 300:
            
            # เช็คว่าเคยส่งไปหรือยัง (หรือราคาถูกลงกว่าเดิม)
            old_price = float(history.get(game_id, 999.99))
            if game_id not in history or current_price_usd < old_price:
                
                genre_text = get_detailed_genres(deal['title'])
                
                # เลือกสีตามความแรงของดีล
                embed_color = 0xff0000 if savings >= 85 else 0x2ecc71
                
                embed = discord.Embed(
                    title=f"🎮 {deal['title']}",
                    url=f"https://www.cheapshark.com/redirect?dealID={deal['dealID']}",
                    color=embed_color
                )
                
                embed.add_field(name="💰 ราคาไทยโดยประมาณ", value=f"**฿{price_thb:,.2f}**", inline=True)
                embed.add_field(name="📉 ส่วนลด", value=f"**{savings:.0f}%**", inline=True)
                embed.add_field(name="💵 ราคาเดิม", value=f"~~${deal['normalPrice']}~~", inline=
