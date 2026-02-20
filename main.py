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
    if "rpg" in desc: return "สวมบทบาท (RPG)"
    if "action" in desc: return "แอคชั่น (Action)"
    if "adventure" in desc: return "ผจญภัย (Adventure)"
    if "strategy" in desc: return "วางแผน (Strategy)"
    if "shooter" in desc or "fps" in desc: return "ยิง (Shooting)"
    return f"อื่นๆ ({game_type})"

def send_to_discord(game):
    genre_thai = get_genre_thai(game['description'], game['type'])
    img_url = game.get('thumbnail', '')
    
    payload = {
        "embeds": [{
            "title": f"🎮 {game['title']}",
            "url": game['open_giveaway_url'],
            "color": 3066993,
            "thumbnail": {"url": img_url}, # ส่งรูปเล็กด้านข้าง
            "description": (
                f"**📂 แนวเกม:** `{genre_thai}`\n"
                f"**💻 แพลตฟอร์ม:** {game['platforms']}\n"
                f"**💰 มูลค่า:** {game['worth']}\n\n"
                f"📝 {game['description'][:150]}...\n\n"
                f"🔗 [**คลิกเพื่อไปหน้ากดรับเกม**]({game['open_giveaway_url']})"
            ),
            "footer": {"text": "GamerPower Updates"}
        }]
    }
    
    # ส่งข้อมูลหลัก
    requests.post(WEBHOOK_URL, json=payload)
    
    # ท่าไม้ตาย: ถ้าส่ง Embed แล้วรูปไม่ขึ้น ให้ส่งลิงก์รูปตามไปทื่อๆ เลย Discord จะบังคับโชว์รูปครับ
    # requests.post(WEBHOOK_URL, json={"content": img_url}) # เปิดบรรทัดนี้ถ้าอยากให้ส่งรูปแยกด้านล่าง

def check_and_run():
    sent_ids = get_sent_games()
    api_url = "https://www.gamerpower.com/api/giveaways"
    try:
        res = requests.get(api_url)
        if res.status_code == 200:
            games = res.json()
            for game in reversed(games[:10]):
                if str(game['id']) not in sent_ids:
                    send_to_discord(game)
                    save_sent_game(str(game['id']))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if WEBHOOK_URL: check_and_run()

