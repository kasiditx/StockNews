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
    max_news_lookups_per_run: int | None,
    min_score_to_alert: int,
    top_alerts_per_run: int | None,
) -> int:
    scanned_count = 0
    below_threshold_count = 0
    skipped_count = 0
    matched_reports: list[StockReport] = []
    for profile in profiles:
        scanned_count += 1
        try:
            report = build_technical_report(profile)
        except (MarketDataError, ValueError) as exc:
            skipped_count += 1
            LOGGER.debug("Skipping %s: %s", profile.ticker, exc)
            continue

        if report.signal.score < min_score_to_alert:
            below_threshold_count += 1
            LOGGER.debug(
                "Skipping %s because score %s is below threshold %s",
                profile.ticker,
                report.signal.score,
                min_score_to_alert,
            )
            continue

        matched_reports.append(report)

    LOGGER.info(
        "Scanned %s stock(s): %s matched, %s below threshold, %s skipped",
        scanned_count,
        len(matched_reports),
        below_threshold_count,
        skipped_count,
    )
    selected_reports = _select_reports(matched_reports, top_alerts_per_run)
    if not selected_reports:
        LOGGER.info("No stocks matched the alert threshold")
        return 0

    LOGGER.info(
        "Preparing digest for %s matched stock(s); fetching news for up to %s report(s)",
        len(selected_reports),
        max_news_lookups_per_run if max_news_lookups_per_run is not None else "all",
    )
    enriched_reports, unavailable_news_count = attach_news_to_reports(
        selected_reports,
        max_news_per_symbol=max_news_per_symbol,
        max_news_lookups_per_run=max_news_lookups_per_run,
    )
    if unavailable_news_count:
        LOGGER.info("News unavailable for %s selected stock(s)", unavailable_news_count)
    enriched_reports = _sort_reports_by_opportunity(enriched_reports)
    message_count = _count_chunks(enriched_reports, REPORTS_PER_TELEGRAM_MESSAGE)
    LOGGER.info("Sending %s Telegram digest message(s)", message_count)
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
                message_count=message_count,
            ),
        )
    return len(selected_reports)


def watch(
    profiles: Iterable[StockProfile],
    bot_token: str,
    chat_id: str,
    max_news_per_symbol: int,
    max_news_lookups_per_run: int | None,
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
            max_news_lookups_per_run=max_news_lookups_per_run,
            min_score_to_alert=min_score_to_alert,
            top_alerts_per_run=top_alerts_per_run,
        )
        LOGGER.info("Sent %s Telegram alert(s)", sent_count)
        time.sleep(interval_minutes * 60)


def build_stock_report(profile: StockProfile, max_news_per_symbol: int) -> StockReport:
    report = build_technical_report(profile)
    enriched_report, _ = attach_news(report, max_news_per_symbol=max_news_per_symbol)
    return enriched_report


def attach_news_to_reports(
    reports: list[StockReport],
    max_news_per_symbol: int,
    max_news_lookups_per_run: int | None,
) -> tuple[list[StockReport], int]:
    if max_news_per_symbol <= 0 or max_news_lookups_per_run == 0:
        return reports, 0

    news_lookup_limit = len(reports) if max_news_lookups_per_run is None else max_news_lookups_per_run
    enriched_reports: list[StockReport] = []
    unavailable_news_count = 0
    for index, report in enumerate(reports):
        if index >= news_lookup_limit:
            enriched_reports.append(report)
            continue

        enriched_report, news_available = attach_news(
            report,
            max_news_per_symbol=max_news_per_symbol,
        )
        if not news_available:
            unavailable_news_count += 1
        enriched_reports.append(enriched_report)
    return enriched_reports, unavailable_news_count


def build_technical_report(profile: StockProfile) -> StockReport:
    history = fetch_price_history(profile.ticker)
    signal = analyze_technical_signal(profile.ticker, history)
    return StockReport(profile=profile, signal=signal, news=())


def attach_news(report: StockReport, max_news_per_symbol: int) -> tuple[StockReport, bool]:
    if max_news_per_symbol <= 0:
        return report, True

    try:
        news = fetch_news(report.profile.ticker, max_news_per_symbol)
    except NewsFetchError as exc:
        LOGGER.debug("News unavailable for %s: %s", report.profile.ticker, exc)
        return StockReport(profile=report.profile, signal=report.signal, news=()), False
    return StockReport(profile=report.profile, signal=report.signal, news=news), bool(news)


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


def _sort_reports_by_opportunity(reports: list[StockReport]) -> list[StockReport]:
    return sorted(
        reports,
        key=lambda report: (
            _calculate_opportunity_score(report),
            report.signal.score,
            report.signal.change_percent,
        ),
        reverse=True,
    )


def _calculate_opportunity_score(report: StockReport) -> int:
    strongest_news_score = max((news_item.sentiment_score for news_item in report.news), default=0)
    return report.signal.score + strongest_news_score


def _chunk_reports(reports: list[StockReport], chunk_size: int) -> list[list[StockReport]]:
    return [reports[index : index + chunk_size] for index in range(0, len(reports), chunk_size)]


def _count_chunks(reports: list[StockReport], chunk_size: int) -> int:
    if not reports:
        return 0
    return ((len(reports) - 1) // chunk_size) + 1
