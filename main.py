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

def get_smart_genre(game):
    desc = game['description'].lower()
    url = game['open_giveaway_url']
    
    # 1. ลองดึงจาก Steam (ลดเวลาเหลือ 3 วินาทีเพื่อความเร็ว)
    if "steampowered.com" in url:
        try:
            print(f"🔍 ส่องแนวเกมจาก Steam: {game['title']}")
            headers = {'User-Agent': 'Mozilla/5.0', 'Cookie': 'birthtime=283993201; lastseenprev=1; steamCountry=TH'}
            res = requests.get(url, headers=headers, timeout=3)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                tags = [tag.get_text().strip() for tag in soup.find_all('a', {'class': 'app_tag'})[:4]]
                if tags: return ", ".join(tags)
        except Exception as e:
            print(f"⚠️ ส่อง Steam ไม่สำเร็จ: {e}")

    # 2. ระบบสำรอง (Smart Keyword)
    keywords = {
        "สวมบทบาท (RPG)": ["rpg", "role-playing", "souls"],
        "แอคชั่น (Action)": ["action", "hack", "slash", "fighting"],
        "ผจญภัย (Adventure)": ["adventure", "puzzle", "narrative", "2d"],
        "วางแผน (Strategy)": ["strategy", "tactic", "moba", "card"],
        "จำลองสถานการณ์ (Simulation)": ["simulation", "sim", "management", "building"],
        "ยิง (Shooting)": ["shooter", "fps", "tps", "gun"],
        "สยองขวัญ (Horror)": ["horror", "scary"],
        "เอาชีวิตรอด (Survival)": ["survival", "open world"]
    }
    found = [g for g, keys in keywords.items() if any(k in desc for k in keys)]
    return ", ".join(found) if found else f"อื่นๆ ({game['type']})"

def send_to_discord(game):
    genre_display = get_smart_genre(game)
    img_url = game.get('thumbnail', '')
    
    payload = {
        "embeds": [{
            "title": f"🎮 {game['title']}",
            "url": game['open_giveaway_url'],
            "color": 2303786,
            "thumbnail": {"url": img_url}, 
            "fields": [
                {"name": "📂 แนวเกม", "value": f"`{genre_display}`", "inline": False},
                {"name": "💻 แพลตฟอร์ม", "value": f"**{game['platforms']}**", "inline": True},
                {"name": "💰 มูลค่า", "value": f"~~{game['worth']}~~ **FREE**", "inline": True}
            ],
            "description": f"📝 {game['description'][:160]}...",
            "footer": {"text": "Multi-Platform Game Tracker • GamerPower"}
        }]
    }
    r = requests.post(WEBHOOK_URL, json=payload)
    print(f"🚀 ส่งเข้า Discord: {game['title']} (Status: {r.status_code})")

def check_and_run():
    sent_ids = get_sent_games()
    api_url = "https://www.gamerpower.com/api/giveaways"
    try:
        res = requests.get(api_url)
        if res.status_code == 200:
            games = res.json()
            # ตรวจสอบ 5 เกมล่าสุด
            for game in reversed(games[:5]):
                game_id = str(game['id'])
                if game_id not in sent_ids:
                    send_to_discord(game)
                    save_sent_game(game_id)
                else:
                    print(f"⏭️ ข้ามเกมเดิม: {game['title']}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if WEBHOOK_URL: check_and_run()
