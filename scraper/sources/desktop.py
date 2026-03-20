"""Fetch Claude Desktop app news from RSS and curated milestones."""

import requests
import xml.etree.ElementTree as ET
import re
from email.utils import parsedate_to_datetime


ANTHROPIC_NEWS_RSS = "https://raw.githubusercontent.com/taobojlen/anthropic-rss-feed/main/anthropic_news_rss.xml"

DESKTOP_KEYWORDS = ["claude desktop", "desktop app", "cowork", "cowork mode",
                    "desktop agent", "desktop extension"]

# Key milestones for Claude Desktop, sourced from Anthropic announcements.
CURATED_ITEMS = [
    {
        "title": "Claude Cowork — agentic mode for Desktop",
        "date": "2026-02-04T00:00:00+00:00",
        "url": "https://www.anthropic.com/news/claude-is-a-space-to-think",
        "summary": "Claude Cowork turns Claude into a digital coworker inside the Desktop app. "
                   "It can read, edit, create, and organize files on your computer — no terminal required. "
                   "Available on Pro and Max plans as a research preview.",
        "source": "desktop",
    },
    {
        "title": "MCP Desktop Extensions — one-click install",
        "date": "2025-11-01T00:00:00+00:00",
        "url": "https://claude.com/download",
        "summary": "Claude Desktop now supports one-click installation of MCP servers, giving Claude "
                   "controlled access to local tools and files. A curated Connectors Directory with "
                   "admin guardrails is available for Team and Enterprise plans.",
        "source": "desktop",
    },
    {
        "title": "Claude Desktop launches on Windows",
        "date": "2025-05-01T00:00:00+00:00",
        "url": "https://claude.com/download",
        "summary": "Claude Desktop is now available on Windows (MSIX installer) alongside the existing "
                   "macOS app. Features include inline visualizations, drag-and-drop file support, "
                   "and org-level update control for staged deployment.",
        "source": "desktop",
    },
]


def fetch():
    """Return Desktop app news from RSS + curated milestones."""
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
    """Scan Anthropic news RSS for Desktop-related articles."""
    try:
        resp = requests.get(ANTHROPIC_NEWS_RSS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"    Warning: Could not fetch RSS for Desktop news: {e}")
        return []

    items = []
    root = ET.fromstring(resp.text)

    for item_el in root.findall(".//item"):
        title = _text(item_el, "title")
        link = _text(item_el, "link")
        pub_date = _text(item_el, "pubDate")
        description = _text(item_el, "description")

        combined = (title + " " + description).lower()
        if not any(kw in combined for kw in DESKTOP_KEYWORDS):
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
            "source": "desktop",
        })

    return items


def _text(el, tag):
    child = el.find(tag)
    return child.text.strip() if child is not None and child.text else ""
