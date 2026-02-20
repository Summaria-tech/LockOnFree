import discord
from discord.ext import commands
import requests
import os
import asyncio

# --- ตั้งค่าส่วนตัว (ใส่ใน GitHub Secrets) ---
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID')) # ID ของห้องที่ต้องการให้บอทส่ง
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

# --- สร้าง View สำหรับปุ่มกด (Link Button) ---
class ClaimView(discord.ui.View):
    def __init__(self, url):
        super().__init__(timeout=None)
        # สร้างปุ่มลิงก์ (ปุ่มประเภท Link จะเป็นสีเทาโดยอัตโนมัติใน Discord)
        # แต่เราจะใส่ Emoji ให้ดูเด่นเหมือนปุ่มกด
        self.add_item(discord.ui.Button(
            label='CLAIM GAME NOW', 
            url=url, 
            style=discord.ButtonStyle.link,
            emoji='🎁'
        ))

async def check_and_send(bot):
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ หาห้องไม่เจอ! ตรวจสอบ CHANNEL_ID")
        return

    sent_ids = get_sent_games()
    api_url = "https://www.gamerpower.com/api/giveaways"
    
    try:
        res = requests.get(api_url)
        if res.status_code == 200:
            games = res.json()
            for game in reversed(games[:5]):
                game_id = str(game['id'])
                if game_id not in sent_ids:
                    # สร้าง Embed สวยๆ
                    embed = discord.Embed(
                        title=f"🔥 {game['title']}",
                        description=f"{game['description'][:150]}...",
                        color=0xff4747, # สีแดง
                        url=game['open_giveaway_url']
                    )
                    embed.set_image(url=game['image'] or game['thumbnail'])
                    embed.add_field(name="💻 Platform", value=f"**{game['platforms']}**", inline=True)
                    embed.add_field(name="💰 Worth", value=f"~~{game['worth']}~~ **FREE**", inline=True)
                    embed.set_footer(text="GamerPower API • LockOnFree")

                    # ส่งข้อความพร้อมปุ่ม
                    await channel.send(embed=embed, view=ClaimView(game['open_giveaway_url']))
                    save_sent_game(game_id)
                    print(f"✅ ส่งเกม {game['title']} สำเร็จ")
    except Exception as e:
        print(f"❌ Error: {e}")

# --- รันบอท ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'🤖 บอท {bot.user} พร้อมทำงาน!')
    await check_and_send(bot)
    await bot.close() # สั่งปิดบอทเมื่อทำงานเสร็จเพื่อให้ GitHub Actions จบงาน

if __name__ == "__main__":
    if TOKEN and CHANNEL_ID:
        bot.run(TOKEN)
    else:
        print("❌ ขาด TOKEN หรือ CHANNEL_ID ในระบบ Secrets")
