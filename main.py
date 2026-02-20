import discord
from discord.ext import commands
import requests
import os
from bs4 import BeautifulSoup

# --- ดึงค่าจาก GitHub Secrets ---
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
channel_id_env = os.getenv('DISCORD_CHANNEL_ID')
CHANNEL_ID = int(channel_id_env) if channel_id_env and channel_id_env.isdigit() else None
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

def get_steam_data(url):
    """ขูดข้อมูล Tags หลายแนวจาก Steam ให้ครอบคลุม Action, RPG, etc."""
    if "steampowered.com" not in url: return None
    try:
        headers = {'User-Agent': 'Mozilla/5.0', 'Cookie': 'birthtime=283993201; steamCountry=TH'}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # ดึงมา 5 แนว เพื่อให้ได้ Action | Adventure | RPG ตามลำดับความสำคัญ
            tags = [tag.get_text().strip() for tag in soup.find_all('a', {'class': 'app_tag'})[:5]]
            return " | ".join(tags) if tags else None
    except: return None

# --- สร้างปุ่มกด Link Button (ปุ่มจริงแยกนอกกล่อง) ---
class ClaimView(discord.ui.View):
    def __init__(self, url):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label='CLAIM GAME NOW', 
            url=url, 
            style=discord.ButtonStyle.link,
            emoji='🎁'
        ))

async def check_and_send(bot):
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return

    sent_ids = get_sent_games()
    api_url = "https://www.gamerpower.com/api/giveaways"
    
    res = requests.get(api_url)
    if res.status_code == 200:
        games = res.json()
        for game in reversed(games[:5]):
            game_id = str(game['id'])
            if game_id not in sent_ids:
                # ดึงแนวเกมหลายแนว
                genre_list = get_steam_data(game['open_giveaway_url']) or game.get('type', 'Game')

                # สร้าง Embed แบบสีแดง
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

                # ส่งพร้อมปุ่มจริง
                await channel.send(embed=embed, view=ClaimView(game['open_giveaway_url']))
                save_sent_game(game_id)
                print(f"✅ ส่งแล้ว: {game['title']}")

# --- รันบอท ---
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
