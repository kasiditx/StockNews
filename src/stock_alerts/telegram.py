from __future__ import annotations

import requests


TELEGRAM_API_TIMEOUT_SECONDS = 15
TELEGRAM_MAX_MESSAGE_LENGTH = 4096


class TelegramError(RuntimeError):
    """Raised when Telegram rejects a message."""


def send_telegram_message(bot_token: str, chat_id: str, text: str) -> None:
    if len(text) > TELEGRAM_MAX_MESSAGE_LENGTH:
        text = text[: TELEGRAM_MAX_MESSAGE_LENGTH - 20] + "\n...(truncated)"

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    response = requests.post(
        url,
        json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
        timeout=TELEGRAM_API_TIMEOUT_SECONDS,
    )
    if response.status_code >= 400:
        raise TelegramError(f"Telegram sendMessage failed with HTTP {response.status_code}")
