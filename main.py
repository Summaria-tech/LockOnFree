import discord
from discord.ext import commands
import requests
import os
from bs4 import BeautifulSoup
import re

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

def get_detailed_genres(game):
    """ดึงแนวเกมแบบเจาะลึก: พยายามดึงจาก Steam ก่อน ถ้าไม่ได้ให้สแกนจากคำอธิบาย"""
    url = game.get('open_giveaway_url', '')
    description = game.get('description', '').lower()
    
    # 1. พยายามดึงจาก Steam Tags
    if "steampowered.com" in url:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', 'Cookie': 'birthtime=283993201; steamCountry=TH'}
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                tags = [tag.get_text().strip() for tag in soup.find_all('a', {'class': 'app_tag'})[:5]]
                if tags: return " | ".join(tags)
        except: pass

    # 2. ถ้าดึงจากเว็บไม่ได้ ให้สแกนหา Keywords ในคำอธิบายเองเลย (อ้างอิงตามที่คุณลิสต์มา)
    keywords = {
        "Action": ["action", "fast-paced", "fighting", "hack and slash"],
        "Adventure": ["adventure", "exploration", "story-driven"],
        "RPG": ["rpg", "role-playing", "level up", "jrpg", "arpg"],
        "Strategy": ["strategy", "rts", "turn-based", "moba", "tactic"],
        "Simulation": ["simulation", "simulator", "building", "management"],
        "Shooting": ["shooting", "fps", "tps", "shooter"],
        "Horror": ["horror", "scary", "survival horror"],
        "Online": ["mmorpg", "mmo", "online multiplayer"],
        "Racing": ["racing", "driving", "cars"],
        "Platformer": ["platformer", "2d retro", "jumping"]
    }
    
    found_genres = []
    for genre, keys in keywords.items():
        if any(key in description for key in keys):
            found_genres.append(genre)
    
    if found_genres:
        return " | ".join(found_genres[:3]) # เอาแค่ 3 อันเด่นๆ
    
    # 3. สุดท้ายถ้าไม่เจอจริงๆ ให้ใช้ค่าจาก API แต่ถ้าเป็นคำว่า Game ให้เปลี่ยนเป็น Giveaway แทน
    api_type = game.get('type', 'Game')
    return api_type if api_type != "Game" else "Full Game"

# --- สร้างปุ่มกด Link Button ---
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
                # ใช้ฟังก์ชันใหม่ดึง Genre
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
                print(f"✅ ส่งแล้ว: {game['title']} ({genre_list})")

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
