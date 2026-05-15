from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

import requests

from stock_alerts.models import StockProfile


NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
REQUEST_TIMEOUT_SECONDS = 30
SUPPORTED_MARKETS = frozenset({"US", "TH"})


class UniverseError(RuntimeError):
    """Raised when a stock universe cannot be loaded safely."""


def load_universe_profiles(
    markets: Iterable[str],
    thai_universe_path: Path,
    symbol_limit: int | None,
) -> tuple[StockProfile, ...]:
    normalized_markets = tuple(_normalize_market(market) for market in markets)
    unsupported_markets = sorted(set(normalized_markets).difference(SUPPORTED_MARKETS))
    if unsupported_markets:
        raise UniverseError(f"Unsupported stock universe market(s): {', '.join(unsupported_markets)}")

    profiles: list[StockProfile] = []
    for market in normalized_markets:
        if market == "US":
            profiles.extend(load_us_profiles())
        elif market == "TH":
            profiles.extend(load_thai_profiles(thai_universe_path))

    deduplicated_profiles = _deduplicate_profiles(profiles)
    if symbol_limit is None:
        return deduplicated_profiles
    return deduplicated_profiles[:symbol_limit]


def load_us_profiles() -> list[StockProfile]:
    nasdaq_rows = _fetch_symbol_directory(NASDAQ_LISTED_URL)
    other_rows = _fetch_symbol_directory(OTHER_LISTED_URL)
    profiles: list[StockProfile] = []

    for row in nasdaq_rows:
        if row.get("Test Issue") != "N" or row.get("ETF") == "Y":
            continue
        symbol = row.get("Symbol", "").strip()
        security_name = row.get("Security Name", "").strip()
        if symbol and security_name:
            profiles.append(
                StockProfile(
                    ticker=_to_yahoo_us_ticker(symbol),
                    name=security_name,
                    business="US listed equity",
                )
            )

    for row in other_rows:
        if row.get("Test Issue") != "N" or row.get("ETF") == "Y":
            continue
        symbol = row.get("ACT Symbol", "").strip()
        security_name = row.get("Security Name", "").strip()
        if symbol and security_name:
            profiles.append(
                StockProfile(
                    ticker=_to_yahoo_us_ticker(symbol),
                    name=security_name,
                    business="US listed equity",
                )
            )

    return profiles


def load_thai_profiles(thai_universe_path: Path) -> list[StockProfile]:
    if not thai_universe_path.exists():
        raise UniverseError(
            f"Thai stock universe file not found: {thai_universe_path}. "
            "Create it with columns ticker,name,business before using STOCK_UNIVERSE=TH."
        )

    with thai_universe_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required_fields = {"ticker", "name", "business"}
        fieldnames = set(reader.fieldnames or ())
        missing_fields = required_fields.difference(fieldnames)
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise UniverseError(f"Thai universe file is missing column(s): {missing}")

        profiles: list[StockProfile] = []
        for row in reader:
            ticker = _normalize_thai_ticker(row.get("ticker", ""))
            name = row.get("name", "").strip()
            business = row.get("business", "").strip()
            if ticker and name and business:
                profiles.append(StockProfile(ticker=ticker, name=name, business=business))
    return profiles


def parse_markets(raw_value: str) -> tuple[str, ...]:
    markets = tuple(market.strip().upper() for market in raw_value.split(",") if market.strip())
    return markets or ("US", "TH")


def _fetch_symbol_directory(url: str) -> list[dict[str, str]]:
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    if response.status_code >= 400:
        raise UniverseError(f"Failed to fetch symbol directory with HTTP {response.status_code}")

    lines = [
        line
        for line in response.text.splitlines()
        if line and not line.startswith("File Creation Time:")
    ]
    reader = csv.DictReader(lines, delimiter="|")
    return list(reader)


def _normalize_market(market: str) -> str:
    normalized_market = market.strip().upper()
    if normalized_market == "USA":
        return "US"
    return normalized_market


def _normalize_thai_ticker(ticker: str) -> str:
    normalized_ticker = ticker.strip().upper()
    if not normalized_ticker:
        return ""
    if normalized_ticker.endswith(".BK"):
        return normalized_ticker
    return f"{normalized_ticker}.BK"


def _to_yahoo_us_ticker(symbol: str) -> str:
    return symbol.strip().upper().replace(".", "-")


def _deduplicate_profiles(profiles: Iterable[StockProfile]) -> tuple[StockProfile, ...]:
    seen: set[str] = set()
    deduplicated: list[StockProfile] = []
    for profile in profiles:
        if profile.ticker in seen:
            continue
        seen.add(profile.ticker)
        deduplicated.append(profile)
    return tuple(deduplicated)
