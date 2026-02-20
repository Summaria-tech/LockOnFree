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
    """ส่งข้อมูลเข้า Discord พร้อมลิงก์ที่กดแล้วเด้งทันที"""
    steam_data = get_steam_data(game['open_giveaway_url'])
    genre_display = steam_data["genres"] if steam_data["genres"] else f"อื่นๆ ({game['type']})"
    img_url = steam_data["image"] if steam_data["image"] else game.get('image', game.get('thumbnail', ''))

    # สร้าง Payload
    payload = {
        # content ด้านบนจะทำให้ Discord สร้างปุ่มพรีวิวขนาดใหญ่ด้านล่างให้อัตโนมัติ
        "content": f"🎁 **กดรับเกมที่นี่:** {game['open_giveaway_url']}",
        "embeds": [{
            "title": f"🎮 {game['title']}",
            "url": game['open_giveaway_url'], # กดที่ชื่อเกมก็เด้งไปลิงก์เลย
            "color": 1752220,
            "image": {"url": img_url}, 
            "fields": [
                {"name": "📂 แนวเกม", "value": f"`{genre_display}`", "inline": False},
                {"name": "💻 แพลตฟอร์ม", "value": f"**{game['platforms']}**", "inline": True},
                {"name": "💰 มูลค่า", "value": f"~~{game['worth']}~~ **FREE**", "inline": True},
                # บรรทัดนี้คือ "ปุ่มกด" ในรูปแบบ Embed ที่กดแล้วเด้งทันที
                {"name": "🚀 วิธีรับเกม", "value": f"**[คลิกที่นี่เพื่อ Claim Game ทันที]({game['open_giveaway_url']})**", "inline": False}
            ],
            "footer": {"text": "คลิกที่ชื่อเกมหรือลิงก์ด้านบนเพื่อรับสิทธิ์ • GamerPower"}
        }]
    }
    
    requests.post(WEBHOOK_URL, json=payload)

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

