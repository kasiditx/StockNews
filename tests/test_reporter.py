from __future__ import annotations

from stock_alerts.models import NewsItem, StockProfile, StockReport, TechnicalSignal
from stock_alerts.reporter import build_digest_message


def test_build_digest_message_includes_ranked_context_and_warning() -> None:
    report = StockReport(
        profile=StockProfile(ticker="AAPL", name="Apple", business="Consumer technology"),
        signal=TechnicalSignal(
            ticker="AAPL",
            score=4,
            stance="น่าจับตามองมาก",
            close_price=200.0,
            change_percent=2.5,
            rsi=55.0,
            sma_20=190.0,
            sma_50=180.0,
            macd=1.2,
            macd_signal=1.0,
            reasons=("ราคาอยู่เหนือ SMA20", "Volume สูง"),
        ),
        news=(
            NewsItem(
                title="Apple news",
                link="https://example.com",
                summary="Apple reported a new product catalyst.",
            ),
        ),
    )

    message = build_digest_message(reports=[report], scanned_count=100, matched_count=5)

    assert "📈 Stock Opportunity Digest" in message
    assert "#1 📌 AAPL - Apple" in message
    assert "🔎 สแกน 100 ตัว" in message
    assert "🧭 ชุดที่ 1/1" in message
    assert "✅ เหตุผล:" in message
    assert "🧾 สรุปข่าว: Apple reported a new product catalyst." in message
    assert "ไม่ใช่การการันตี" in message
