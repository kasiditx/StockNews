from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StockProfile:
    ticker: str
    name: str
    business: str


@dataclass(frozen=True)
class NewsItem:
    title: str
    link: str
    published: str | None = None


@dataclass(frozen=True)
class TechnicalSignal:
    ticker: str
    score: int
    stance: str
    close_price: float
    change_percent: float
    rsi: float | None
    sma_20: float | None
    sma_50: float | None
    macd: float | None
    macd_signal: float | None
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class StockReport:
    profile: StockProfile
    signal: TechnicalSignal
    news: tuple[NewsItem, ...]
