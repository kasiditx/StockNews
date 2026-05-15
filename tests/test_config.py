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


def test_explicit_watchlist_file_takes_priority_over_all_environment(monkeypatch, tmp_path) -> None:
    watchlist = tmp_path / "watchlist.json"
    watchlist.write_text(
        json.dumps(
            {
                "symbols": [
                    {"ticker": "AAPL", "name": "Apple", "business": "Technology"},
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("STOCK_WATCHLIST", "ALL")
    monkeypatch.setenv("STOCK_UNIVERSE", "TH")
    monkeypatch.setenv("STOCK_UNIVERSE_TH_FILE", str(tmp_path / "missing.csv"))

    profiles = load_watchlist(watchlist)

    assert [profile.ticker for profile in profiles] == ["AAPL"]


def test_explicit_watchlist_file_must_exist(tmp_path) -> None:
    missing_watchlist = tmp_path / "missing.json"

    with pytest.raises(ConfigError, match="Watchlist file not found"):
        load_watchlist(missing_watchlist)


def test_all_watchlist_loads_thai_universe_file(monkeypatch, tmp_path) -> None:
    thai_universe = tmp_path / "universe.th.csv"
    thai_universe.write_text(
        "ticker,name,business\nPTT,PTT,Energy\nAOT.BK,Airports of Thailand,Airport operator\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("STOCK_WATCHLIST", "ALL")
    monkeypatch.setenv("STOCK_UNIVERSE", "TH")
    monkeypatch.setenv("STOCK_UNIVERSE_TH_FILE", str(thai_universe))
    monkeypatch.setenv("MAX_SYMBOLS_PER_RUN", "1")

    profiles = load_watchlist(None)

    assert [profile.ticker for profile in profiles] == ["PTT.BK"]


def test_all_watchlist_requires_thai_universe_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STOCK_WATCHLIST", "ALL")
    monkeypatch.setenv("STOCK_UNIVERSE", "TH")
    monkeypatch.setenv("STOCK_UNIVERSE_TH_FILE", str(tmp_path / "missing.csv"))

    with pytest.raises(ConfigError, match="Thai stock universe file not found"):
        load_watchlist(None)
