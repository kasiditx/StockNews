from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from stock_alerts.models import StockProfile
from stock_alerts.universe import UniverseError, load_universe_profiles, parse_markets


DEFAULT_ALERT_INTERVAL_MINUTES = 60
DEFAULT_MAX_NEWS_PER_SYMBOL = 3
DEFAULT_MAX_NEWS_LOOKUPS_PER_RUN = 50
DEFAULT_MIN_SCORE_TO_ALERT = 2
DEFAULT_TOP_ALERTS_PER_RUN = None
DEFAULT_MAX_SYMBOLS_PER_RUN = 300
DEFAULT_STOCK_UNIVERSE = "US,TH"
DEFAULT_THAI_UNIVERSE_PATH = Path("config/universe.th.csv")
DEFAULT_WATCHLIST_PATH = Path("config/watchlist.json")
ALL_STOCKS_SENTINELS = frozenset({"ALL", "*"})


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
    if watchlist_path is not None:
        if not watchlist_path.exists():
            raise ConfigError(f"Watchlist file not found: {watchlist_path}")
        return _load_watchlist_file(watchlist_path)

    stock_watchlist = os.getenv("STOCK_WATCHLIST", "").strip()
    if stock_watchlist.upper() in ALL_STOCKS_SENTINELS:
        return _load_all_stock_universe()

    tickers = [
        ticker.strip().upper()
        for ticker in stock_watchlist.split(",")
        if ticker.strip()
    ]
    if tickers:
        return tuple(
            StockProfile(ticker=ticker, name=ticker, business="Not configured") for ticker in tickers
        )

    if DEFAULT_WATCHLIST_PATH.exists():
        return _load_watchlist_file(DEFAULT_WATCHLIST_PATH)

    raise ConfigError(
        "No stock watchlist configured. Set STOCK_WATCHLIST or create config/watchlist.json"
    )


def _load_all_stock_universe() -> tuple[StockProfile, ...]:
    raw_markets = os.getenv("STOCK_UNIVERSE", DEFAULT_STOCK_UNIVERSE)
    thai_universe_path = Path(os.getenv("STOCK_UNIVERSE_TH_FILE", str(DEFAULT_THAI_UNIVERSE_PATH)))
    symbol_limit = get_optional_int_env("MAX_SYMBOLS_PER_RUN", DEFAULT_MAX_SYMBOLS_PER_RUN)

    try:
        profiles = load_universe_profiles(
            markets=parse_markets(raw_markets),
            thai_universe_path=thai_universe_path,
            symbol_limit=symbol_limit,
        )
    except UniverseError as exc:
        raise ConfigError(str(exc)) from exc

    if not profiles:
        raise ConfigError("Stock universe is empty")
    return profiles


def get_optional_int_env(name: str, default: int | None) -> int | None:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc

    if value < 0:
        raise ConfigError(f"{name} must be zero or greater")
    if value == 0:
        return None
    return value


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
