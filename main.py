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
    """วิเคราะห์แนวเกมจากทั้ง Steam Tags และ Description ของค่ายอื่น"""
    desc = game['description'].lower()
    url = game['open_giveaway_url']
    
    # 1. ถ้าเป็น Steam ให้ลองไปขูด Tags มาก่อน
    if "steampowered.com" in url:
        try:
            headers = {'User-Agent': 'Mozilla/5.0', 'Cookie': 'birthtime=283993201; lastseenprev=1; steamCountry=TH'}
            res = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            tags = [tag.get_text().strip() for tag in soup.find_all('a', {'class': 'app_tag'})[:4]]
            if tags: return ", ".join(tags)
        except: pass

    # 2. ถ้าไม่ใช่ Steam หรือดึงไม่ได้ ให้ใช้ระบบ Keyword Mapping (ครอบคลุมทุกค่าย)
    keywords = {
        "สวมบทบาท (RPG)": ["rpg", "role-playing", "souls", "level up"],
        "แอคชั่น (Action)": ["action", "hack", "slash", "fighting", "combat"],
        "ผจญภัย (Adventure)": ["adventure", "puzzle", "narrative", "visual novel", "2d"],
        "วางแผน (Strategy)": ["strategy", "tactic", "moba", "card", "tower defense"],
        "จำลองสถานการณ์ (Simulation)": ["simulation", "sim", "management", "building", "sandbox"],
        "ยิง (Shooting)": ["shooter", "fps", "tps", "gun", "warfare"],
        "สยองขวัญ (Horror)": ["horror", "scary", "spooky", "survival horror"],
        "เอาชีวิตรอด (Survival)": ["survival", "crafting", "open world"]
    }

    found_genres = []
    for genre, keys in keywords.items():
        if any(k in desc for k in keys):
            found_genres.append(genre)
    
    return ", ".join(found_genres) if found_genres else f"อื่นๆ ({game['type']})"

def send_to_discord(game):
    genre_display = get_smart_genre(game)
    img_url = game.get('thumbnail', '')
    
    payload = {
        "embeds": [{
            "title": f"🎮 {game['title']}",
            "url": game['open_giveaway_url'],
            "color": 2303786, # สีเทาเข้มโทนเกมมิ่ง
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
    requests.post(WEBHOOK_URL, json=payload)

def check_and_run():
    sent_ids = get_sent_games()
    api_url = "https://www.gamerpower.com/api/giveaways"
    try:
        res = requests.get(api_url)
        if res.status_code == 200:
            games = res.json()
            for game in reversed(games[:5]): # รัน 5 เกมล่าสุด
                if str(game['id']) not in sent_ids:
                    send_to_discord(game)
                    save_sent_game(str(game['id']))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if WEBHOOK_URL: check_and_run()
