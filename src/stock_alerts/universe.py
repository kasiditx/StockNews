from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import requests

from stock_alerts.models import StockProfile


NASDAQ_SCREENER_URL = "https://api.nasdaq.com/api/screener/stocks"
NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
REQUEST_TIMEOUT_SECONDS = 30
SUPPORTED_MARKETS = frozenset({"US", "TH"})
NASDAQ_SCREENER_LIMIT = 10_000
NASDAQ_API_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 stock-telegram-alert/1.0",
}
SECTOR_ALIASES = {
    "TECHNOLOGY": frozenset({"Technology"}),
    "เทคโนโลยี": frozenset({"Technology"}),
    "INDUSTRIALS": frozenset({"Industrials"}),
    "INDUSTRY": frozenset({"Industrials"}),
    "สินค้าอุตสาหกรรม": frozenset({"Industrials"}),
    "SERVICES": frozenset({"Consumer Discretionary", "Miscellaneous", "Telecommunications"}),
    "SERVICE": frozenset({"Consumer Discretionary", "Miscellaneous", "Telecommunications"}),
    "บริการ": frozenset({"Consumer Discretionary", "Miscellaneous", "Telecommunications"}),
    "FINANCIALS": frozenset({"Finance"}),
    "FINANCE": frozenset({"Finance"}),
    "ธุรกิจการเงิน": frozenset({"Finance"}),
    "CONSUMER PRODUCTS": frozenset({"Consumer Discretionary", "Consumer Staples"}),
    "CONSUMER": frozenset({"Consumer Discretionary", "Consumer Staples"}),
    "สินค้าอุปโภคบริโภค": frozenset({"Consumer Discretionary", "Consumer Staples"}),
}
EXCLUDED_SYMBOL_SUFFIXES = ("R", "U", "W")
EXCLUDED_SYMBOL_MARKERS = ("$", "^", "/")
EXCLUDED_SECURITY_NAME_TERMS = (
    " warrant",
    " warr",
    " unit",
    " right",
    " preferred",
    " preference",
    " depositary share",
    " notes",
    " note ",
    " bond",
    " debenture",
)


class UniverseError(RuntimeError):
    """Raised when a stock universe cannot be loaded safely."""


def load_universe_profiles(
    markets: Iterable[str],
    thai_universe_path: Path,
    symbol_limit: int | None,
    sectors: frozenset[str] = frozenset(),
) -> tuple[StockProfile, ...]:
    normalized_markets = tuple(_normalize_market(market) for market in markets)
    unsupported_markets = sorted(set(normalized_markets).difference(SUPPORTED_MARKETS))
    if unsupported_markets:
        raise UniverseError(f"Unsupported stock universe market(s): {', '.join(unsupported_markets)}")

    profiles: list[StockProfile] = []
    for market in normalized_markets:
        if market == "US":
            profiles.extend(load_us_profiles(sectors=sectors))
        elif market == "TH":
            profiles.extend(load_thai_profiles(thai_universe_path, sectors=sectors))

    deduplicated_profiles = _deduplicate_profiles(profiles)
    if symbol_limit is None:
        return deduplicated_profiles
    return deduplicated_profiles[:symbol_limit]


def load_us_profiles(sectors: frozenset[str] = frozenset()) -> list[StockProfile]:
    try:
        screener_profiles = load_us_profiles_from_screener(sectors=sectors)
    except UniverseError:
        if sectors:
            raise
    else:
        if screener_profiles or sectors:
            return screener_profiles

    nasdaq_rows = _fetch_symbol_directory(NASDAQ_LISTED_URL)
    other_rows = _fetch_symbol_directory(OTHER_LISTED_URL)
    profiles: list[StockProfile] = []

    for row in nasdaq_rows:
        if row.get("Test Issue") != "N" or row.get("ETF") == "Y":
            continue
        symbol = row.get("Symbol", "").strip()
        security_name = row.get("Security Name", "").strip()
        if _is_supported_us_common_stock(symbol=symbol, security_name=security_name):
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
        if _is_supported_us_common_stock(symbol=symbol, security_name=security_name):
            profiles.append(
                StockProfile(
                    ticker=_to_yahoo_us_ticker(symbol),
                    name=security_name,
                    business="US listed equity",
                )
            )

    return profiles


