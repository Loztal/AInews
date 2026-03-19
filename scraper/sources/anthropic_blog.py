"""Fetch Anthropic blog posts from community-maintained RSS feed."""

import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


FEED_URL = "https://raw.githubusercontent.com/taobojlen/anthropic-rss-feed/main/anthropic_news_rss.xml"


def fetch():
    """Return list of recent Anthropic blog post items."""
    resp = requests.get(FEED_URL, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    items = []

    for item_el in root.findall(".//item")[:20]:
        title = _text(item_el, "title")
        link = _text(item_el, "link")
        pub_date = _text(item_el, "pubDate")
        description = _text(item_el, "description")

        date_iso = ""
        if pub_date:
            try:
                date_iso = parsedate_to_datetime(pub_date).isoformat()
            except Exception:
                pass

        items.append({
            "title": title,
            "date": date_iso,
            "url": link,
            "summary": _clean(description),
            "source": "anthropic_blog",
        })

    return items


def _text(el, tag):
    child = el.find(tag)
    return child.text.strip() if child is not None and child.text else ""


def _clean(text):
    clean = re.sub(r"<[^>]+>", "", text)
    return clean[:300].strip() + ("..." if len(clean) > 300 else "")
