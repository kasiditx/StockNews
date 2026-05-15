from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from stock_alerts.models import StockProfile


DEFAULT_ALERT_INTERVAL_MINUTES = 60
DEFAULT_MAX_NEWS_PER_SYMBOL = 3
DEFAULT_MIN_SCORE_TO_ALERT = 2


class ConfigError(ValueError):
    """Raised when required runtime configuration is missing or invalid."""


def load_environment() -> None:
    load_dotenv()


def get_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    return value


def get_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc

    if value <= 0:
        raise ConfigError(f"{name} must be greater than zero")
    return value


def load_watchlist(watchlist_path: Path | None) -> tuple[StockProfile, ...]:
    if watchlist_path is not None and watchlist_path.exists():
        return _load_watchlist_file(watchlist_path)

    tickers = [
        ticker.strip().upper()
        for ticker in os.getenv("STOCK_WATCHLIST", "").split(",")
        if ticker.strip()
    ]
    if not tickers:
        raise ConfigError(
            "No stock watchlist configured. Set STOCK_WATCHLIST or create config/watchlist.json"
        )

    return tuple(StockProfile(ticker=ticker, name=ticker, business="Not configured") for ticker in tickers)


def _load_watchlist_file(watchlist_path: Path) -> tuple[StockProfile, ...]:
    with watchlist_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    symbols = payload.get("symbols")
    if not isinstance(symbols, list) or not symbols:
        raise ConfigError("watchlist file must contain a non-empty symbols list")

    profiles = tuple(_parse_profile(item) for item in symbols)
    duplicate_tickers = _find_duplicates(profile.ticker for profile in profiles)
    if duplicate_tickers:
        raise ConfigError(f"Duplicate ticker(s) in watchlist: {', '.join(duplicate_tickers)}")

    return profiles


def _parse_profile(item: Any) -> StockProfile:
    if not isinstance(item, dict):
        raise ConfigError("Each watchlist symbol must be an object")

    ticker = _read_required_string(item, "ticker").upper()
    name = item.get("name", ticker)
    business = item.get("business", "Not configured")

    if not isinstance(name, str) or not name.strip():
        raise ConfigError(f"name for {ticker} must be a non-empty string")
    if not isinstance(business, str) or not business.strip():
        raise ConfigError(f"business for {ticker} must be a non-empty string")

    return StockProfile(ticker=ticker, name=name.strip(), business=business.strip())


def _read_required_string(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"watchlist symbol must include non-empty {key}")
    return value.strip()


def _find_duplicates(values: Any) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return tuple(sorted(duplicates))
