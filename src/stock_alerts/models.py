from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StockProfile:
    ticker: str
    name: str
    business: str
    sector: str | None = None
    industry: str | None = None


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
    rsi_fast: float | None = None
    rsi_slow: float | None = None
    plus_di: float | None = None
    minus_di: float | None = None
    atr_stop_loss: float | None = None
    atr_take_profit_2x: float | None = None
    atr_take_profit_3x: float | None = None
    technical_plan: tuple[str, ...] = ()


@dataclass(frozen=True)
class StockReport:
    profile: StockProfile
    signal: TechnicalSignal
    news: tuple[NewsItem, ...]
