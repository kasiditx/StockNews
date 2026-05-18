from __future__ import annotations

import logging

import pytest

from stock_alerts import market_data


def test_yfinance_logger_is_quiet() -> None:
    assert market_data is not None
    assert logging.getLogger("yfinance").level == logging.CRITICAL


def test_fetch_price_history_wraps_provider_errors(monkeypatch) -> None:
    class FakeTicker:
        def __init__(self, ticker: str) -> None:
            self.ticker = ticker

        def history(self, **kwargs):
            raise AttributeError("'Response' object has no attribute 'get'")

    monkeypatch.setattr(market_data.yf, "Ticker", FakeTicker)

    with pytest.raises(market_data.MarketDataError, match="Price history request failed for BROKEN"):
        market_data.fetch_price_history("BROKEN")
