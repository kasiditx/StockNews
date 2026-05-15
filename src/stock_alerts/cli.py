from __future__ import annotations

import argparse
import logging
from pathlib import Path

from stock_alerts.app import run_once, watch
from stock_alerts.config import (
    DEFAULT_ALERT_INTERVAL_MINUTES,
    DEFAULT_MAX_NEWS_LOOKUPS_PER_RUN,
    DEFAULT_MAX_NEWS_PER_SYMBOL,
    DEFAULT_MIN_SCORE_TO_ALERT,
    DEFAULT_TOP_ALERTS_PER_RUN,
    DEFAULT_WATCHLIST_PATH,
    ConfigError,
    get_int_env,
    get_optional_int_env,
    get_required_env,
    load_environment,
    load_watchlist,
)


def main() -> None:
    load_environment()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = _build_parser()
    args = parser.parse_args()

    try:
        profiles = load_watchlist(args.watchlist)
        bot_token = get_required_env("TELEGRAM_BOT_TOKEN")
        chat_id = get_required_env("TELEGRAM_CHAT_ID")
        max_news_per_symbol = get_int_env("MAX_NEWS_PER_SYMBOL", DEFAULT_MAX_NEWS_PER_SYMBOL)
        max_news_lookups_per_run = get_optional_int_env(
            "MAX_NEWS_LOOKUPS_PER_RUN",
            DEFAULT_MAX_NEWS_LOOKUPS_PER_RUN,
        )
        min_score_to_alert = get_int_env("MIN_SCORE_TO_ALERT", DEFAULT_MIN_SCORE_TO_ALERT)
        top_alerts_per_run = get_optional_int_env("TOP_ALERTS_PER_RUN", DEFAULT_TOP_ALERTS_PER_RUN)

        if args.command == "run-once":
            sent_count = run_once(
                profiles=profiles,
                bot_token=bot_token,
                chat_id=chat_id,
                max_news_per_symbol=max_news_per_symbol,
                max_news_lookups_per_run=max_news_lookups_per_run,
                min_score_to_alert=min_score_to_alert,
                top_alerts_per_run=top_alerts_per_run,
            )
            logging.info("Sent %s Telegram alert(s)", sent_count)
            return

        interval_minutes = get_int_env("ALERT_INTERVAL_MINUTES", DEFAULT_ALERT_INTERVAL_MINUTES)
        watch(
            profiles=profiles,
            bot_token=bot_token,
            chat_id=chat_id,
            max_news_per_symbol=max_news_per_symbol,
            max_news_lookups_per_run=max_news_lookups_per_run,
            min_score_to_alert=min_score_to_alert,
            top_alerts_per_run=top_alerts_per_run,
            interval_minutes=interval_minutes,
        )
    except ConfigError as exc:
        parser.error(str(exc))
    except KeyboardInterrupt as exc:
        logging.info("Stopped by user")
        raise SystemExit(130) from exc


def _build_parser() -> argparse.ArgumentParser:
    command_options = argparse.ArgumentParser(add_help=False)
    _add_watchlist_argument(command_options, default=argparse.SUPPRESS)

    parser = argparse.ArgumentParser(description="Send Telegram stock alerts.")
    _add_watchlist_argument(parser, default=None)

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "run-once",
        parents=[command_options],
        help="Analyze configured stocks once and send matching alerts.",
    )
    subparsers.add_parser(
        "watch",
        parents=[command_options],
        help="Keep analyzing and sending alerts on an interval.",
    )
    return parser


def _add_watchlist_argument(
    parser: argparse.ArgumentParser,
    default: Path | str | None,
) -> None:
    parser.add_argument(
        "--watchlist",
        type=Path,
        default=default,
        help=(
            "Path to watchlist JSON. Defaults to "
            f"{DEFAULT_WATCHLIST_PATH} when STOCK_WATCHLIST is not configured."
        ),
    )
