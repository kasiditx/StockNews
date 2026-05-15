from __future__ import annotations

import re
from html import unescape
from urllib.parse import quote_plus
from xml.etree import ElementTree

import requests

from stock_alerts.models import NewsItem


REQUEST_TIMEOUT_SECONDS = 15
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
WHITESPACE_PATTERN = re.compile(r"\s+")
POSITIVE_NEWS_KEYWORDS = frozenset(
    {
        "beat",
        "beats",
        "upgrade",
        "upgraded",
        "raises",
        "raised",
        "growth",
        "record",
        "profit",
        "profits",
        "surge",
        "surges",
        "jump",
        "jumps",
        "contract",
        "partnership",
        "approval",
        "launch",
        "expansion",
        "dividend",
        "buyback",
    }
)
NEGATIVE_NEWS_KEYWORDS = frozenset(
    {
        "miss",
        "misses",
        "downgrade",
        "downgraded",
        "cuts",
        "cut",
        "loss",
        "losses",
        "fall",
        "falls",
        "drop",
        "drops",
        "lawsuit",
        "probe",
        "investigation",
        "recall",
        "delay",
        "weak",
        "warning",
        "bankruptcy",
    }
)


class NewsFetchError(RuntimeError):
    """Raised when news data cannot be fetched or parsed."""


def fetch_news(ticker: str, limit: int) -> tuple[NewsItem, ...]:
    query = quote_plus(ticker)
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={query}&region=US&lang=en-US"
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    if response.status_code >= 400:
        raise NewsFetchError(f"News request failed for {ticker} with HTTP {response.status_code}")

    root = ElementTree.fromstring(response.text)
    items: list[NewsItem] = []
    for item in root.findall("./channel/item"):
        title = _read_child_text(item, "title")
        link = _read_child_text(item, "link")
        summary = _summarize_description(_read_child_text(item, "description"), fallback_title=title)
        published = _read_child_text(item, "pubDate")
        if title and link:
            sentiment, sentiment_score = _score_news_sentiment(title=title, summary=summary)
            items.append(
                NewsItem(
                    title=unescape(title),
                    link=link,
                    summary=summary,
                    sentiment=sentiment,
                    sentiment_score=sentiment_score,
                    published=published,
                )
            )
        if len(items) >= limit:
            break
    return tuple(items)


def _read_child_text(item: ElementTree.Element, child_name: str) -> str | None:
    child = item.find(child_name)
    if child is None or child.text is None:
        return None
    return child.text.strip()


def _summarize_description(description: str | None, fallback_title: str | None) -> str | None:
    if description:
        cleaned_description = _clean_text(description)
        if cleaned_description:
            return _truncate_text(cleaned_description, max_length=240)

    if fallback_title:
        return _truncate_text(_clean_text(fallback_title), max_length=180)
    return None


def _clean_text(value: str) -> str:
    without_html = HTML_TAG_PATTERN.sub(" ", unescape(value))
    return WHITESPACE_PATTERN.sub(" ", without_html).strip()


def _truncate_text(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return value[: max_length - 1].rstrip() + "…"


def _score_news_sentiment(title: str, summary: str | None) -> tuple[str, int]:
    text = _clean_text(f"{title} {summary or ''}").lower()
    words = set(re.findall(r"[a-z]+", text))
    score = len(words.intersection(POSITIVE_NEWS_KEYWORDS)) - len(
        words.intersection(NEGATIVE_NEWS_KEYWORDS)
    )

    if score >= 2:
        return "positive", score
    if score <= -2:
        return "negative", score
    if score == 1:
        return "slightly_positive", score
    if score == -1:
        return "slightly_negative", score
    return "neutral", score
