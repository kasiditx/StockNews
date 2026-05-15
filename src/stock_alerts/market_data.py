from __future__ import annotations

import pandas as pd
import yfinance as yf


class MarketDataError(RuntimeError):
    """Raised when market data cannot be fetched or is not usable."""


def fetch_price_history(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    history = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
    if history.empty:
        raise MarketDataError(f"No price history returned for {ticker}")

    required_columns = {"High", "Low", "Close", "Volume"}
    missing_columns = required_columns.difference(history.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise MarketDataError(f"Price history for {ticker} is missing column(s): {missing}")

    return history
