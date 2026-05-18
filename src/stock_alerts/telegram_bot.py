from __future__ import annotations

import logging
import threading
import time
from collections.abc import Iterable
from dataclasses import dataclass, field

from stock_alerts.analysis import analyze_technical_signal
from stock_alerts.market_data import fetch_price_history
from stock_alerts.models import NewsItem, StockProfile, StockReport
from stock_alerts.news import NewsFetchError, fetch_news
from stock_alerts.reporter import build_report_message
from stock_alerts.sop import calculate_opportunity_score
from stock_alerts.telegram import (
    TelegramError,
    fetch_telegram_updates,
    send_telegram_messages,
)


LOGGER = logging.getLogger(__name__)
SUPPORTED_COMMANDS = ("/help", "/status", "/top", "/analyze", "/why", "/news")


@dataclass
class TelegramBotState:
    started_at: float = field(default_factory=time.time)
    last_reports: tuple[StockReport, ...] = ()
    last_scanned_count: int = 0
    last_matched_count: int = 0
    last_run_at: float | None = None


def start_telegram_command_bot(
    profiles: Iterable[StockProfile],
    bot_token: str,
    chat_id: str,
    max_news_per_symbol: int,
    top_alerts_per_run: int | None,
    state: TelegramBotState,
) -> threading.Thread:
    profile_map = _build_profile_map(profiles)
    thread = threading.Thread(
        target=_poll_commands,
        kwargs={
            "profile_map": profile_map,
            "bot_token": bot_token,
            "chat_id": chat_id,
            "max_news_per_symbol": max_news_per_symbol,
            "top_alerts_per_run": top_alerts_per_run,
            "state": state,
        },
        name="telegram-command-bot",
        daemon=True,
    )
    thread.start()
    return thread


def handle_telegram_command(
    text: str,
    profile_map: dict[str, StockProfile],
    max_news_per_symbol: int,
    top_alerts_per_run: int | None,
    state: TelegramBotState,
) -> str:
    normalized_text = text.strip()
    if not normalized_text:
        return _help_message()

    command, argument = _split_command(normalized_text)
    if command in {"/help", "help"}:
        return _help_message()
    if command == "/status":
        return _status_message(top_alerts_per_run=top_alerts_per_run, state=state)
    if command == "/top":
        return _top_message(state)
    if command in {"/analyze", "/why"}:
        return _analyze_ticker(argument, profile_map, max_news_per_symbol)
    if command == "/news":
        return _news_message(argument, max_news_per_symbol)

    if _looks_like_ticker(command):
        return _analyze_ticker(command, profile_map, max_news_per_symbol)
    return "ยังไม่รู้จักคำสั่งนี้ครับ\n\n" + _help_message()


def update_latest_reports(
    state: TelegramBotState,
    reports: list[StockReport],
    scanned_count: int,
    matched_count: int,
) -> None:
    state.last_reports = tuple(reports)
    state.last_scanned_count = scanned_count
    state.last_matched_count = matched_count
    state.last_run_at = time.time()


def _poll_commands(
    profile_map: dict[str, StockProfile],
    bot_token: str,
    chat_id: str,
    max_news_per_symbol: int,
    top_alerts_per_run: int | None,
    state: TelegramBotState,
) -> None:
    offset: int | None = None
    LOGGER.info("Telegram command bot started")
    while True:
        try:
            updates = fetch_telegram_updates(bot_token, offset=offset)
            for update in updates:
                update_id = update.get("update_id")
                if isinstance(update_id, int):
                    offset = update_id + 1
                text = _read_message_text(update, chat_id)
                if text is None:
                    continue
                response = handle_telegram_command(
                    text=text,
                    profile_map=profile_map,
                    max_news_per_symbol=max_news_per_symbol,
                    top_alerts_per_run=top_alerts_per_run,
                    state=state,
                )
                send_telegram_messages(bot_token, chat_id, response)
        except TelegramError as exc:
            LOGGER.warning("Telegram command bot error: %s", exc)
            time.sleep(5)
        except Exception:
            LOGGER.exception("Unexpected Telegram command bot error")
            time.sleep(5)


def _read_message_text(update: dict, chat_id: str) -> str | None:
    message = update.get("message")
    if not isinstance(message, dict):
        return None
    chat = message.get("chat")
    if not isinstance(chat, dict) or str(chat.get("id", "")) != str(chat_id):
        return None
    text = message.get("text")
    if not isinstance(text, str) or not text.strip():
        return None
    return text


def _build_profile_map(profiles: Iterable[StockProfile]) -> dict[str, StockProfile]:
    return {profile.ticker.upper(): profile for profile in profiles}


def _split_command(text: str) -> tuple[str, str]:
    command, _, argument = text.partition(" ")
    return command.split("@", 1)[0].strip().lower(), argument.strip()


