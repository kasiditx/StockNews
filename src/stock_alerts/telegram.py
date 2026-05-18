from __future__ import annotations

import time

import requests


TELEGRAM_API_TIMEOUT_SECONDS = 15
TELEGRAM_MAX_MESSAGE_LENGTH = 4096
TELEGRAM_MAX_RETRIES = 3
TELEGRAM_DEFAULT_RETRY_AFTER_SECONDS = 3
TELEGRAM_POLL_TIMEOUT_SECONDS = 20


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


def send_telegram_messages(bot_token: str, chat_id: str, text: str) -> None:
    for message in split_telegram_text(text):
        send_telegram_message(bot_token, chat_id, message)
        time.sleep(1)


def split_telegram_text(text: str) -> tuple[str, ...]:
    if len(text) <= TELEGRAM_MAX_MESSAGE_LENGTH:
        return (text,)

    chunks: list[str] = []
    current_lines: list[str] = []
    current_length = 0
    for line in text.splitlines():
        line_length = len(line) + 1
        if current_lines and current_length + line_length > TELEGRAM_MAX_MESSAGE_LENGTH:
            chunks.append("\n".join(current_lines))
            current_lines = [line]
            current_length = line_length
            continue
        if line_length > TELEGRAM_MAX_MESSAGE_LENGTH:
            chunks.extend(_split_long_line(line))
            current_lines = []
            current_length = 0
            continue
        current_lines.append(line)
        current_length += line_length

    if current_lines:
        chunks.append("\n".join(current_lines))
    return tuple(chunks)


def fetch_telegram_updates(
    bot_token: str,
    offset: int | None,
    timeout: int = TELEGRAM_POLL_TIMEOUT_SECONDS,
) -> tuple[dict, ...]:
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    payload: dict[str, object] = {
        "timeout": timeout,
        "allowed_updates": ["message"],
    }
    if offset is not None:
        payload["offset"] = offset

    response = requests.post(url, json=payload, timeout=timeout + TELEGRAM_API_TIMEOUT_SECONDS)
    if response.status_code >= 400:
        raise TelegramError(f"Telegram getUpdates failed with HTTP {response.status_code}")

    try:
        body = response.json()
    except ValueError as exc:
        raise TelegramError("Telegram getUpdates returned invalid JSON") from exc
    if not isinstance(body, dict) or body.get("ok") is not True:
        raise TelegramError("Telegram getUpdates returned an unsuccessful response")
    updates = body.get("result", ())
    if not isinstance(updates, list):
        raise TelegramError("Telegram getUpdates result was not a list")
    return tuple(update for update in updates if isinstance(update, dict))


def _split_long_line(line: str) -> list[str]:
    return [
        line[index : index + TELEGRAM_MAX_MESSAGE_LENGTH]
        for index in range(0, len(line), TELEGRAM_MAX_MESSAGE_LENGTH)
    ]


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
