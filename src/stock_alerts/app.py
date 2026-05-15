from __future__ import annotations

import logging
import time
from collections.abc import Iterable

from stock_alerts.analysis import analyze_technical_signal
from stock_alerts.market_data import MarketDataError, fetch_price_history
from stock_alerts.models import StockProfile, StockReport
from stock_alerts.news import NewsFetchError, fetch_news
from stock_alerts.reporter import build_digest_message
from stock_alerts.telegram import send_telegram_message


LOGGER = logging.getLogger(__name__)
REPORTS_PER_TELEGRAM_MESSAGE = 10


def run_once(
    profiles: Iterable[StockProfile],
    bot_token: str,
    chat_id: str,
    max_news_per_symbol: int,
    min_score_to_alert: int,
    top_alerts_per_run: int | None,
) -> int:
    scanned_count = 0
    matched_reports: list[StockReport] = []
    for profile in profiles:
        scanned_count += 1
        try:
            report = build_technical_report(profile)
        except (MarketDataError, ValueError) as exc:
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

        matched_reports.append(report)

    LOGGER.info("Scanned %s stock(s)", scanned_count)
    selected_reports = _select_reports(matched_reports, top_alerts_per_run)
    if not selected_reports:
        LOGGER.info("No stocks matched the alert threshold")
        return 0

    enriched_reports = [
        attach_news(report, max_news_per_symbol=max_news_per_symbol) for report in selected_reports
    ]
    for message_index, report_chunk in enumerate(
        _chunk_reports(enriched_reports, REPORTS_PER_TELEGRAM_MESSAGE),
        start=1,
    ):
        send_telegram_message(
            bot_token,
            chat_id,
            build_digest_message(
                reports=report_chunk,
                scanned_count=scanned_count,
                matched_count=len(matched_reports),
                message_index=message_index,
                message_count=_count_chunks(enriched_reports, REPORTS_PER_TELEGRAM_MESSAGE),
            ),
        )
    return len(selected_reports)


def watch(
    profiles: Iterable[StockProfile],
    bot_token: str,
    chat_id: str,
    max_news_per_symbol: int,
    min_score_to_alert: int,
    top_alerts_per_run: int | None,
    interval_minutes: int,
) -> None:
    while True:
        sent_count = run_once(
            profiles=profiles,
            bot_token=bot_token,
            chat_id=chat_id,
            max_news_per_symbol=max_news_per_symbol,
            min_score_to_alert=min_score_to_alert,
            top_alerts_per_run=top_alerts_per_run,
        )
        LOGGER.info("Sent %s Telegram alert(s)", sent_count)
        time.sleep(interval_minutes * 60)


def build_stock_report(profile: StockProfile, max_news_per_symbol: int) -> StockReport:
    report = build_technical_report(profile)
    return attach_news(report, max_news_per_symbol=max_news_per_symbol)


def build_technical_report(profile: StockProfile) -> StockReport:
    history = fetch_price_history(profile.ticker)
    signal = analyze_technical_signal(profile.ticker, history)
    return StockReport(profile=profile, signal=signal, news=())


def attach_news(report: StockReport, max_news_per_symbol: int) -> StockReport:
    if max_news_per_symbol <= 0:
        return report

    try:
        news = fetch_news(report.profile.ticker, max_news_per_symbol)
    except NewsFetchError as exc:
        LOGGER.warning("News unavailable for %s: %s", report.profile.ticker, exc)
        news = ()
    return StockReport(profile=report.profile, signal=report.signal, news=news)


def _select_reports(reports: list[StockReport], limit: int | None) -> list[StockReport]:
    sorted_reports = sorted(
        reports,
        key=lambda report: (
            report.signal.score,
            report.signal.change_percent,
            report.signal.close_price,
        ),
        reverse=True,
    )
    if limit is None:
        return sorted_reports
    return sorted_reports[:limit]


def _chunk_reports(reports: list[StockReport], chunk_size: int) -> list[list[StockReport]]:
    return [reports[index : index + chunk_size] for index in range(0, len(reports), chunk_size)]


def _count_chunks(reports: list[StockReport], chunk_size: int) -> int:
    if not reports:
        return 0
    return ((len(reports) - 1) // chunk_size) + 1