def load_us_profiles_from_screener(sectors: frozenset[str] = frozenset()) -> list[StockProfile]:
    profiles: list[StockProfile] = []
    for row in _fetch_nasdaq_screener_rows():
        symbol = _read_string(row, "symbol")
        security_name = _read_string(row, "name")
        sector = _read_string(row, "sector")
        industry = _read_string(row, "industry")
        if sectors and sector not in sectors:
            continue
        if _is_supported_us_common_stock(symbol=symbol, security_name=security_name):
            profiles.append(
                StockProfile(
                    ticker=_to_yahoo_us_ticker(symbol),
                    name=security_name,
                    business=_format_business(sector=sector, industry=industry),
                    sector=sector or None,
                    industry=industry or None,
                )
            )
    return profiles


def load_thai_profiles(
    thai_universe_path: Path,
    sectors: frozenset[str] = frozenset(),
) -> list[StockProfile]:
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
            sector = row.get("sector", "").strip()
            industry = row.get("industry", "").strip()
            if sectors and sector and sector not in sectors:
                continue
            if ticker and name and business:
                profiles.append(
                    StockProfile(
                        ticker=ticker,
                        name=name,
                        business=business,
                        sector=sector or None,
                        industry=industry or None,
                    )
                )
    return profiles


def parse_markets(raw_value: str) -> tuple[str, ...]:
    markets = tuple(market.strip().upper() for market in raw_value.split(",") if market.strip())
    return markets or ("US", "TH")


def parse_sectors(raw_value: str) -> frozenset[str]:
    sectors: set[str] = set()
    for raw_sector in raw_value.split(","):
        sector = raw_sector.strip()
        if not sector:
            continue
        sectors.update(SECTOR_ALIASES.get(sector.upper(), frozenset({sector})))
    return frozenset(sectors)


def _fetch_nasdaq_screener_rows() -> list[dict[str, Any]]:
    response = requests.get(
        NASDAQ_SCREENER_URL,
        params={
            "tableonly": "true",
            "limit": str(NASDAQ_SCREENER_LIMIT),
            "offset": "0",
            "download": "true",
        },
        headers=NASDAQ_API_HEADERS,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if response.status_code >= 400:
        raise UniverseError(f"Failed to fetch Nasdaq screener with HTTP {response.status_code}")

    payload = response.json()
    rows = payload.get("data", {}).get("rows", [])
    if not isinstance(rows, list):
        raise UniverseError("Nasdaq screener response did not include a rows list")
    return [row for row in rows if isinstance(row, dict)]


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


def _read_string(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if value is None:
        return ""
    return str(value).strip()


def _format_business(sector: str, industry: str) -> str:
    if sector and industry:
        return f"{sector} / {industry}"
    return sector or industry or "US listed equity"


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


def _is_supported_us_common_stock(symbol: str, security_name: str) -> bool:
    if not symbol or not security_name:
        return False

    normalized_symbol = symbol.strip().upper()
    normalized_name = f" {security_name.strip().lower()} "
    if any(marker in normalized_symbol for marker in EXCLUDED_SYMBOL_MARKERS):
        return False
    if normalized_symbol.endswith(EXCLUDED_SYMBOL_SUFFIXES):
        return False
    return not any(term in normalized_name for term in EXCLUDED_SECURITY_NAME_TERMS)


def _deduplicate_profiles(profiles: Iterable[StockProfile]) -> tuple[StockProfile, ...]:
    seen: set[str] = set()
    deduplicated: list[StockProfile] = []
    for profile in profiles:
        if profile.ticker in seen:
            continue
        seen.add(profile.ticker)
        deduplicated.append(profile)
    return tuple(deduplicated)
