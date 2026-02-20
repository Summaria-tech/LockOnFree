import requests
import os
from bs4 import BeautifulSoup

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
DB_FILE = 'sent_games.txt'

def get_sent_games():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: pass
        return []
    with open(DB_FILE, 'r') as f:
        return f.read().splitlines()

def save_sent_game(game_id):
    with open(DB_FILE, 'a') as f:
        f.write(f"{game_id}\n")

def get_steam_tags(url):
    """ฟังก์ชันเสริม: ดึงแค่แนวเกมจาก Steam (ถ้าเป็นลิงก์ Steam)"""
    if "steampowered.com" not in url: return None
    try:
        headers = {'User-Agent': 'Mozilla/5.0', 'Cookie': 'birthtime=283993201; steamCountry=TH'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            tags = [tag.get_text().strip() for tag in soup.find_all('a', {'class': 'app_tag'})[:5]]
            return ", ".join(tags) if tags else None
    except: pass
    return None

def send_to_discord(game):
    # 1. ดึงแนวเกม (พยายามเอาจาก Steam Tags ก่อน ถ้าไม่ได้ใช้ประเภทจาก API)
    steam_tags = get_steam_tags(game['open_giveaway_url'])
    genre_display = steam_tags if steam_tags else f"อื่นๆ ({game['type']})"
    
    # 2. ดึงรูปภาพจาก GamerPower (เน้นค่า image เพราะรูปจะใหญ่และชัดกว่า thumbnail)
    img_url = game.get('image') or game.get('thumbnail') or ""

    payload = {
        "embeds": [{
            "title": f"🎮 {game['title']}",
            "url": game['open_giveaway_url'],
            "color": 1752220,
            "image": {"url": img_url}, # เปลี่ยนจาก thumbnail เป็น image เพื่อให้รูปแสดงผลขนาดใหญ่ด้านล่าง
            "fields": [
                {"name": "📂 แนวเกม", "value": f"`{genre_display}`", "inline": False},
                {"name": "💻 แพลตฟอร์ม", "value": f"**{game['platforms']}**", "inline": True},
                {"name": "💰 มูลค่า", "value": f"~~{game['worth']}~~ **FREE**", "inline": True}
            ],
            "description": f"📝 {game['description'][:160]}...",
            "footer": {"text": "LockOnFree • Powered by GamerPower API"}
        }]
    }
    r = requests.post(WEBHOOK_URL, json=payload)
    print(f"✅ ส่งเกม {game['title']} แล้ว (Status: {r.status_code})")

def check_and_run():
    print("🤖 บอทกำลังเช็คเกมใหม่จาก GamerPower...")
    sent_ids = get_sent_games()
    api_url = "https://www.gamerpower.com/api/giveaways"
    
    try:
        res = requests.get(api_url)
        if res.status_code == 200:
            games = res.json()
            for game in reversed(games[:5]):
                game_id = str(game['id'])
                if game_id not in sent_ids:
                    send_to_discord(game)
                    save_sent_game(game_id)
                else:
                    print(f"⏭️ ข้ามเกมเดิม: {game['title']}")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    if WEBHOOK_URL:
        check_and_run()
