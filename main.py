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

def get_steam_genres(steam_url):
    """ฟังก์ชันพิเศษ: เข้าไปดูที่หน้า Steam เพื่อดึงแนวเกมภาษาไทย"""
    if "steampowered.com" not in steam_url:
        return None
    try:
        # หลอกว่าเป็นเบราว์เซอร์และขอเป็นภาษาไทย
        headers = {'User-Agent': 'Mozilla/5.0', 'Cookie': 'birthtime=283993201; lastseenprev=1; steamCountry=TH%7C50468305963f46f40c749c95d852a326'}
        res = requests.get(steam_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # ค้นหาแท็กแนวเกมในหน้า Steam
        genre_tags = soup.find_all('a', {'class': 'app_tag'})
        genres = [tag.get_text().strip() for tag in genre_tags[:5]] # เอา 5 แนวเกมแรก
        return ", ".join(genres) if genres else None
    except:
        return None

def send_to_discord(game):
    # พยายามดึงแนวเกมจาก Steam ก่อน
    steam_genres = get_steam_genres(game['open_giveaway_url'])
    
    # ถ้าไม่ใช่เกม Steam หรือดึงไม่ได้ ให้ใช้ระบบ Keyword ภาษาไทยที่เราทำไว้
    if not steam_genres:
        genre_display = f"อื่นๆ ({game['type']})"
        # (คุณสามารถใส่ Logic get_genre_thai อันเดิมมาช่วยตรงนี้ได้)
    else:
        genre_display = steam_genres

    img_url = game.get('thumbnail', '')
    
    payload = {
        "embeds": [{
            "title": f"🎮 {game['title']}",
            "url": game['open_giveaway_url'],
            "color": 1752220,
            "thumbnail": {"url": img_url}, 
            "fields": [
                {"name": "📂 แนวเกม (Steam Tags)", "value": f"`{genre_display}`", "inline": False},
                {"name": "💻 แพลตฟอร์ม", "value": f"`{game['platforms']}`", "inline": True},
                {"name": "💰 มูลค่า", "value": f"~~{game['worth']}~~ **FREE**", "inline": True}
            ],
            "description": f"📝 {game['description'][:150]}...",
            "footer": {"text": "Steam Data Scraper Active • GamerPower"}
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
            for game in reversed(games[:10]):
                game_id = str(game['id'])
                if game_id not in sent_ids:
                    send_to_discord(game)
                    save_sent_game(game_id)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if WEBHOOK_URL: check_and_run()
