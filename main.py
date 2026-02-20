import requests
import os
from bs4 import BeautifulSoup

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
DB_FILE = 'sent_games.txt'

# --- ฟังก์ชันจัดการประวัติ (ของเดิม) ---
def get_sent_games():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: pass
        return []
    with open(DB_FILE, 'r') as f:
        return f.read().splitlines()

def save_sent_game(game_id):
    with open(DB_FILE, 'a') as f:
        f.write(f"{game_id}\n")

# --- ฟังก์ชันดึงข้อมูล Steam (ที่ทำหายไปเมื่อกี้ เอากลับมาแล้วครับ) ---
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

# --- ฟังก์ชันส่ง Discord (เพิ่มลิงก์ Claim ให้กดง่าย) ---
def send_to_discord(game):
    steam_data = get_steam_data(game['open_giveaway_url'])
    genre_display = steam_data["genres"] if steam_data["genres"] else f"อื่นๆ ({game['type']})"
    img_url = steam_data["image"] if steam_data["image"] else game.get('image', game.get('thumbnail', ''))

    payload = {
        "content": f"🎁 **Claim Game Here:** {game['open_giveaway_url']}", # ลิงก์ที่กดแล้วเด้งทันที
        "embeds": [{
            "title": f"🎮 {game['title']}",
            "url": game['open_giveaway_url'], # กดที่ชื่อเกมก็เด้ง
            "color": 1752220,
            "image": {"url": img_url}, 
            "fields": [
                {"name": "📂 แนวเกม", "value": f"`{genre_display}`", "inline": False},
                {"name": "💻 แพลตฟอร์ม", "value": f"**{game['platforms']}**", "inline": True},
                {"name": "💰 มูลค่า", "value": f"~~{game['worth']}~~ **FREE**", "inline": True},
                {"name": "🚀 วิธีรับเกม", "value": f"**[คลิกเพื่อรับเกมทันที]({game['open_giveaway_url']})**", "inline": False}
            ],
            "footer": {"text": "LockOnFree • GamerPower API"}
        }]
    }
    requests.post(WEBHOOK_URL, json=payload)
    print(f"✅ ส่งแล้ว: {game['title']}")

# --- ฟังก์ชันหลัก (ของเดิม) ---
def check_and_run():
    print("🤖 บอทกำลังตรวจสอบเกมใหม่...")
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
                    print(f"⏭️ ข้าม: {game['title']}")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    if WEBHOOK_URL:
        check_and_run()
