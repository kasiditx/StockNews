from __future__ import annotations

from stock_alerts.news import _parse_yfinance_news_item, _score_news_sentiment, _summarize_description


def test_summarize_description_cleans_html() -> None:
    summary = _summarize_description(
        "<p>Company reports <strong>strong earnings</strong> and raises guidance.</p>",
        fallback_title="Fallback",
    )

    assert summary == "Company reports strong earnings and raises guidance."


def test_summarize_description_falls_back_to_title() -> None:
    summary = _summarize_description(None, fallback_title="Stock jumps after new contract")

    assert summary == "Stock jumps after new contract"


def test_score_news_sentiment_detects_positive_catalyst() -> None:
    sentiment, score = _score_news_sentiment(
        title="Company beats profit estimates and raises guidance",
        summary=None,
    )

    assert sentiment == "positive"
    assert score >= 2


def test_parse_yfinance_news_item_reads_nested_content() -> None:
    item = _parse_yfinance_news_item(
        {
            "content": {
                "title": "Company beats profit estimates",
                "summary": "Revenue growth remains strong.",
                "pubDate": "2026-05-15T16:22:53Z",
                "canonicalUrl": {"url": "https://example.com/news"},
            }
        }
    )

    assert item is not None
    assert item.title == "Company beats profit estimates"
    assert item.summary == "Revenue growth remains strong."
    assert item.link == "https://example.com/news"
    assert item.published == "2026-05-15T16:22:53Z"
