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
    
    # ดึงข้อมูลจาก Steam (StoreID 1) จำนวน 60 เกม
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
        price_thb = current_price_usd * 36 

        # เงื่อนไข: ลด 70% ขึ้นไป หรือ ราคาต่ำกว่า 300 บาท
        if savings >= 70 or price_thb < 300:
            old_price = float(history.get(game_id, 999.99))
            if game_id not in history or current_price_usd < old_price:
                genre_text = get_detailed_genres(deal['title'])
                
                embed = discord.Embed(
                    title=f"🔥 {deal['title']}",
                    url=f"https://www.cheapshark.com/redirect?dealID={deal['dealID']}",
                    color=0xe74c3c if savings >= 85 else 0x3498db
                )
                embed.add_field(name="💰 ราคาไทย (ประมาณ)", value=f"**฿{price_thb:,.2f}**", inline=True)
                embed.add_field(name="📉 ส่วนลด", value=f"**{savings:.0f}%**", inline=True)
                embed.add_field(name="💵 ราคาเดิม", value=f"~~${deal['normalPrice']}~~", inline=True)
                embed.description = f"**แนวเกม:** `{genre_text}`\n**แพลตฟอร์ม:** `Steam` ✅"
                embed.set_image(url=deal['thumb'])
                embed.set_footer(text=f"ตรวจพบเมื่อ: {time_str} | LockOnFree")
                
                await channel.send(embed=embed)
                new_history[game_id] = current_price_usd
                sent_count += 1

    # ส่งรายงาน Status
    status_embed = discord.Embed(title="🤖 Sales Bot Status", color=0x2ecc71)
    status_msg = f"🔍 **รอบการทำงาน:** {time_str}\n📅 **วันที่:** {date_str}\n\n"
    status_msg += f"✅ **พบดีลใหม่ {sent_count} รายการ**" if sent_count > 0 else "✅ **ตรวจสอบแล้ว: ยังไม่มีดีลใหม่**"
    status_embed.description = status_msg
    await channel.send(embed=status_embed)

    save_history(new_history)
    await client.close()

if __name__ == "__main__":
    if TOKEN:
        client.run(TOKEN)
