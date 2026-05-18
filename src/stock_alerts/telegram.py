from __future__ import annotations

import time

import requests


TELEGRAM_API_TIMEOUT_SECONDS = 15
TELEGRAM_MAX_MESSAGE_LENGTH = 4096
TELEGRAM_MAX_RETRIES = 3
TELEGRAM_DEFAULT_RETRY_AFTER_SECONDS = 3


class TelegramError(RuntimeError):
    """Raised when Telegram rejects a message."""


def send_telegram_message(bot_token: str, chat_id: str, text: str) -> None:
    if len(text) > TELEGRAM_MAX_MESSAGE_LENGTH:
        raise TelegramError(
            f"Telegram message is too long: {len(text)} characters "
            f"(max {TELEGRAM_MAX_MESSAGE_LENGTH})"
        )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    response: requests.Response | None = None
    for attempt in range(TELEGRAM_MAX_RETRIES + 1):
        response = requests.post(
            url,
            json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
            timeout=TELEGRAM_API_TIMEOUT_SECONDS,
        )
        if response.status_code != 429:
            break
        if attempt < TELEGRAM_MAX_RETRIES:
            time.sleep(_read_retry_after(response))

    if response is None:
        raise TelegramError("Telegram sendMessage failed before receiving a response")
    if response.status_code >= 400:
        raise TelegramError(f"Telegram sendMessage failed with HTTP {response.status_code}")


def _read_retry_after(response: requests.Response) -> int:
    try:
        payload = response.json()
    except ValueError:
        return TELEGRAM_DEFAULT_RETRY_AFTER_SECONDS

    if not isinstance(payload, dict):
        return TELEGRAM_DEFAULT_RETRY_AFTER_SECONDS
    parameters = payload.get("parameters")
    if not isinstance(parameters, dict):
        return TELEGRAM_DEFAULT_RETRY_AFTER_SECONDS
    retry_after = parameters.get("retry_after")
    if not isinstance(retry_after, int) or retry_after < 0:
        return TELEGRAM_DEFAULT_RETRY_AFTER_SECONDS
    return retry_after + 1
