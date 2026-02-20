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
    if "rpg" in desc or "role-playing" in desc: return "สวมบทบาท (RPG)"
    if "action" in desc or "hack and slash" in desc or "fighting" in desc: return "แอคชั่น (Action)"
    if "adventure" in desc or "puzzle" in desc: return "ผจญภัย (Adventure)"
    if "strategy" in desc or "rts" in desc or "tactic" in desc or "moba" in desc: return "วางแผน (Strategy)"
    if "simulation" in desc or "simulator" in desc or "management" in desc: return "จำลองสถานการณ์ (Simulation)"
    if "shooter" in desc or "fps" in desc or "tps" in desc: return "ยิง (Shooting)"
    if "mmorpg" in desc or "mmo" in desc: return "เกมออนไลน์ (MMORPG)"
    if "horror" in desc: return "สยองขวัญ (Horror)"
    if "racing" in desc: return "แข่งรถ (Racing)"
    if "sandbox" in desc or "open world" in desc: return "Sandbox (อิสระ)"
    if "casual" in desc: return "Casual (เล่นชิลล์ๆ)"
    return f"อื่นๆ ({game_type})"

def send_to_discord(game):
    genre_thai = get_genre_thai(game['description'], game['type'])
    
    payload = {
        "embeds": [{
            "title": f"{game['title']}", # ชื่อเกมเด่นๆ
            "url": game['open_giveaway_url'],
            "color": 3066993,
            # ย้ายรูปจาก 'image' มาเป็น 'thumbnail' เพื่อให้อยู่ด้านหน้า/ข้าง
            "thumbnail": {"url": game['thumbnail']}, 
            "description": (
                f"**📂 แนวเกม:** `{genre_thai}`\n"
                f"**💻 แพลตฟอร์ม:** {game['platforms']}\n"
