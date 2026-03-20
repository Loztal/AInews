"""Fetch Claude for Chrome extension news from RSS and curated milestones."""

import requests
import xml.etree.ElementTree as ET
import re
from email.utils import parsedate_to_datetime


ANTHROPIC_NEWS_RSS = "https://raw.githubusercontent.com/taobojlen/anthropic-rss-feed/main/anthropic_news_rss.xml"

CHROME_KEYWORDS = ["claude for chrome", "claude in chrome", "chrome extension",
                   "browser extension", "browser agent"]

# Key milestones for Claude for Chrome, sourced from Anthropic announcements.
CURATED_ITEMS = [
    {
        "title": "Claude for Chrome now in beta for all paid plans",
        "date": "2025-12-01T00:00:00+00:00",
        "url": "https://www.anthropic.com/news/claude-for-chrome",
        "summary": "Claude in Chrome is now available to all Pro, Max, Team, and Enterprise users. "
                   "Features include scheduled tasks, workflow recording, multi-tab browsing, and "
                   "Claude Code integration.",
        "source": "chrome_extension",
    },
    {
        "title": "Piloting Claude in Chrome — Research preview",
        "date": "2025-08-01T00:00:00+00:00",
        "url": "https://www.anthropic.com/news/claude-for-chrome",
        "summary": "Anthropic launches Claude in Chrome as a research preview with 1,000 testers. "
                   "The browser extension lets Claude read, click, and navigate websites alongside you.",
        "source": "chrome_extension",
    },
]


def fetch():
    """Return Chrome extension news from RSS + curated milestones."""
    items = _fetch_from_rss()
    items.extend(CURATED_ITEMS)

    # Deduplicate by title (case-insensitive), keep first occurrence
    seen = set()
    unique = []
    for item in items:
        key = item["title"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique


def _fetch_from_rss():
    """Scan Anthropic news RSS for Chrome-related articles."""
    try:
        resp = requests.get(ANTHROPIC_NEWS_RSS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"    Warning: Could not fetch RSS for Chrome news: {e}")
        return []

    items = []
    root = ET.fromstring(resp.text)

    for item_el in root.findall(".//item"):
        title = _text(item_el, "title")
        link = _text(item_el, "link")
        pub_date = _text(item_el, "pubDate")
        description = _text(item_el, "description")

        combined = (title + " " + description).lower()
        if not any(kw in combined for kw in CHROME_KEYWORDS):
            continue

        date_iso = ""
        if pub_date:
            try:
                date_iso = parsedate_to_datetime(pub_date).isoformat()
            except Exception:
                pass

        clean_summary = re.sub(r"<[^>]+>", "", description)
        clean_summary = clean_summary[:300].strip() + ("..." if len(clean_summary) > 300 else "")

        items.append({
            "title": title,
            "date": date_iso,
            "url": link,
            "summary": clean_summary,
            "source": "chrome_extension",
        })

    return items


def _text(el, tag):
    child = el.find(tag)
    return child.text.strip() if child is not None and child.text else ""
