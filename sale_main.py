import discord
import requests
import json
import os
from datetime import datetime, timedelta

# ดึงข้อมูลจาก GitHub Secrets
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

def get_best_deals():
    # ดึงดีลเด็ด 5 อันดับแรก
    url = "https://www.cheapshark.com/api/1.0/deals?upperPrice=15&onSale=1&pageSize=5"
    try:
        response = requests.get(url)
        return response.json()
    except: return []

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    print(f"💰 Sale Bot Online")
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        await client.close()
        return

    history = load_history()
    deals = get_best_deals()
    new_history = history.copy()
    
    now_th = datetime.utcnow() + timedelta(hours=7)
    time_str = now_th.strftime("%d/%m/%Y %H:%M")

    for deal in deals:
        game_id = deal['gameID']
        current_price = float(deal['salePrice'])
        old_price = float(history.get(game_id, 999.99))

        # เงื่อนไขเดิม: ส่งเฉพาะเกมใหม่หรือราคาถูกลง
        if game_id not in history or current_price < old_price:
            status = "🔥 ดีลใหม่ที่น่าสนใจ!" if game_id not in history else "📉 ลดราคาถูกลงกว่าเดิม!"
            
            # สร้าง Embed ทรงเดียวกับบอทเกมฟรี
            embed = discord.Embed(
                title=deal['title'],
                description=f"**{status}**\nรีบคว้าก่อนหมดโปรโมชั่น!",
                color=0xFFA500, # สีส้มทองแบบพรีเมียม
                url=f"https://www.cheapshark.com/redirect?dealID={deal['dealID']}"
            )
            
            # แสดงราคาแบบเน้นๆ
            embed.add_field(name="💰 ราคาลดเหลือ", value=f"**${current_price}**", inline=True)
            embed.add_field(name="💵 ราคาปกติ", value=f"~~${deal['normalPrice']}~~", inline=True)
            embed.add_field(name="📉 ส่วนลด", value=f"**{float(deal['savings']):.0f}%**", inline=True)
            
            # ใส่รูปปกเกม
            embed.set_image(url=deal['thumb'])
            
            # ส่วนท้ายบอกเวลาตรวจสอบเหมือนบอทเกมฟรี
            embed.set_footer(text=f"ตรวจสอบเมื่อ: {time_str} | ข้อมูลโดย CheapShark")
            
            await channel.send(embed=embed)
            new_history[game_id] = current_price

    save_history(new_history)
    await client.close()

client.run(TOKEN)
