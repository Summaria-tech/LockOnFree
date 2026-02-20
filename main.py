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
    # เพิ่ม Keyword ให้แม่นยำแบบ Steam
    if any(k in desc for k in ["rpg", "role-playing", "souls"]): return "สวมบทบาท (RPG)"
    if any(k in desc for k in ["action", "hack", "slash", "fighting"]): return "แอคชั่น (Action)"
    if any(k in desc for k in ["platformer", "retro", "2d"]): return "ผจญภัย (Adventure/Platformer)"
    if any(k in desc for k in ["strategy", "tactic", "moba", "card"]): return "วางแผน (Strategy)"
    if any(k in desc for k in ["simulation", "sim", "management", "build"]): return "จำลองสถานการณ์ (Simulation)"
    if any(k in desc for k in ["shooter", "fps", "tps", "gun"]): return "ยิง (Shooting)"
    if any(k in desc for k in ["horror", "scary", "survival horror"]): return "สยองขวัญ (Horror)"
    if "racing" in desc: return "แข่งรถ (Racing)"
    if any(k in desc for k in ["sandbox", "open world", "survival"]): return "Sandbox (อิสระ/เอาชีวิตรอด)"
    if "visual novel" in desc or "narrative" in desc: return "ผจญภัย (Visual Novel)"
    
    return f"อื่นๆ ({game_type})"

def send_to_discord(game):
    genre_thai = get_genre_thai(game['description'], game['type'])
    img_url = game.get('thumbnail', '')
    
    # ปรับ Embed ให้ใกล้เคียง Steam Style
    payload = {
        "embeds": [{
            "title": f"🎮 {game['title']}",
            "url": game['open_giveaway_url'],
            "color": 1752220, # สีฟ้าน้ำทะเลแบบ Steam
            "thumbnail": {"url": img_url}, # รูปเล็กด้านข้าง
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
