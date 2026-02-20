import discord
from discord.ext import commands
import requests
import os
import re  # <--- ต้องมีบรรทัดนี้ ไม่งั้นบอทจะ Error ตรง re.sub

# --- ดึงค่าจาก GitHub Secrets ---
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID')) if os.getenv('DISCORD_CHANNEL_ID') else None
RAWG_KEY = os.getenv('RAWG_API_KEY')
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
    """ดึงแนวเกมทั้งหมดที่ RAWG มี โดยล้างชื่อเกมให้สะอาดก่อนค้นหา"""
    if not RAWG_KEY: return []
    try:
        # ล้างชื่อเกม: ตัด (Steam), Giveaway, และอักขระพิเศษออกเพื่อให้ RAWG หาเจอ
        clean_name = re.sub(r'\(.*?\)|(?i)giveaway|free|download|pack', '', game_name)
        clean_name = re.sub(r'[^\w\s]', '', clean_name).strip()
        
        url = f"https://api.rawg.io/api/games?key={RAWG_KEY}&search={clean_name}&page_size=1"
        res = requests.get(url, timeout=5).json()
        
        if res.get('results'):
            # ดึง Genres ทั้งหมด (Action, Adventure, Indie ฯลฯ)
            return [g['name'] for g in res['results'][0].get('genres', [])]
    except Exception as e:
        print(f"RAWG Error: {e}")
    return []

def get_detailed_genres(game):
    title = game.get('title', '')
    desc = game.get('description', '').lower()
    
    # 1. ตรวจสอบประเภท (Full Game / DLC)
    g_type = "Full Game" if game.get('type') == "Game" else game.get('type', 'Full Game')
    
    # 2. ดึงแนวจาก RAWG
    rawg_genres = get_genres_from_rawg(title)
    
    # 3. แผนสำรอง: สแกน Keyword
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

    # 4. รวมข้อมูลและลบตัวซ้ำ
    combined = rawg_genres + backup_genres
    final_list = []
    for item in combined:
        if item not in final_list:
            final_list.append(item)

    if final_list:
        return f"{g_type} | {' | '.join(final_list[:5])}"
    
    return g_type

# --- ส่วนของ Discord Bot (คงเดิมตามที่คุณส่งมา) ---
class ClaimView(discord.ui.View):
    def __init__(self, url):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label='CLAIM GAME NOW', url=url, style=discord.ButtonStyle.link, emoji='🎁'))

# แก้ไขในฟังก์ชัน check_and_send
async def check_and_send(bot):
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return
    
    sent_ids = get_sent_games()
    res = requests.get("https://www.gamerpower.com/api/giveaways")
    
    if res.status_code == 200:
        games = res.json()
        # เช็ค 50 เกมล่าสุด
        for game in reversed(games[:50]):
            game_id = str(game['id'])
            
            if game_id not in sent_ids:
                # --- ส่วนที่เพิ่มเข้ามาเพื่อกันบอทส่งซ้ำตอนเริ่มใหม่ ---
                # ถ้าไฟล์ประวัติมีน้อย (เช่น < 5) ให้ถือว่าเป็นการเซ็ตอัพครั้งแรก 
                # ให้บันทึก ID ไปเลยโดยไม่ต้องส่ง Discord
                if len(sent_ids) < 10: 
                    save_sent_game(game_id)
                    continue
                # ----------------------------------------------

                genre_list = get_detailed_genres(game)
                # ... โค้ดส่ง Embed ตามปกติ ...
                
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


