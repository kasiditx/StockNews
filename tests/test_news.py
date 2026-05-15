from __future__ import annotations

from stock_alerts.news import _summarize_description


def test_summarize_description_cleans_html() -> None:
    summary = _summarize_description(
        "<p>Company reports <strong>strong earnings</strong> and raises guidance.</p>",
        fallback_title="Fallback",
    )

    assert summary == "Company reports strong earnings and raises guidance."


def test_summarize_description_falls_back_to_title() -> None:
    summary = _summarize_description(None, fallback_title="Stock jumps after new contract")

    assert summary == "Stock jumps after new contract"
