import requests
import os
from bs4 import BeautifulSoup

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
DB_FILE = 'sent_games.txt'

def get_sent_games():
    if not os.path.exists(DB_FILE): return []
    with open(DB_FILE, 'r') as f: return f.read().splitlines()

def save_sent_game(game_id):
    with open(DB_FILE, 'a') as f: f.write(f"{game_id}\n")

def get_steam_data(url):
    """ขูดข้อมูลแนวเกมและรูปภาพจาก Steam"""
    data = {"genres": None, "image": None}
    if "steampowered.com" not in url: return data
    try:
        headers = {'User-Agent': 'Mozilla/5.0', 'Cookie': 'birthtime=283993201; steamCountry=TH'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # 1. ดึงแนวเกม (Tags)
            tags = [tag.get_text().strip() for tag in soup.find_all('a', {'class': 'app_tag'})[:5]]
            if tags: data["genres"] = ", ".join(tags)
            # 2. ดึงรูปโปรไฟล์ (พยายามดึงจากหลายจุด)
            img_tag = soup.find('img', {'class': 'game_header_image_full'})
            if img_tag: 
                data["image"] = img_tag['src']
            else:
                # สำรอง: ดึงจากภาพตัวอย่างแรก
                img_tag = soup.find('img', {'class': 'highlight_screenshot_img'})
                if img_tag: data["image"] = img_tag['src']
    except: pass
    return data

def send_to_discord(game):
    # ดึงข้อมูลเสริม
    steam_data = get_steam_data(game['open_giveaway_url'])
    genre_display = steam_data["genres"] if steam_data["genres"] else f"อื่นๆ ({game['type']})"
    
    # บังคับใช้รูปที่ชัดที่สุด (จัดลำดับ: Steam > API Thumbnail)
    img_url = steam_data["image"] if steam_data["image"] else game.get('thumbnail', '')

    payload = {
        "embeds": [{
            "title": f"🎮 {game['title']}",
            "url": game['open_giveaway_url'],
            "color": 1752220,
            "thumbnail": {"url": img_url}, 
            "fields": [
                {"name": "📂 แนวเกม (Steam Tags)", "value": f"`{genre_display}`", "inline": False},
                {"name": "💻 แพลตฟอร์ม", "value": f"**{game['platforms']}**", "inline": True},
                {"name": "💰 มูลค่า", "value": f"~~{game['worth']}~~ **FREE**", "inline": True}
            ],
            "description": f"📝 {game['description'][:160]}...",
            "footer": {"text": "Steam Tracker Active • GamerPower"}
        }]
    }
    requests.post(WEBHOOK_URL, json=payload)

def check_and_run():
    sent_ids = get_sent_games()
    api_url = "https://www.gamerpower.com/api/giveaways"
    try:
        res = requests.get(api_url)
        if res.status_code == 200:
            games = res.json()
            # ตรวจสอบ 5 เกมล่าสุด ถ้าลบไฟล์ txt แล้ว มันจะเด้งใหม่หมดครับ
            for game in reversed(games[:5]):
                game_id = str(game['id'])
                if game_id not in sent_ids:
                    send_to_discord(game)
                    save_sent_game(game_id)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if WEBHOOK_URL: check_and_run()
