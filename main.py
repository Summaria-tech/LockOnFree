import requests
import os

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
DB_FILE = 'sent_games.txt'

def get_sent_games():
    if not os.path.exists(DB_FILE): return []
    with open(DB_FILE, 'r') as f: return f.read().splitlines()

def save_sent_game(game_id):
    with open(DB_FILE, 'a') as f: f.write(f"{game_id}\n")

def send_to_discord(game):
    payload = {
        "embeds": [{
            "title": f"🎮 {game['title']}",
            "description": f"**Platform:** {game['platforms']}\n**Worth:** {game['worth']}\n\n[คลิกเพื่อไปหน้ากดรับเกม]({game['open_giveaway_url']})",
            "url": game['open_giveaway_url'],
            "color": 5763719,
            "image": {"url": game['thumbnail']},
            "footer": {"text": "GamerPower Updates"}
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
            # ส่งเฉพาะเกมที่ยังไม่เคยส่ง (เช็ค 10 เกมล่าสุด)
            for game in reversed(games[:10]):
                game_id = str(game['id'])
                if game_id not in sent_ids:
                    send_to_discord(game)
                    save_sent_game(game_id)
                    print(f"✅ Sent: {game['title']}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if WEBHOOK_URL:
        check_and_run()
    else:
        print("❌ Error: DISCORD_WEBHOOK not found")
