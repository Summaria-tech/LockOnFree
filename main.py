import discord
from discord.ext import commands
import requests
import os
import re
from datetime import datetime, timedelta  # <--- เช็คด่วน! บรรทัดนี้ต้องมีและห้ามมีช่องว่างข้างหน้า

# --- ดึงค่าจาก GitHub Secrets ---
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID')) if os.getenv('DISCORD_CHANNEL_ID') else None
RAWG_KEY = os.getenv('RAWG_API_KEY')
DB_FILE = 'sent_games.txt'

def get_sent_games():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return f.read().splitlines()
    return []

def save_sent_game(game_id):
    with open(DB_FILE, 'a') as f:
        f.write(f"{game_id}\n")

def get_genres_from_rawg(game_name):
    if not RAWG_KEY: return []
    try:
        clean_name = re.sub(r'\(.*?\)|(?i)giveaway|free|download|pack', '', game_name)
        clean_name = re.sub(r'[^\w\s]', '', clean_name).strip()
        url = f"https://api.rawg.io/api/games?key={RAWG_KEY}&search={clean_name}&page_size=1"
        res = requests.get(url, timeout=10).json()
        if res.get('results'):
            return [g['name'] for g in res['results'][0].get('genres', [])]
    except Exception as e:
        print(f"RAWG Error: {e}")
    return []

def get_detailed_genres(game):
    title = game.get('title', '')
    desc = game.get('description', '').lower()
    g_type = "Full Game" if game.get('type') == "Game" else game.get('type', 'Full Game')
    rawg_genres = get_genres_from_rawg(title)
    backup_genres = []
    keywords = {
        "Action": ["action", "fighting", "hack"],
        "Adventure": ["adventure", "exploration"],
        "RPG": ["rpg", "role-playing"],
        "Strategy": ["strategy", "tactic"],
        "Shooting": ["shooting", "fps"],
        "Platformer": ["platformer", "2d", "retro"],
        "Indie": ["indie", "independent"]
    }
    for genre, keys in keywords.items():
        if any(key in desc or key in title.lower() for key in keys):
            backup_genres.append(genre)
    combined = rawg_genres + backup_genres
    final_list = []
    for item in combined:
        if item not in final_list:
            final_list.append(item)
    if final_list:
        return f"{g_type} | {' | '.join(final_list[:5])}"
    return g_type

class ClaimView(discord.ui.View):
    def __init__(self, url):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label='CLAIM GAME NOW', url=url, style=discord.ButtonStyle.link, emoji='🎁'))

async def check_and_send(bot):
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: 
        print("❌ Error: Channel ID not found")
        return
    
    sent_ids = get_sent_games()
    res = requests.get("https://www.gamerpower.com/api/giveaways")
    new_game_count = 0 
    
    if res.status_code == 200:
        games = res.json()
        for game in reversed(games[:100]):
            game_id = str(game['id'])
            if game_id not in sent_ids:
                genre_list = get_detailed_genres(game)
                
                embed = discord.Embed(
                    title=f"🎮 {game['title']}",
                    description=f"✅ **Genres:** `{genre_list}`\n\n{game['description'][:180]}...",
                    color=5814783,
                    url=game['open_giveaway_url']
                )
                embed.set_image(url=game.get('image') or game.get('thumbnail'))
                embed.add_field(name="💻 Platform", value=f"**{game.get('platforms')}**", inline=True)
                embed.add_field(name="💰 Worth", value=f"~~{game.get('worth')}~~ **FREE**", inline=True)
                embed.set_footer(text="LockOnFree • Click the button below to claim")
                
                await channel.send(embed=embed, view=ClaimView(game['open_giveaway_url']))
                save_sent_game(game_id)
                new_game_count += 1
                print(f"✅ Sent: {game['title']}")

    # --- ส่วนที่ต้องแก้ในฟังก์ชัน check_and_send ---
    
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'🤖 {bot.user} Online')
    await check_and_send(bot)
    await bot.close()

if __name__ == "__main__":
    if TOKEN and CHANNEL_ID:
        bot.run(TOKEN)