def _help_message() -> str:
    return "\n".join(
        [
            "🤖 StockNews command/chat",
            "",
            "ใช้คำสั่ง:",
            "/status - เช็กว่า bot ทำงานอยู่ไหม",
            "/top - ดู Top 10 ล่าสุดที่ระบบคัดไว้",
            "/analyze NVDA - วิเคราะห์กราฟ+ข่าว+SOP ของหุ้น",
            "/why NVDA - เหมือน /analyze แต่ใช้ถามว่าทำไมน่าสนใจ",
            "/news MSFT - สรุปข่าวล่าสุด",
            "",
            "พิมพ์ ticker เปล่า ๆ เช่น NVDA ก็ได้ ระบบจะวิเคราะห์ให้",
        ]
    )


def _status_message(top_alerts_per_run: int | None, state: TelegramBotState) -> str:
    last_run = _format_age(state.last_run_at)
    limit = "ไม่จำกัด" if top_alerts_per_run is None else str(top_alerts_per_run)
    return "\n".join(
        [
            "🟢 StockNews bot กำลังทำงาน",
            f"🎯 Top alerts ต่อรอบ: {limit}",
            f"📊 รอบล่าสุด: {last_run}",
            f"🔎 รอบล่าสุดสแกน: {state.last_scanned_count} | เข้าเกณฑ์: {state.last_matched_count}",
        ]
    )


def _top_message(state: TelegramBotState) -> str:
    if not state.last_reports:
        return "ยังไม่มี Top ล่าสุดใน memory ครับ รอให้รอบ scan ปัจจุบันจบก่อน หรือใช้ /analyze TICKER เพื่อวิเคราะห์รายตัว"

    lines = ["🏆 Top ล่าสุดจากรอบ scan", ""]
    for index, report in enumerate(state.last_reports[:10], start=1):
        lines.append(
            f"#{index} {report.profile.ticker} | opportunity {calculate_opportunity_score(report)} | "
            f"{report.signal.trend} | {report.signal.close_price:,.2f} ({report.signal.change_percent:+.2f}%)"
        )
    return "\n".join(lines)


def _analyze_ticker(
    ticker: str,
    profile_map: dict[str, StockProfile],
    max_news_per_symbol: int,
) -> str:
    normalized_ticker = _normalize_ticker_argument(ticker)
    if not normalized_ticker:
        return "กรุณาใส่ ticker เช่น /analyze NVDA"

    profile = profile_map.get(
        normalized_ticker,
        StockProfile(ticker=normalized_ticker, name=normalized_ticker, business="Not configured"),
    )
    try:
        report = _build_stock_report(profile, max_news_per_symbol=max_news_per_symbol)
    except Exception as exc:
        return f"วิเคราะห์ {normalized_ticker} ไม่สำเร็จครับ: {exc}"
    return build_report_message(report)


def _build_stock_report(profile: StockProfile, max_news_per_symbol: int) -> StockReport:
    history = fetch_price_history(profile.ticker)
    signal = analyze_technical_signal(profile.ticker, history)
    try:
        news = fetch_news(profile.ticker, max_news_per_symbol)
    except NewsFetchError:
        news = ()
    return StockReport(profile=profile, signal=signal, news=news)


def _news_message(ticker: str, max_news_per_symbol: int) -> str:
    normalized_ticker = _normalize_ticker_argument(ticker)
    if not normalized_ticker:
        return "กรุณาใส่ ticker เช่น /news MSFT"

    try:
        news_items = fetch_news(normalized_ticker, max_news_per_symbol)
    except NewsFetchError as exc:
        return f"ดึงข่าว {normalized_ticker} ไม่สำเร็จครับ: {exc}"
    if not news_items:
        return f"ยังไม่พบข่าวล่าสุดของ {normalized_ticker} จาก feed ที่ใช้"

    lines = [f"📰 ข่าวล่าสุด {normalized_ticker}"]
    for item in news_items:
        lines.extend(_format_news_item(item))
    return "\n".join(lines)


def _format_news_item(item: NewsItem) -> list[str]:
    summary = item.summary or "feed ไม่มีสรุปข่าว ให้ตรวจรายละเอียดจากลิงก์"
    return [
        "",
        f"• {item.title}",
        f"  Tone: {item.sentiment} ({item.sentiment_score:+d})",
        f"  สรุป: {summary}",
        f"  {item.link}",
    ]


def _normalize_ticker_argument(value: str) -> str:
    return value.strip().split(maxsplit=1)[0].upper()


def _looks_like_ticker(value: str) -> bool:
    if not value or value.startswith("/"):
        return False
    return 1 <= len(value) <= 12 and all(char.isalnum() or char in {".", "-", "/"} for char in value)


def _format_age(timestamp: float | None) -> str:
    if timestamp is None:
        return "ยังไม่มีรอบ scan จบใน memory"
    elapsed_seconds = max(0, int(time.time() - timestamp))
    minutes, seconds = divmod(elapsed_seconds, 60)
    if minutes < 60:
        return f"{minutes} นาที {seconds} วินาทีที่แล้ว"
    hours, remaining_minutes = divmod(minutes, 60)
    return f"{hours} ชั่วโมง {remaining_minutes} นาทีที่แล้ว"
