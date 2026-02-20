import discord
import requests
import json
import os
import re
from datetime import datetime, timedelta

# ดึงข้อมูลจาก GitHub Secrets
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_SALE_CHANNEL_ID'))
RAWG_API_KEY = os.getenv('RAWG_API_KEY')
HISTORY_FILE = "sale_history.json"

def get_genres_from_rawg(game_name):
    if not RAWG_API_KEY: return []
    try:
        clean_name = re.sub(r'\(.*?\)|(?i)giveaway|free|download|pack', '', game_name)
        clean_name = re.sub(r'[^\w\s]', '', clean_name).strip()
        url = f"https://api.rawg.io/api/games?key={RAWG_API_KEY}&search={clean_name}&page_size=1"
        res = requests.get(url, timeout=10).json()
        if res.get('results'):
            return [g['name'] for g in res['results'][0].get('genres', [])]
    except: return []
    return []

def get_detailed_genres(game_title):
    rawg_genres = get_genres_from_rawg(game_title)
    backup_genres = []
    keywords = {
        "Action": ["action", "fighting", "hack", "jedi", "warrior"],
        "Adventure": ["adventure", "exploration", "survivor", "journey"],
        "RPG": ["rpg", "role-playing", "fantasy"],
        "Strategy": ["strategy", "tactic", "sim", "management"],
        "Shooting": ["shooting", "fps", "shooter", "sniper"],
        "Platformer": ["platformer", "2d", "retro"],
        "Indie": ["indie"]
    }
    title_lower = game_title.lower()
    for genre, keys in keywords.items():
        if any(key in title_lower for key in keys):
            backup_genres.append(genre)
    combined = rawg_genres + backup_genres
    final_list = []
    for item in combined:
        if item not in final_list: final_list.append(item)
    return " | ".join(final_list[:5]) if final_list else "Action | Adventure"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

client = discord.Client(intents=discord.Intents.
