from __future__ import annotations

from stock_alerts.universe import (
    UniverseError,
    _is_supported_us_common_stock,
    load_us_profiles,
    load_us_profiles_from_screener,
    parse_sectors,
)


def test_us_common_stock_filter_allows_plain_common_stock() -> None:
    assert _is_supported_us_common_stock("AAPL", "Apple Inc. Common Stock")


def test_us_common_stock_filter_rejects_warrants_units_and_preferred() -> None:
    assert not _is_supported_us_common_stock("AACIW", "Armada Acquisition Corp. I Warrant")
    assert not _is_supported_us_common_stock("AACIU", "Armada Acquisition Corp. I Unit")
    assert not _is_supported_us_common_stock("WRB$E", "W. R. Berkley Corporation Preferred Stock")


def test_parse_sectors_maps_requested_groups_to_provider_sectors() -> None:
    sectors = parse_sectors("Technology, Industrials, Services, Financials, Consumer Products")

    assert sectors == frozenset(
        {
            "Technology",
            "Industrials",
            "Consumer Discretionary",
            "Miscellaneous",
            "Telecommunications",
            "Finance",
            "Consumer Staples",
        }
    )


def test_load_us_profiles_from_screener_filters_by_sector(monkeypatch) -> None:
    monkeypatch.setattr(
        "stock_alerts.universe._fetch_nasdaq_screener_rows",
        lambda: [
            {
                "symbol": "AAPL",
                "name": "Apple Inc. Common Stock",
                "sector": "Technology",
                "industry": "Computer Manufacturing",
            },
            {
                "symbol": "PFE",
                "name": "Pfizer Inc. Common Stock",
                "sector": "Health Care",
                "industry": "Biotechnology",
            },
        ],
    )

    profiles = load_us_profiles_from_screener(sectors=parse_sectors("Technology"))

    assert [profile.ticker for profile in profiles] == ["AAPL"]
    assert profiles[0].business == "Technology / Computer Manufacturing"
    assert profiles[0].sector == "Technology"


def test_load_us_profiles_does_not_fallback_to_unfiltered_directory_when_sector_filter_fails(
    monkeypatch,
) -> None:
    def raise_screener_error() -> list[dict[str, str]]:
        raise UniverseError("screener unavailable")

    monkeypatch.setattr("stock_alerts.universe._fetch_nasdaq_screener_rows", raise_screener_error)

    try:
        load_us_profiles(sectors=parse_sectors("Technology"))
    except UniverseError as exc:
        assert "screener unavailable" in str(exc)
    else:
        raise AssertionError("expected UniverseError")
