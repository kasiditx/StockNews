from __future__ import annotations

import logging

from stock_alerts import market_data


def test_yfinance_logger_is_quiet() -> None:
    assert market_data is not None
    assert logging.getLogger("yfinance").level == logging.CRITICAL
