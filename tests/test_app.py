from __future__ import annotations

from stock_alerts.app import _chunk_reports_for_telegram, run_once
from stock_alerts.models import NewsItem, StockProfile, StockReport, TechnicalSignal


def test_run_once_fetches_news_only_for_selected_reports(monkeypatch) -> None:
    reports = {
        "AAA": _build_report("AAA", score=5, change_percent=1.0),
        "BBB": _build_report("BBB", score=4, change_percent=1.0),
        "CCC": _build_report("CCC", score=3, change_percent=1.0),
    }
    fetched_news_for: list[str] = []
    sent_messages: list[str] = []

    monkeypatch.setattr("stock_alerts.app.build_technical_report", lambda profile: reports[profile.ticker])
    monkeypatch.setattr("stock_alerts.app.fetch_news", lambda ticker, limit: fetched_news_for.append(ticker) or ())
    monkeypatch.setattr(
        "stock_alerts.app.send_telegram_message",
        lambda bot_token, chat_id, text: sent_messages.append(text),
    )

    sent_count = run_once(
        profiles=[StockProfile(ticker=ticker, name=ticker, business="Test") for ticker in reports],
        bot_token="token",
        chat_id="chat",
        max_news_per_symbol=3,
        max_news_lookups_per_run=None,
        min_score_to_alert=2,
        top_alerts_per_run=2,
    )

    assert sent_count == 2
    assert fetched_news_for == ["AAA", "BBB"]
    assert len(sent_messages) == 1


def test_run_once_sends_all_matched_reports_when_limit_is_disabled(monkeypatch) -> None:
    reports = {
        "AAA": _build_report("AAA", score=5, change_percent=1.0),
        "BBB": _build_report("BBB", score=4, change_percent=1.0),
        "CCC": _build_report("CCC", score=3, change_percent=1.0),
    }
    fetched_news_for: list[str] = []
    sent_messages: list[str] = []

    monkeypatch.setattr("stock_alerts.app.build_technical_report", lambda profile: reports[profile.ticker])
    monkeypatch.setattr("stock_alerts.app.fetch_news", lambda ticker, limit: fetched_news_for.append(ticker) or ())
    monkeypatch.setattr(
        "stock_alerts.app.send_telegram_message",
        lambda bot_token, chat_id, text: sent_messages.append(text),
    )

    sent_count = run_once(
        profiles=[StockProfile(ticker=ticker, name=ticker, business="Test") for ticker in reports],
        bot_token="token",
        chat_id="chat",
        max_news_per_symbol=3,
        max_news_lookups_per_run=None,
        min_score_to_alert=2,
        top_alerts_per_run=None,
    )

    assert sent_count == 3
    assert fetched_news_for == ["AAA", "BBB", "CCC"]
    assert len(sent_messages) == 1


def test_run_once_sorts_digest_by_news_adjusted_opportunity(monkeypatch) -> None:
    reports = {
        "TECH": _build_report("TECH", score=5, change_percent=1.0),
        "NEWS": _build_report("NEWS", score=4, change_percent=0.5),
    }

    def fake_fetch_news(ticker: str, limit: int):
        if ticker == "NEWS":
            return (
                NewsItem(
                    title="NEWS beats profit estimates and raises guidance",
                    link="https://example.com/news",
                    summary="NEWS beats profit estimates and raises guidance.",
                    sentiment="positive",
                    sentiment_score=3,
                ),
            )
        return ()

    sent_messages: list[str] = []
    monkeypatch.setattr("stock_alerts.app.build_technical_report", lambda profile: reports[profile.ticker])
    monkeypatch.setattr("stock_alerts.app.fetch_news", fake_fetch_news)
    monkeypatch.setattr(
        "stock_alerts.app.send_telegram_message",
        lambda bot_token, chat_id, text: sent_messages.append(text),
    )

    run_once(
        profiles=[StockProfile(ticker=ticker, name=ticker, business="Test") for ticker in reports],
        bot_token="token",
        chat_id="chat",
        max_news_per_symbol=3,
        max_news_lookups_per_run=None,
        min_score_to_alert=2,
        top_alerts_per_run=None,
    )

    assert sent_messages
    assert sent_messages[0].find("#1 📌 NEWS") < sent_messages[0].find("#2 📌 TECH")


def test_run_once_limits_news_lookups_after_technical_filter(monkeypatch) -> None:
    reports = {
        "AAA": _build_report("AAA", score=5, change_percent=1.0),
        "BBB": _build_report("BBB", score=4, change_percent=1.0),
        "CCC": _build_report("CCC", score=3, change_percent=1.0),
    }
    fetched_news_for: list[str] = []
    sent_messages: list[str] = []

    monkeypatch.setattr("stock_alerts.app.build_technical_report", lambda profile: reports[profile.ticker])
    monkeypatch.setattr("stock_alerts.app.fetch_news", lambda ticker, limit: fetched_news_for.append(ticker) or ())
    monkeypatch.setattr(
        "stock_alerts.app.send_telegram_message",
        lambda bot_token, chat_id, text: sent_messages.append(text),
    )

    sent_count = run_once(
        profiles=[StockProfile(ticker=ticker, name=ticker, business="Test") for ticker in reports],
        bot_token="token",
        chat_id="chat",
        max_news_per_symbol=3,
        max_news_lookups_per_run=1,
        min_score_to_alert=2,
        top_alerts_per_run=None,
    )

    assert sent_count == 3
    assert fetched_news_for == ["AAA"]


def test_digest_chunks_are_limited_by_message_length() -> None:
    reports = [
        _build_report(f"AAA{index}", score=5, change_percent=1.0, reason="x" * 500)
        for index in range(4)
    ]

    chunks = _chunk_reports_for_telegram(
        reports=reports,
        scanned_count=100,
        matched_count=4,
        max_length=1100,
    )

    assert len(chunks) > 1
    assert all(chunks)


def _build_report(
    ticker: str,
    score: int,
    change_percent: float,
    reason: str = "Test reason",
) -> StockReport:
    return StockReport(
        profile=StockProfile(ticker=ticker, name=ticker, business="Test"),
        signal=TechnicalSignal(
            ticker=ticker,
            score=score,
            stance="น่าติดตาม",
            close_price=10.0,
            change_percent=change_percent,
            rsi=50.0,
            sma_20=9.0,
            sma_50=8.0,
            macd=1.0,
            macd_signal=0.9,
            adx=30.0,
            atr_percent=2.0,
            bollinger_position=0.8,
            distance_from_high_percent=-1.0,
            trend="ขาขึ้นแข็งแรง",
            reasons=(reason,),
            risk_flags=(),
        ),
        news=(),
    )
