from __future__ import annotations

from stock_alerts.universe import (
    UniverseError,
    _is_supported_us_common_stock,
    build_group_filter,
    load_us_profiles,
    load_thai_profiles,
    load_us_profiles_from_screener,
    parse_groups,
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


def test_parse_groups_accepts_requested_set_codes_and_aliases() -> None:
    groups = parse_groups("FINCIAL, INDUS, Services, Technology")

    assert groups == frozenset({"FINCIAL", "INDUS", "SERVICE", "TECH"})


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


def test_load_us_profiles_from_screener_filters_by_requested_groups(monkeypatch) -> None:
    monkeypatch.setattr(
        "stock_alerts.universe._fetch_nasdaq_screener_rows",
        lambda: [
            {
                "symbol": "BRK/B",
                "name": "Berkshire Hathaway Inc.",
                "sector": "",
                "industry": "",
            },
            {
                "symbol": "JPM",
                "name": "JPMorgan Chase & Co. Common Stock",
                "sector": "Finance",
                "industry": "Major Banks",
            },
            {
                "symbol": "NVDA",
                "name": "NVIDIA Corporation Common Stock",
                "sector": "Technology",
                "industry": "Semiconductors",
            },
            {
                "symbol": "UPS",
                "name": "United Parcel Service Inc. Common Stock",
                "sector": "Industrials",
                "industry": "Trucking Freight/Courier Services",
            },
            {
                "symbol": "PFE",
                "name": "Pfizer Inc. Common Stock",
                "sector": "Health Care",
                "industry": "Biotechnology",
            },
        ],
    )

    profiles = load_us_profiles_from_screener(
        group_filter=build_group_filter(raw_groups="FINCIAL,INDUS,TECH", raw_sectors=""),
    )

    assert [profile.ticker for profile in profiles] == ["BRK-B", "JPM", "NVDA", "UPS", "SIEGY"]


def test_load_thai_profiles_filters_by_set_sector_and_subsector_codes(tmp_path) -> None:
    thai_universe = tmp_path / "universe.th.csv"
    thai_universe.write_text(
        "\n".join(
            [
                "ticker,name,business,sector,industry",
                "BBL,Bangkok Bank,Bank,FINCIAL,BANK",
                "ADVANC,Advanced Info Service,Telecom,TECH,ICT",
                "PTT,PTT,Energy,RESOURC,ENERG",
            ]
        ),
        encoding="utf-8",
    )

    profiles = load_thai_profiles(
        thai_universe,
        group_filter=build_group_filter(raw_groups="FINCIAL,TECH", raw_sectors=""),
    )

    assert [profile.ticker for profile in profiles] == ["BBL.BK", "ADVANC.BK"]


def test_load_us_profiles_does_not_fallback_to_unfiltered_directory_when_sector_filter_fails(
    monkeypatch,
) -> None:
    def raise_screener_error() -> list[dict[str, str]]:
        raise UniverseError("screener unavailable")

    monkeypatch.setattr("stock_alerts.universe._fetch_nasdaq_screener_rows", raise_screener_error)

    try:
        load_us_profiles(group_filter=build_group_filter(raw_groups="TECH", raw_sectors=""))
    except UniverseError as exc:
        assert "screener unavailable" in str(exc)
    else:
        raise AssertionError("expected UniverseError")
