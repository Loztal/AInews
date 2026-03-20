"""Fetch Anthropic blog posts from community-maintained RSS feed."""

import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


FEED_URL = "https://raw.githubusercontent.com/taobojlen/anthropic-rss-feed/main/anthropic_news_rss.xml"


FALLBACK_POSTS = [
    {
        "title": "Anthropic invests $100 million to launch The Anthropic Partner Network",
        "date": "2026-03-18T00:00:00+00:00",
        "url": "https://www.anthropic.com/news/anthropic-partner-network",
        "summary": "Anthropic launches $100M Partner Network to accelerate enterprise AI adoption through consulting, technology, and implementation partnerships.",
        "source": "anthropic_blog",
    },
    {
        "title": "Introducing the Anthropic Institute",
        "date": "2026-03-13T00:00:00+00:00",
        "url": "https://www.anthropic.com/news/anthropic-institute",
        "summary": "Anthropic establishes a new research institute focused on AI safety, policy, and governance to advance responsible AI development.",
        "source": "anthropic_blog",
    },
    {
        "title": "Expanding access in Asia-Pacific",
        "date": "2026-03-11T00:00:00+00:00",
        "url": "https://www.anthropic.com/news/expanding-access-asia-pacific",
        "summary": "Claude is now available to more users across Asia-Pacific, expanding Anthropic's global reach with localized support.",
        "source": "anthropic_blog",
    },
    {
        "title": "Partnering with Mozilla to advance AI transparency",
        "date": "2026-03-06T00:00:00+00:00",
        "url": "https://www.anthropic.com/news/mozilla-partnership",
        "summary": "Anthropic and Mozilla partner to promote AI transparency, open research, and responsible deployment standards.",
        "source": "anthropic_blog",
    },
]


def fetch():
    """Return list of recent Anthropic blog post items."""
    try:
        resp = requests.get(FEED_URL, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"    Warning: Could not fetch Anthropic blog RSS: {e}")
        print("    Using fallback blog posts")
        return list(FALLBACK_POSTS)

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
