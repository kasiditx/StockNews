from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass
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
DEFAULT_STOCK_GROUPS = "FINCIAL,INDUS,SERVICE,TECH"
GROUP_ALIASES = {
    "FINANCIAL": "FINCIAL",
    "FINANCIALS": "FINCIAL",
    "FINANCE": "FINCIAL",
    "ธุรกิจการเงิน": "FINCIAL",
    "สินค้าอุตสาหกรรม": "INDUS",
    "INDUSTRIAL": "INDUS",
    "INDUSTRIALS": "INDUS",
    "บริการ": "SERVICE",
    "SERVICES": "SERVICE",
    "เทคโนโลยี": "TECH",
    "TECHNOLOGY": "TECH",
}
REQUESTED_GROUPS = frozenset({"FINCIAL", "INDUS", "SERVICE", "TECH"})
GROUP_DEFINITIONS = {
    "FINCIAL": {
        "sectors": frozenset({"Finance"}),
        "subsectors": frozenset({"BANK", "FIN", "INSUR"}),
        "tickers": frozenset({"BAC", "BLK", "BRK-A", "BRK-B", "JPM", "MA", "PNC", "V", "XYZ"}),
        "industry_keywords": frozenset(
            {
                "asset management",
                "bank",
                "broker",
                "credit services",
                "finance",
                "financial services",
                "insurance",
                "payment",
                "transaction",
            }
        ),
    },
    "INDUS": {
        "sectors": frozenset({"Basic Materials", "Industrials"}),
        "subsectors": frozenset({"AUTO", "IMM", "PETRO", "STEEL"}),
        "tickers": frozenset({"BA", "CAT", "DE", "FDX", "LMT", "SIEGY", "UPS"}),
        "industry_keywords": frozenset(
            {
                "aerospace",
                "agricultural machinery",
                "air freight",
                "aluminum",
                "auto manufacturing",
                "chemicals",
                "construction machinery",
                "defense",
                "farm machinery",
                "industrial machinery",
                "logistics",
                "metal",
                "petrochemical",
                "steel",
                "transportation",
                "trucking",
            }
        ),
    },
    "SERVICE": {
        "sectors": frozenset(
            {"Consumer Discretionary", "Health Care", "Miscellaneous", "Telecommunications"}
        ),
        "subsectors": frozenset({"COMM", "HELTH", "MEDIA", "PROF", "TRANS"}),
        "tickers": frozenset({"ABNB", "AMZN", "GOOGL", "MA", "META", "MSFT", "V"}),
        "industry_keywords": frozenset(
            {
                "advertising",
                "air freight",
                "broadcasting",
                "business services",
                "e-commerce",
                "health care",
                "hotels",
                "internet",
                "logistics",
                "media",
                "medical",
                "professional services",
                "retail",
                "social media",
                "telecommunications",
                "transportation",
                "travel",
            }
        ),
    },
    "TECH": {
        "sectors": frozenset({"Technology", "Telecommunications"}),
        "subsectors": frozenset({"ICT"}),
        "tickers": frozenset({"ADVANC.BK", "MSFT", "NVDA"}),
        "industry_keywords": frozenset(
            {
                "artificial intelligence",
                "cloud",
                "communication equipment",
                "computer",
                "cybersecurity",
                "electronic components",
                "semiconductor",
                "software",
                "telecommunications",
            }
        ),
    },
}
EXTRA_GROUP_PROFILES = {
    "SIEGY": StockProfile(
        ticker="SIEGY",
        name="Siemens AG",
        business="Industrials / Engineering and industrial technology",
        sector="Industrials",
        industry="Engineering and Industrial Technology",
    ),
}
PROFILE_OVERRIDES = {
    "BRK-A": StockProfile(
        ticker="BRK-A",
        name="Berkshire Hathaway Inc. Class A",
        business="Finance / Holding company, insurance, and long-term investments",
        sector="Finance",
        industry="Insurance and Investment Holding Company",
    ),
    "BRK-B": StockProfile(
        ticker="BRK-B",
        name="Berkshire Hathaway Inc. Class B",
        business="Finance / Holding company, insurance, and long-term investments",
        sector="Finance",
        industry="Insurance and Investment Holding Company",
    ),
    "MA": StockProfile(
        ticker="MA",
        name="Mastercard Incorporated",
        business="Finance / Global payment network",
        sector="Finance",
        industry="Payment Network",
    ),
    "V": StockProfile(
        ticker="V",
        name="Visa Inc.",
        business="Finance / Global payment network",
        sector="Finance",
        industry="Payment Network",
    ),
    "XYZ": StockProfile(
        ticker="XYZ",
        name="Block, Inc.",
        business="Fintech / Digital payments, Cash App, and merchant services",
        sector="Technology",
        industry="Financial Technology",
    ),
}
EXCLUDED_SYMBOL_SUFFIXES = ("R", "U", "W")
EXCLUDED_SYMBOL_MARKERS = ("$", "^", "/")
EXCLUDED_SECURITY_NAME_TERMS = (
    " warrant",
    " warr",
    " unit ",
    " units ",
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


@dataclass(frozen=True)
class StockGroupFilter:
    groups: frozenset[str] = frozenset()
    sectors: frozenset[str] = frozenset()

    @property
    def is_enabled(self) -> bool:
        return bool(self.groups or self.sectors)


def load_universe_profiles(
    markets: Iterable[str],
    thai_universe_path: Path,
    symbol_limit: int | None,
    sectors: frozenset[str] = frozenset(),
    group_filter: StockGroupFilter = StockGroupFilter(),
) -> tuple[StockProfile, ...]:
    normalized_markets = tuple(_normalize_market(market) for market in markets)
    unsupported_markets = sorted(set(normalized_markets).difference(SUPPORTED_MARKETS))
    if unsupported_markets:
        raise UniverseError(f"Unsupported stock universe market(s): {', '.join(unsupported_markets)}")

    profiles: list[StockProfile] = []
    for market in normalized_markets:
        if market == "US":
            profiles.extend(load_us_profiles(sectors=sectors, group_filter=group_filter))
        elif market == "TH":
            profiles.extend(
                load_thai_profiles(
                    thai_universe_path,
                    sectors=sectors,
                    group_filter=group_filter,
                )
            )

    deduplicated_profiles = _deduplicate_profiles(profiles)
    if symbol_limit is None:
        return deduplicated_profiles
    return deduplicated_profiles[:symbol_limit]


def load_us_profiles(
    sectors: frozenset[str] = frozenset(),
    group_filter: StockGroupFilter = StockGroupFilter(),
) -> list[StockProfile]:
    try:
        screener_profiles = load_us_profiles_from_screener(
            sectors=sectors,
            group_filter=group_filter,
        )
    except UniverseError:
        if sectors or group_filter.is_enabled:
            raise
    else:
        if screener_profiles or sectors or group_filter.is_enabled:
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


def load_us_profiles_from_screener(
    sectors: frozenset[str] = frozenset(),
    group_filter: StockGroupFilter = StockGroupFilter(),
) -> list[StockProfile]:
    profiles: list[StockProfile] = []
    for row in _fetch_nasdaq_screener_rows():
        symbol = _read_string(row, "symbol")
        ticker = _to_yahoo_us_ticker(symbol)
        security_name = _read_string(row, "name")
        sector = _read_string(row, "sector")
        industry = _read_string(row, "industry")
        if sectors and sector not in sectors:
            continue
        if group_filter.is_enabled and not _matches_group_filter(
            ticker=ticker,
            sector=sector,
            industry=industry,
            group_filter=group_filter,
        ):
            continue
        if _is_supported_us_common_stock(symbol=ticker, security_name=security_name):
            profiles.append(
                _override_profile(
                    StockProfile(
                        ticker=ticker,
                        name=security_name,
                        business=_format_business(sector=sector, industry=industry),
                        sector=sector or None,
                        industry=industry or None,
                    )
                )
            )
    profiles.extend(_extra_group_profiles(group_filter))
    return profiles


def load_thai_profiles(
    thai_universe_path: Path,
    sectors: frozenset[str] = frozenset(),
    group_filter: StockGroupFilter = StockGroupFilter(),
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
            if group_filter.is_enabled and not _matches_group_filter(
                ticker=ticker,
                sector=sector,
                industry=industry,
                group_filter=group_filter,
            ):
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


def parse_groups(raw_value: str) -> frozenset[str]:
    groups: set[str] = set()
    for raw_group in raw_value.split(","):
        group = raw_group.strip()
        if not group:
            continue
        normalized_group = GROUP_ALIASES.get(group.upper(), group.upper())
        if normalized_group not in REQUESTED_GROUPS:
            raise UniverseError(
                f"Unsupported stock group: {group}. "
                f"Supported groups: {', '.join(sorted(REQUESTED_GROUPS))}"
            )
        groups.add(normalized_group)
    return frozenset(groups)


def build_group_filter(raw_groups: str, raw_sectors: str) -> StockGroupFilter:
    return StockGroupFilter(groups=parse_groups(raw_groups), sectors=parse_sectors(raw_sectors))


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


def _matches_group_filter(
    ticker: str,
    sector: str,
    industry: str,
    group_filter: StockGroupFilter,
) -> bool:
    if group_filter.sectors and sector in group_filter.sectors:
        return True

    normalized_ticker = ticker.strip().upper()
    normalized_sector = sector.strip()
    normalized_industry = industry.strip().lower()
    normalized_subsector = industry.strip().upper()

    for group in group_filter.groups:
        definition = GROUP_DEFINITIONS[group]
        if normalized_ticker in definition["tickers"]:
            return True
        if normalized_sector in definition["sectors"]:
            return True
        if normalized_subsector in definition["subsectors"]:
            return True
        if any(keyword in normalized_industry for keyword in definition["industry_keywords"]):
            return True
    return False


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
    return symbol.strip().upper().replace(".", "-").replace("/", "-")


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


def _extra_group_profiles(group_filter: StockGroupFilter) -> list[StockProfile]:
    if not group_filter.groups:
        return []

    requested_tickers: set[str] = set()
    for group in group_filter.groups:
        requested_tickers.update(GROUP_DEFINITIONS[group]["tickers"])

    return [
        _override_profile(profile)
        for ticker, profile in EXTRA_GROUP_PROFILES.items()
        if ticker in requested_tickers
    ]


def _override_profile(profile: StockProfile) -> StockProfile:
    return PROFILE_OVERRIDES.get(profile.ticker, profile)
