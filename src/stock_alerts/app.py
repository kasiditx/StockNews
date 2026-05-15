from __future__ import annotations

import logging
import time
from collections.abc import Iterable

from stock_alerts.analysis import analyze_technical_signal
from stock_alerts.market_data import MarketDataError, fetch_price_history
from stock_alerts.models import StockProfile, StockReport
from stock_alerts.news import NewsFetchError, fetch_news
from stock_alerts.reporter import build_report_message
from stock_alerts.telegram import send_telegram_message


LOGGER = logging.getLogger(__name__)


def run_once(
    profiles: Iterable[StockProfile],
    bot_token: str,
    chat_id: str,
    max_news_per_symbol: int,
    min_score_to_alert: int,
) -> int:
    sent_count = 0
    scanned_count = 0
    for profile in profiles:
        scanned_count += 1
        try:
            report = build_stock_report(profile, max_news_per_symbol)
        except (MarketDataError, NewsFetchError, ValueError) as exc:
            LOGGER.warning("Skipping %s: %s", profile.ticker, exc)
            continue

        if report.signal.score < min_score_to_alert:
            LOGGER.info(
                "Skipping %s because score %s is below threshold %s",
                profile.ticker,
                report.signal.score,
                min_score_to_alert,
            )
            continue

        send_telegram_message(bot_token, chat_id, build_report_message(report))
        sent_count += 1
    LOGGER.info("Scanned %s stock(s)", scanned_count)
    return sent_count


def watch(
    profiles: Iterable[StockProfile],
    bot_token: str,
    chat_id: str,
    max_news_per_symbol: int,
    min_score_to_alert: int,
    interval_minutes: int,
) -> None:
    while True:
        sent_count = run_once(
            profiles=profiles,
            bot_token=bot_token,
            chat_id=chat_id,
            max_news_per_symbol=max_news_per_symbol,
            min_score_to_alert=min_score_to_alert,
        )
        LOGGER.info("Sent %s Telegram alert(s)", sent_count)
        time.sleep(interval_minutes * 60)


def build_stock_report(profile: StockProfile, max_news_per_symbol: int) -> StockReport:
    history = fetch_price_history(profile.ticker)
    signal = analyze_technical_signal(profile.ticker, history)
    news = fetch_news(profile.ticker, max_news_per_symbol)
    return StockReport(profile=profile, signal=signal, news=news)
