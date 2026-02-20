def send_to_discord(game):
    deep_link = game['open_giveaway_url'] # ลิงก์ตรงไปหน้ากดรับเกม
    payload = {
        "embeds": [{
            "title": f"🚀 กดรับเกม: {game['title']}",
            "description": (
                f"**🎮 Platform:** {game['platforms']}\n"
                f"**💰 Worth:** {game['worth']}\n\n"
                f"**👇 คลิกที่ชื่อเกมด้านบน หรือลิงก์นี้เพื่อรับเกม:**\n"
                f"[Click to Claim Game]({deep_link})"
            ),
            "url": deep_link,
            "color": 5763719,
            "image": {"url": game['thumbnail']},
            "footer": {"text": "GamerPower Updates • แตะลิงก์แล้วกดรับได้เลย!"}
        }]
    }
    requests.post(WEBHOOK_URL, json=payload)
