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
    summary: str | None = None
    sentiment: str = "neutral"
    sentiment_score: int = 0
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
    adx: float | None
    atr_percent: float | None
    bollinger_position: float | None
    distance_from_high_percent: float | None
    trend: str
    reasons: tuple[str, ...]
    risk_flags: tuple[str, ...]


@dataclass(frozen=True)
class StockReport:
    profile: StockProfile
    signal: TechnicalSignal
    news: tuple[NewsItem, ...]
