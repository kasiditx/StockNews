from __future__ import annotations

from stock_alerts.universe import _is_supported_us_common_stock


def test_us_common_stock_filter_allows_plain_common_stock() -> None:
    assert _is_supported_us_common_stock("AAPL", "Apple Inc. Common Stock")


def test_us_common_stock_filter_rejects_warrants_units_and_preferred() -> None:
    assert not _is_supported_us_common_stock("AACIW", "Armada Acquisition Corp. I Warrant")
    assert not _is_supported_us_common_stock("AACIU", "Armada Acquisition Corp. I Unit")
    assert not _is_supported_us_common_stock("WRB$E", "W. R. Berkley Corporation Preferred Stock")
