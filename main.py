import requests
import os
from bs4 import BeautifulSoup

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
DB_FILE = 'sent_games.txt'

# --- 1. ฟังก์ชันจัดการไฟล์ประวัติ ---
def get_sent_games():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: pass
        return []
    with open(DB_FILE, 'r') as f:
        return f.read().splitlines()

def save_sent_game(game_id):
    with open(DB_FILE, 'a') as f:
        f.write(f"{game_id}\n")

# --- 2. ฟังก์ชันดึงข้อมูลจาก Steam ---
def get_steam_data(url):
    data = {"genres": None, "image": None}
    if "steampowered.com" not in url: return data
    try:
        headers = {'User-Agent': 'Mozilla/5.0', 'Cookie': 'birthtime=283993201; steamCountry=TH'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            tags = [tag.get_text().strip() for tag in soup.find_all('a', {'class': 'app_tag'})[:5]]
            if tags: data["genres"] = ", ".join(tags)
            img_tag = soup.find('img', {'class': 'game_header_image_full'})
            if img_tag: data["image"] = img_tag['src']
    except: pass
    return data

# --- 3. ฟังก์ชันส่งเข้า Discord ---
def send_to_discord(game):
    steam_data = get_steam_data(game['open_giveaway_url'])
    genre_display = steam_data["genres"] if steam_data["genres"] else f"อื่นๆ ({game['type']})"
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
    r = requests.post(WEBHOOK_URL, json=payload)
    print(f"✅ ส่งเกม {game['title']} แล้ว (Status: {r.status_code})")

# --- 4. ฟังก์ชันหลัก (ตัวเริ่มรัน) ---
def check_and_run():
    print("🤖 บอทกำลังตรวจสอบเกมใหม่...")
    sent_ids = get_sent_games()
    api_url = "https://www.gamerpower.com/api/giveaways"
    
    try:
        res = requests.get(api_url)
        if res.status_code == 200:
            games = res.json()
            for game in reversed(games[:5]): # เช็ค 5 เกมล่าสุด
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
    else:
        print("❌ ไม่พบ Webhook URL ใน Secrets!")
