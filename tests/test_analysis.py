from __future__ import annotations

import pandas as pd

from stock_alerts.analysis import analyze_technical_signal


def test_analyze_technical_signal_detects_positive_trend() -> None:
    close_prices = [100 + index for index in range(80)]
    history = pd.DataFrame(
        {
            "High": [101 + index for index in range(80)],
            "Low": [99 + index for index in range(80)],
            "Close": close_prices,
            "Volume": [1_000] * 79 + [2_000],
        }
    )

    signal = analyze_technical_signal("TEST", history)

    assert signal.ticker == "TEST"
    assert signal.score >= 2
    assert "SMA20" in " ".join(signal.reasons)
    assert signal.trend in {"ขาขึ้นแข็งแรง", "ขาขึ้นระยะสั้น"}
    assert signal.adx is not None


def test_analyze_technical_signal_requires_enough_history() -> None:
    history = pd.DataFrame(
        {
            "High": [1, 2, 3],
            "Low": [1, 2, 3],
            "Close": [1, 2, 3],
            "Volume": [100, 100, 100],
        }
    )

    try:
        analyze_technical_signal("TEST", history)
    except ValueError as exc:
        assert "Need at least" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
