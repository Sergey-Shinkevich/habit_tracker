import requests
from django.conf import settings


def send_telegram_message(chat_id: int, text: str) -> None:
    """Отправляет сообщение пользователю в Telegram по его chat_id."""
    token = settings.TG_BOT_TOKEN
    if not token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    requests.post(url, json=payload, timeout=10)
    