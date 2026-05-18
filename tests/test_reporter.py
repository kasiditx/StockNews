from __future__ import annotations

from stock_alerts.models import NewsItem, StockProfile, StockReport, TechnicalSignal
from stock_alerts.reporter import build_digest_message, build_report_message


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


def test_build_report_message_uses_sop_format_and_short_news() -> None:
    report = StockReport(
        profile=StockProfile(
            ticker="APLD",
            name="Applied Digital",
            business="Technology / AI data center infrastructure",
            sector="Technology",
            industry="AI Data Center Infrastructure",
        ),
        signal=TechnicalSignal(
            ticker="APLD",
            score=5,
            stance="น่าจับตามองมาก",
            close_price=42.56,
            change_percent=-8.88,
            rsi=65.32,
            sma_20=37.97,
            sma_50=31.26,
            macd=4.04,
            macd_signal=3.48,
            adx=34.71,
            atr_percent=8.17,
            bollinger_position=0.7,
            distance_from_high_percent=-8.88,
            trend="ขาขึ้นแข็งแรง",
            reasons=("trend หลักเป็นขาขึ้น",),
            risk_flags=("ATR สูง",),
            rsi_fast=61.0,
            rsi_slow=59.0,
            plus_di=32.0,
            minus_di=12.0,
            atr_stop_loss=38.0,
            atr_take_profit_2x=47.0,
            atr_take_profit_3x=50.0,
            technical_plan=("ATR plan: stop ประมาณ 38.00",),
        ),
        news=(
            NewsItem(
                title="Applied Digital closes bridge loan for AI data center expansion",
                link="https://example.com/apld",
                summary="Applied Digital closed a large bridge loan to fund AI data center construction. "
                * 10,
                sentiment="positive",
                sentiment_score=2,
            ),
        ),
    )

    message = build_report_message(report)

    assert "🏢 ทำอะไร: Technology / AI data center infrastructure" in message
    assert "🧩 จำเป็นต่อ: โครงสร้างพื้นฐาน AI/data center" in message
    assert "🔮 โอกาสขึ้น:" in message
    assert "🧭 SOP next step:" in message
    assert "🧮 RSI5/14/21:" in message
    assert "🗺️ Technical plan:" in message
    assert "🧠 วิเคราะห์ข่าวรวม:" in message
    assert len(message) < 4096
