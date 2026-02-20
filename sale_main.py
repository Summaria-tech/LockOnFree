import discord
import requests
import json
import os
from datetime import datetime, timedelta

# ดึงข้อมูลจาก GitHub Secrets
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_SALE_CHANNEL_ID')) # ใช้ ID ห้องใหม่
HISTORY_FILE = "sale_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                return json.load(f)
            except: return {}
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def get_best_deals():
    # ดึงดีลเด็ด 5 อันดับแรกที่ราคาต่ำกว่า $15 (ประมาณ 500 บาท)
    url = "https://www.cheapshark.com/api/1.0/deals?upperPrice=15&onSale=1&pageSize=5"
    try:
        response = requests.get(url)
        return response.json()
    except:
        return []

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    print(f"💰 Sale Bot: {client.user} Online")
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ หาห้องแชทไม่เจอ! เช็ค ID ใน Secrets อีกรอบนะครับ")
        await client.close()
        return

    history = load_history()
    deals = get_best_deals()
    new_history = history.copy()
    has_update = False

    # เวลาไทยสำหรับรายงานท้าย Embed
    now_th = datetime.utcnow() + timedelta(hours=7)
    time_str = now_th.strftime("%H:%M")

    for deal in deals:
        game_id = deal['gameID']
        current_price = float(deal['salePrice'])
        # ถ้าไม่มีในประวัติ ให้ตั้งราคาสูงๆ ไว้ก่อนเพื่อให้มันส่งครั้งแรก
        old_price = float(history.get(game_id, 999.99)) 

        # เงื่อนไข: ส่งเฉพาะเมื่อเป็นเกมใหม่ (ID ไม่ซ้ำ) หรือ ราคาลดลงกว่าเดิม
        if game_id not in history or current_price < old_price:
            has_update = True
            status_text = "🔥 ดีลใหม่แนะนำ!" if game_id not in history else "📉 ลดถูกลงกว่าเดิม!"
            
            embed = discord.Embed(
                title=f"{deal['title']}",
                description=f"**{status_text}**",
                color=0x2ecc71, # สีเขียว
                url=f"https://www.cheapshark.com/redirect?dealID={deal['dealID']}"
            )
            
            savings = float(deal['savings'])
            embed.add_field(name="ราคาปัจจุบัน", value=f"${current_price}", inline=True)
            embed.add_field(name="ราคาปกติ", value=f"${deal['normalPrice']}", inline=True)
            embed.add_field(name="ส่วนลด", value=f"{savings:.0f}%", inline=True)
            embed.set_thumbnail(url=deal['thumb'])
            embed.set_footer(text=f"เช็คราคาเมื่อ: {time_str} | ข้อมูลจาก CheapShark")
            
            await channel.send(embed=embed)
            new_history[game_id] = current_price # บันทึกราคาปัจจุบันลงประวัติ

    if not has_update:
        print("🏠 ไม่มีเกมลดราคาใหม่ หรือราคาเท่าเดิม")
        # ส่ง Status สั้นๆ เพื่อให้เรารู้ว่าบอททำงาน (Optional: ลบออกได้ถ้าไม่อยากให้ห้องรก)
        # await channel.send(f"✅ บอทเช็คราคาแล้ว: ยังไม่มีดีลใหม่ที่ถูกลง ({time_str})")

    save_history(new_history)
    await client.close()

client.run(TOKEN)
