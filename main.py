import requests
import os

# 1. ดึง Webhook
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')

def test_send():
    print(f"Checking Webhook URL...")
    if not WEBHOOK_URL:
        print("❌ Error: Webhook URL is empty!")
        return

    # 2. ลองส่งข้อความทดสอบแบบง่ายที่สุด
    payload = {
        "content": "🚀 บอทรายงานตัว! ถ้าเห็นข้อความนี้แสดงว่าระบบเชื่อมต่อสำเร็จแล้ว"
    }
    
    try:
        r = requests.post(WEBHOOK_URL, json=payload)
        print(f"Status Code: {r.status_code}")
        if r.status_code == 204 or r.status_code == 200:
            print("✅ Send Success!")
        else:
            print(f"❌ Send Failed: {r.text}")
    except Exception as e:
        print(f"❌ Error occurred: {e}")

if __name__ == "__main__":
    test_send()
