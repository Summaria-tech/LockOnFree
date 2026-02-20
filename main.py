import discord
from discord.ext import commands
import requests
import os

# ใช้ TOKEN แทน WEBHOOK_URL แล้วนะ
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID')) # ต้องระบุ ID ห้องที่จะให้บอทไปพิมพ์
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

# --- สร้างปุ่มแบบ Link Button ---
class ClaimView(discord.ui.View):
    def __init__(self, url):
        super().__init__()
        # เพิ่มปุ่มสีแดง (Danger) ที่เป็นลิงก์
        self.add_item(discord.ui.Button(label='🔥 CLAIM GAME NOW', url=url, style=discord.ButtonStyle.link))

async def check_games(bot):
    channel = bot.get_channel(CHANNEL_ID)
    sent_ids = get_sent_games()
    api_url = "https://www.gamerpower.com/api/giveaways"
    
    res = requests.get(api_url)
    if res.status_code == 200:
        games = res.json()
        for game in reversed(games[:5]):
            game_id = str(game['id'])
            if game_id not in sent_ids:
                embed = discord.Embed(title=f"🎮 {game['title']}", url=game['open_giveaway_url'], color=0xff0000)
                embed.set_image(url=game['image'])
                embed.description = f"📝 {game['description'][:160]}..."
                embed.add_field(name="💻 Platform", value=game['platforms'])
                
                # ส่งพร้อมปุ่ม
                await channel.send(embed=embed, view=ClaimView(game['open_giveaway_url']))
                save_sent_game(game_id)
    
    await bot.close() # รันเสร็จแล้วปิดตัวเองเพื่อให้ GitHub Actions จบงาน

# --- ส่วนรันบอท ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'🤖 Logged in as {bot.user}')
    await check_games(bot)

if __name__ == "__main__":
    bot.run(TOKEN)
