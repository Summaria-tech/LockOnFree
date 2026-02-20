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
    title = game.get('title', '')
    desc = game.get('description', '').lower()
    full_text = (title + " " + desc).lower()
    
    # 1. จำแนกประเภทพื้นฐาน
    g_type = "Full Game" if game.get('type') == "Game" else game.get('type', 'Full Game')
    
    # 2. พยายามดึงจาก RAWG (ถ้า Config ถูกต้อง)
    found_genres = get_genres_from_rawg(title)
    
    # 3. ระบบจำแนกตาม Keyword (อ้างอิงตาม Genres ที่คุณกำหนด)
    # ถ้า RAWG ไม่เจอ เราจะใช้ระบบนี้ดึงออกมาให้ครบ
    if not found_genres:
        # ลิสต์คำจำแนกตามที่คุณต้องการ
        category_map = {
            "Action": ["action", "fighting", "hack and slash", "beat em up"],
            "Adventure": ["adventure", "exploration", "puzzle"],
            "RPG": ["rpg", "role-playing", "arpg", "jrpg", "level up"],
            "Strategy": ["strategy", "tactic", "rts", "turn-based", "moba"],
            "Simulation": ["simulation", "simulator", "management", "building"],
            "Shooting": ["shooting", "fps", "tps", "shooter"],
            "Horror": ["horror", "scary", "survival horror"],
            "Online": ["mmorpg", "mmo", "multiplayer online"],
            "Racing": ["racing", "driving", "car"],
            "Sandbox": ["sandbox", "open world"],
            "Platformer": ["platformer", "2d retro", "jump", "pixel", "side-scroller"]
        }
        
        for genre, keys in category_map.items():
            if any(key in full_text for key in keys):
                found_genres.append(genre)

    # 4. รวมผลลัพธ์ (Full Game | แนว1 | แนว2)
    if found_genres:
        unique_genres = list(dict.fromkeys(found_genres))
        # ทำให้มั่นใจว่า "Full Game" หรือ "DLC" อยู่หน้าสุดเสมอ
        return f"{g_type} | {' | '.join(unique_genres[:3])}"
    
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

