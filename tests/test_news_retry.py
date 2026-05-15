from __future__ import annotations

from stock_alerts import news


class _FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


def test_get_with_retry_retries_rate_limit(monkeypatch) -> None:
    responses = [_FakeResponse(429), _FakeResponse(200)]
    sleep_calls: list[int] = []

    def fake_get(url, headers, timeout):
        assert headers["User-Agent"]
        assert timeout == news.REQUEST_TIMEOUT_SECONDS
        return responses.pop(0)

    monkeypatch.setattr(news.requests, "get", fake_get)
    monkeypatch.setattr(news.time, "sleep", lambda seconds: sleep_calls.append(seconds))

    response = news._get_with_retry("https://example.com/rss")

    assert response.status_code == 200
    assert sleep_calls == [1]
