from __future__ import annotations

from html import unescape
from urllib.parse import quote_plus
from xml.etree import ElementTree

import requests

from stock_alerts.models import NewsItem


REQUEST_TIMEOUT_SECONDS = 15


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
        published = _read_child_text(item, "pubDate")
        if title and link:
            items.append(NewsItem(title=unescape(title), link=link, published=published))
        if len(items) >= limit:
            break
    return tuple(items)


def _read_child_text(item: ElementTree.Element, child_name: str) -> str | None:
    child = item.find(child_name)
    if child is None or child.text is None:
        return None
    return child.text.strip()
