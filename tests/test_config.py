from __future__ import annotations

import json

import pytest

from stock_alerts.config import ConfigError, load_watchlist


def test_load_watchlist_rejects_duplicate_tickers(tmp_path) -> None:
    watchlist = tmp_path / "watchlist.json"
    watchlist.write_text(
        json.dumps(
            {
                "symbols": [
                    {"ticker": "AAPL", "name": "Apple", "business": "Technology"},
                    {"ticker": "AAPL", "name": "Apple", "business": "Technology"},
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="Duplicate ticker"):
        load_watchlist(watchlist)


def test_load_watchlist_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("STOCK_WATCHLIST", "aapl, nvda")

    profiles = load_watchlist(None)

    assert [profile.ticker for profile in profiles] == ["AAPL", "NVDA"]
