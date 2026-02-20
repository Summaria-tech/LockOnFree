import discord
from discord.ext import commands
import requests
import os

# --- ดึงค่าจาก GitHub Secrets ---
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID')) if os.getenv('DISCORD_CHANNEL_ID') else None
RAWG_KEY = os.getenv('RAWG_API_KEY') # อย่าลืมไปใส่ใน GitHub Secrets นะครับ
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

def get_genres_from_rawg(game_name):
    """ดึงแนวเกมจากฐานข้อมูล RAWG (ครอบคลุมทุกแพลตฟอร์ม)"""
    if not RAWG_KEY: return []
    try:
        url = f"https://api.rawg.io/api/games?key={RAWG_KEY}&search={game_name}&page_size=1"
        res = requests.get(url, timeout=5).json()
        if res.get('results'):
            genres = [g['name'] for g in res['results'][0].get('genres', [])]
            return genres
    except: return []
    return []

def get_detailed_genres(game):
    """รวม 'ประเภทการแจก' และ 'แนวเกมจาก RAWG' เข้าด้วยกัน"""
    title = game.get('title', '')
    
    # 1. แยกประเภท (Full Game / DLC / Early Access)
    g_type = game.get('type', 'Game')
    if g_type == "Game": g_type = "Full Game"
    
    # 2. ดึงแนวเกมจากฐานข้อมูลโลก (RAWG)
    rawg_genres = get_genres_from_rawg(title)
    
    # 3. ถ้าหาแนวเจอ ให้เอามาต่อท้ายประเภทเกม
    if rawg_genres:
        # ผลลัพธ์จะเป็น: Full Game | Action | Adventure
        return f"{g_type} | {' | '.join(rawg_genres[:3])}"
    
    return g_type

class ClaimView(discord.ui.View):
    def __init__(self, url):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label='CLAIM GAME NOW', url=url, style=discord.ButtonStyle.link, emoji='🎁'))

async def check_and_send(bot):
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return
    
    sent_ids = get_sent_games()
    res = requests.get("https://www.gamerpower.com/api/giveaways")
    
    if res.status_code == 200:
        games = res.json()
        for game in reversed(games[:5]):
            game_id = str(game['id'])
            if game_id not in sent_ids:
                # ดึง Genre แบบละเอียด (Full Game + RAWG Genres)
                genre_list = get_detailed_genres(game)
                
                embed = discord.Embed(
                    title=f"🎮 {game['title']}",
                    description=f"✅ **Genres:** `{genre_list}`\n\n{game['description'][:180]}...",
                    color=0xff4747,
                    url=game['open_giveaway_url']
                )
                embed.set_image(url=game['image'] or game['thumbnail'])
                embed.add_field(name="💻 Platform", value=f"**{game['platforms']}**", inline=True)
                embed.add_field(name="💰 Worth", value=f"~~{game['worth']}~~ **FREE**", inline=True)
                embed.set_footer(text="LockOnFree • Click the button below to claim")
                
                await channel.send(embed=embed, view=ClaimView(game['open_giveaway_url']))
                save_sent_game(game_id)
                print(f"✅ Sent: {game['title']} | Genre: {genre_list}")

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
