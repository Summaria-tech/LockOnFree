import requests
import os
from bs4 import BeautifulSoup

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
DB_FILE = 'sent_games.txt'

def get_steam_data(url):
    """ขูดข้อมูลแนวเกมและรูปภาพจาก Steam"""
    data = {"genres": None, "image": None}
    if "steampowered.com" not in url: return data
    try:
        # ใช้ Cookie ภาษาไทยเพื่อให้ได้ Tags ภาษาไทย
        headers = {'User-Agent': 'Mozilla/5.0', 'Cookie': 'birthtime=283993201; steamCountry=TH'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # ดึง Tags แนวเกม
            tags = [tag.get_text().strip() for tag in soup.find_all('a', {'class': 'app_tag'})[:5]]
            if tags: data["genres"] = ", ".join(tags)
            # ดึงรูปภาพโปรไฟล์ (ใช้รูป Header ขนาดใหญ่)
            img_tag = soup.find('img', {'class': 'game_header_image_full'})
            if img_tag: data["image"] = img_tag['src']
    except: pass
    return data

def send_to_discord(game):
    steam_data = get_steam_data(game['open_giveaway_url'])
    
    # กำหนดแนวเกม: ถ้าขูดจาก Steam ได้ให้ใช้ Steam ถ้าไม่ได้ให้ใช้ระบบเดิม
    genre_display = steam_data["genres"] if steam_data["genres"] else f"อื่นๆ ({game['type']})"
    
    # กำหนดรูปภาพ: ใช้รูปจาก Steam ถ้ามี (เพราะชัดกว่า)
    img_url = steam_data["image"] if steam_data["image"] else game.get('thumbnail', '')

    payload = {
        "embeds": [{
            "title": f"🎮 {game['title']}",
            "url": game['open_giveaway_url'],
            "color": 1752220,
            "thumbnail": {"url": img_url}, # รูปโปรไฟล์เล็กด้านข้าง
            "fields": [
                {"name": "📂 แนวเกม", "value": f"`{genre_display}`", "inline": False},
                {"name": "💻 แพลตฟอร์ม", "value": f"**{game['platforms']}**", "inline": True},
                {"name": "💰 มูลค่า", "value": f"~~{game['worth']}~~ **FREE**", "inline": True}
            ],
            "description": f"📝 {game['description'][:180]}...",
            "footer": {"text": "Steam Data Scraper Active • GamerPower"}
        }]
    }
    requests.post(WEBHOOK_URL, json=payload)

# ส่วนอื่นๆ (get_sent_games, save_sent_game, check_and_run) คงเดิมไว้ครับ
