from __future__ import annotations

from stock_alerts import telegram


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


def test_send_telegram_message_retries_rate_limit(monkeypatch) -> None:
    responses = [
        _FakeResponse(429, {"parameters": {"retry_after": 2}}),
        _FakeResponse(200),
    ]
    sleep_calls: list[int] = []

    def fake_post(url, json, timeout):
        assert json["disable_web_page_preview"] is True
        assert timeout == telegram.TELEGRAM_API_TIMEOUT_SECONDS
        return responses.pop(0)

    monkeypatch.setattr(telegram.requests, "post", fake_post)
    monkeypatch.setattr(telegram.time, "sleep", lambda seconds: sleep_calls.append(seconds))

    telegram.send_telegram_message("token", "chat", "hello")

    assert sleep_calls == [3]


def test_send_telegram_message_rejects_oversized_text_before_posting(monkeypatch) -> None:
    post_called = False

    def fake_post(url, json, timeout):
        nonlocal post_called
        post_called = True
        return _FakeResponse(200)

    monkeypatch.setattr(telegram.requests, "post", fake_post)

    long_text = "x" * (telegram.TELEGRAM_MAX_MESSAGE_LENGTH + 1)
    try:
        telegram.send_telegram_message("token", "chat", long_text)
    except telegram.TelegramError as exc:
        assert "too long" in str(exc)
    else:
        raise AssertionError("expected TelegramError")

    assert post_called is False
