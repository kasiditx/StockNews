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
            adx=28.0,
            atr_percent=3.0,
            bollinger_position=0.8,
            distance_from_high_percent=-2.0,
            trend="ขาขึ้นแข็งแรง",
            reasons=("ราคาอยู่เหนือ SMA20", "Volume สูง"),
            risk_flags=("ATR สูง",),
            rsi_fast=60.0,
            rsi_slow=52.0,
            plus_di=30.0,
            minus_di=15.0,
            atr_stop_loss=191.0,
            atr_take_profit_2x=212.0,
            atr_take_profit_3x=218.0,
            technical_plan=("SMA setup: trend ขาขึ้นระยะสั้น",),
        ),
        news=(
            NewsItem(
                title="Apple news",
                link="https://example.com",
                summary="Apple reported a new product catalyst.",
                sentiment="positive",
                sentiment_score=2,
                published="2026-05-15T16:22:53Z",
            ),
        ),
    )

    message = build_digest_message(reports=[report], scanned_count=100, matched_count=5)

    assert "📈 Stock Opportunity Digest" in message
    assert "#1 📌 AAPL - Apple" in message
    assert "🏢 ทำอะไร: Consumer technology" in message
    assert "🧩 จำเป็นต่อ:" in message
    assert "🔮 โอกาสขึ้น:" in message
    assert "🧭 SOP next step:" in message
    assert "🔎 สแกน 100 ตัว" in message
    assert "🧭 ชุดที่ 1/1" in message
    assert "✅ เหตุผล:" in message
    assert "🧾 สรุปข่าว: Apple reported a new product catalyst." in message
    assert "🕒 เวลา: 2026-05-15T16:22:53Z" in message
    assert "📈 Trend: ขาขึ้นแข็งแรง" in message
    assert "RSI5/14/21:" in message
    assert "ATR stop/TP:" in message
    assert "🗺️ Technical plan:" in message
    assert "🗞️ Tone: บวก (+2)" in message
    assert "🧠 วิเคราะห์ข่าว:" in message
    assert "🔥 ข่าวบวกแรง" in message
    assert "opportunity 6" in message
    assert "⚠️ จุดที่ต้องระวัง:" in message
    assert "ไม่ใช่การการันตี" in message


def test_build_digest_message_can_continue_rank_across_chunks() -> None:
    report = StockReport(
        profile=StockProfile(ticker="MSFT", name="Microsoft", business="Cloud software"),
        signal=TechnicalSignal(
            ticker="MSFT",
            score=5,
            stance="น่าจับตามองมาก",
            close_price=400.0,
            change_percent=1.2,
            rsi=58.0,
            sma_20=390.0,
            sma_50=370.0,
            macd=1.5,
            macd_signal=1.0,
            adx=25.0,
            atr_percent=2.0,
            bollinger_position=0.7,
            distance_from_high_percent=-3.0,
            trend="ขาขึ้นแข็งแรง",
            reasons=("Momentum ยังดี",),
            risk_flags=(),
        ),
        news=(),
    )

    message = build_digest_message(
        reports=[report],
        scanned_count=100,
        matched_count=10,
        message_index=2,
        message_count=4,
        rank_start=4,
    )

    assert "#4 📌 MSFT - Microsoft" in message
