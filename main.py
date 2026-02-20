import requests
import os

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
DB_FILE = 'sent_games.txt'

def get_sent_games():
    if not os.path.exists(DB_FILE): return []
    with open(DB_FILE, 'r') as f: return f.read().splitlines()

def save_sent_game(game_id):
    with open(DB_FILE, 'a') as f: f.write(f"{game_id}\n")

def get_genre_thai(description, game_type):
    desc = description.lower()
    if any(k in desc for k in ["rpg", "role-playing", "souls"]): return "สวมบทบาท (RPG)"
    if any(k in desc for k in ["action", "hack", "slash", "fighting"]): return "แอคชั่น (Action)"
    if any(k in desc for k in ["platformer", "retro", "2d", "jump"]): return "ผจญภัย (Adventure)"
    if any(k in desc for k in ["strategy", "tactic", "moba", "card"]): return "วางแผน (Strategy)"
    if any(k in desc for k in ["simulation", "sim", "management", "build"]): return "จำลองสถานการณ์ (Simulation)"
    if any(k in desc for k in ["shooter", "fps", "tps", "gun"]): return "ยิง (Shooting)"
    if any(k in desc for k in ["horror", "scary"]): return "สยองขวัญ (Horror)"
    if "racing" in desc: return "แข่งรถ (Racing)"
    return f"อื่นๆ ({game_type})"

def send_to_discord(game):
    genre_thai = get_genre_thai(game['description'], game['type'])
    img_url = game.get('thumbnail', '')
    
    payload = {
        "embeds": [{
            "title": f"🎮 {game['title']}",
            "url": game['open_giveaway_url'],
            "color": 1752220,
            "thumbnail": {"url": img_url}, 
            "fields": [
                {"name": "📂 แนวเกม", "value": f"`{genre_thai}`", "inline": True},
                {"name": "💻 แพลตฟอร์ม", "value": f"`{game['platforms']}`", "inline": True},
                {"name": "💰 มูลค่า", "value": f"~~{game['worth']}~~ **FREE**", "inline": False}
            ],
            "description": f"📝 {game['description'][:180]}...",
            "footer": {"text": "Steam Free Games Tracker", "icon_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Steam_icon_logo.svg/512px-Steam_icon_logo.svg.png"}
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
            # บังคับรัน 5 เกมแรกเพื่อสร้างไฟล์ใหม่
            for game in reversed(games[:5]):
                game_id = str(game['id'])
                if game_id not in sent_ids:
                    send_to_discord(game)
                    save_sent_game(game_id)
                    print(f"✅ Sent: {game['title']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if WEBHOOK_URL:
        check_and_run()
