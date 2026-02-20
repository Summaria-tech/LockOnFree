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

STORES = {
    "1": "Steam", "2": "GamersGate", "3": "GreenManGaming", "7": "GOG",
    "11": "Humble Store", "25": "Epic Games Store", "31": "Blizzard Shop"
}

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

def get_sales():
    url = "https://www.cheapshark.com/api/1.0/deals?upperPrice=15&onSale=1&pageSize=10"
    try: return requests.get(url).json()
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
    date_str = now_th.strftime("%d/%m/%Y")
    
    categorized_games = {"🔥 ดีลลดหนัก (80% ขึ้นไป)": [], "📉 ดีลใหม่น่าสนใจ": []}
    sent_count = 0
    free_games_skipped = 0

    for deal in deals:
        game_id = deal['gameID']
        current_price = float(deal['salePrice'])
        
        # กรองเกมฟรี
        if current_price == 0:
            free_games_skipped += 1
            continue 

        old_price = float(history.get(game_id, 999.99))

        # ส่งเฉพาะเกมใหม่หรือเกมที่ลดราคาลงกว่าเดิม
        if game_id not in history or current_price < old_price:
            deal['genre'] = get_detailed_genres(deal['title'])
            deal['platform'] = STORES.get(deal['storeID'], "PC Store")
            
            if float(deal['savings']) >= 80:
                categorized_games["🔥 ดีลลดหนัก (80% ขึ้นไป)"].append(deal)
            else:
                categorized_games["📉 ดีลใหม่น่าสนใจ"].append(deal)
            
            new_history[game_id] = current_price
            sent_count += 1

    # ส่งดีลใหม่ (ถ้ามี)
    for category, games in categorized_games.items():
        for game in games:
            desc_content = f"**สถานะ:** {category}\n**แพลตฟอร์ม:** {game['platform']}\n**แนวเกม:** {game['genre']}"
            embed = discord.Embed(
                title=game['title'],
                description=desc_content,
                color=0xFF4500 if "ลดหนัก" in category else 0x3498db,
                url=f"https://www.cheapshark.com/redirect?dealID={game['dealID']}"
            )
            embed.add_field(name="💰 ราคาลดเหลือ", value=f"**${game['salePrice']}**", inline=True)
            embed.add_field(name="💵 ราคาปกติ", value=f"~~${game['normalPrice']}~~", inline=True)
            embed.add_field(name="📉 ส่วนลด", value=f"**{float(game['savings']):.0f}%**", inline=True)
            embed.set_image(url=game['thumb'])
            embed.set_footer(text=f"ตรวจพบเมื่อ: {time_str} | ข้อมูลจาก CheapShark")
            await channel.send(embed=embed)

    # --- ส่วนรายงาน Status (แก้ให้รันได้จริง) ---
    skipped_count = len(deals) - sent_count - free_games_skipped
    status_embed = discord.Embed(title="🤖 Bot Status: Online", color=0x2ecc71)
    
    msg = f"🔍 **ตรวจสอบรอบที่:** {time_str}\n📅 **วันที่:** {date_str}\n\n"
    if sent_count > 0:
        msg += f"✅ **พบดีลลดราคาใหม่ {sent_count} รายการ!**\n"
    else:
        msg += "✅ **ตรวจสอบแล้ว: ยังไม่มีดีลที่ถูกลงกว่าเดิม**\n"
    
    msg += f"🏠 **เฝ้าดูอยู่:** {skipped_count} เกม (ราคายังไม่ลดเพิ่ม)"
    
    status_embed.description = msg
    status_embed.set_footer(text="ระบบเฝ้าดูดีลลดราคาให้คุณตลอด 24 ชม.")
    await channel.send(embed=status_embed)

    save_history(new_history)
    await client.close()

client.run(TOKEN)
