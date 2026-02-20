import requests
import os
from bs4 import BeautifulSoup

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
DB_FILE = 'sent_games.txt'

def get_sent_games():
    # ถ้าไม่มีไฟล์ ให้สร้างไฟล์เปล่าขึ้นมาทันที
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            pass
        return []
    with open(DB_FILE, 'r') as f:
        return f.read().splitlines()

def save_sent_game(game_id):
    with open(DB_FILE, 'a') as f:
        f.write(f"{game_id}\n")

# ... (ฟังก์ชัน get_steam_data และ send_to_discord เหมือนเดิม) ...

def check_and_run():
    sent_ids = get_sent_games()
    api_url = "https://www.gamerpower.com/api/giveaways"
    try:
        res = requests.get(api_url)
        if res.status_code == 200:
            games = res.json()
            # ลองส่ง 5 เกมล่าสุด (ถ้ายังไม่เคยส่ง)
            for game in reversed(games[:5]):
                game_id = str(game['id'])
                if game_id not in sent_ids:
                    send_to_discord(game)
                    save_sent_game(game_id)
                    print(f"✅ บอทส่งเกมแล้ว: {game['title']}")
                else:
                    print(f"⏭️ ข้ามเกมเดิม: {game['title']}")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    if WEBHOOK_URL:
        check_and_run()
    else:
        print("❌ ไม่พบ DISCORD_WEBHOOK ใน Secrets")
