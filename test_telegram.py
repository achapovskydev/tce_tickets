#!/usr/bin/env python3
"""
Тестовый скрипт для проверки отправки в Telegram
"""
import os
from dotenv import load_dotenv
import requests

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        print(f"Отправка сообщения в Telegram...")
        print(f"URL: {url}")
        print(f"Chat ID: {CHAT_ID}")
        r = requests.post(url, data=payload, timeout=15)
        r.raise_for_status()
        print("✅ Сообщение успешно отправлено!")
        print(f"Ответ от Telegram: {r.json()}")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Ответ сервера: {e.response.text}")
        return False

if __name__ == "__main__":
    test_message = "🧪 <b>Тестовое сообщение</b>\n\nЕсли вы получили это сообщение, значит Telegram бот работает корректно!"
    send_telegram(test_message)
