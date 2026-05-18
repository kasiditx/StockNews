from __future__ import annotations

from stock_alerts.models import StockProfile, StockReport, TechnicalSignal
from stock_alerts.telegram_bot import TelegramBotState, handle_telegram_command, update_latest_reports


def test_handle_help_command_lists_supported_commands() -> None:
    response = handle_telegram_command(
        text="/help",
        profile_map={},
        max_news_per_symbol=3,
        top_alerts_per_run=10,
        state=TelegramBotState(),
    )

    assert "/analyze NVDA" in response
    assert "/top" in response


def test_handle_status_command_reports_runtime_limit() -> None:
    state = TelegramBotState()

    response = handle_telegram_command(
        text="/status",
        profile_map={},
        max_news_per_symbol=3,
        top_alerts_per_run=10,
        state=state,
    )

    assert "กำลังทำงาน" in response
    assert "Top alerts ต่อรอบ: 10" in response


def test_handle_top_command_uses_latest_reports() -> None:
    state = TelegramBotState()
    report = StockReport(
        profile=StockProfile(ticker="NVDA", name="NVIDIA", business="AI chips"),
        signal=TechnicalSignal(
            ticker="NVDA",
            score=6,
            stance="น่าจับตามองมาก",
            close_price=100.0,
            change_percent=3.0,
            rsi=55.0,
            sma_20=95.0,
            sma_50=90.0,
            macd=1.0,
            macd_signal=0.5,
            adx=30.0,
            atr_percent=2.5,
            bollinger_position=0.8,
            distance_from_high_percent=-1.5,
            trend="ขาขึ้นแข็งแรง",
            reasons=("Momentum ดี",),
            risk_flags=(),
        ),
        news=(),
    )
    update_latest_reports(state, reports=[report], scanned_count=100, matched_count=1)

    response = handle_telegram_command(
        text="/top",
        profile_map={},
        max_news_per_symbol=3,
        top_alerts_per_run=10,
        state=state,
    )

    assert "#1 NVDA" in response
    assert "opportunity 6" in response
