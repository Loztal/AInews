"""Fetch Claude for Office (Excel & PowerPoint) plugin news from RSS and curated milestones."""

import requests
import xml.etree.ElementTree as ET
import re
from email.utils import parsedate_to_datetime


ANTHROPIC_NEWS_RSS = "https://raw.githubusercontent.com/taobojlen/anthropic-rss-feed/main/anthropic_news_rss.xml"

OFFICE_KEYWORDS = ["claude for excel", "claude for powerpoint", "office add-in",
                   "office plugin", "excel add-in", "powerpoint add-in",
                   "claude in excel", "claude in powerpoint"]

# Key milestones for Claude Office plugins, sourced from Anthropic announcements.
CURATED_ITEMS = [
    {
        "title": "Shared context across Excel and PowerPoint add-ins",
        "date": "2026-03-11T00:00:00+00:00",
        "url": "https://venturebeat.com/orchestration/anthropic-gives-claude-shared-context-across-microsoft-excel-and-powerpoint",
        "summary": "The Claude add-ins for Excel and PowerPoint now share a single conversation "
                   "thread, eliminating repeated setup when switching between apps. Reusable Skills "
                   "let teams save repeatable workflows as one-click actions. Available on Mac and "
                   "Windows for all paid plans.",
        "source": "office_plugins",
    },
    {
        "title": "Claude for PowerPoint — research preview",
        "date": "2026-02-05T00:00:00+00:00",
        "url": "https://marketplace.microsoft.com/en-us/product/office/wa200010001?tab=overview",
        "summary": "Claude for PowerPoint launches as a research preview. It reads slide masters, "
                   "layouts, fonts, and color schemes to generate or revise content while maintaining "
                   "brand consistency. Creates native editable charts and diagrams. Available for "
                   "Max, Team, and Enterprise plans.",
        "source": "office_plugins",
    },
    {
        "title": "Claude for Excel — now available for Pro subscribers",
        "date": "2026-01-24T00:00:00+00:00",
        "url": "https://marketplace.microsoft.com/en-us/product/saas/wa200009404?tab=overview",
        "summary": "Claude for Excel expands from Max/Enterprise to all Pro subscribers ($20/mo). "
                   "Supports full spreadsheet functionality including pivot tables, chart modifications, "
                   "and conditional formatting while keeping formulas and dependencies intact.",
        "source": "office_plugins",
    },
    {
        "title": "Claude for Excel — beta launch",
        "date": "2025-10-01T00:00:00+00:00",
        "url": "https://marketplace.microsoft.com/en-us/product/saas/wa200009404?tab=overview",
        "summary": "Anthropic releases Claude for Excel as a Microsoft Office add-in. Initially "
                   "available in beta for Max and Enterprise plans. Claude can read, understand, "
                   "and modify spreadsheets directly from a sidebar panel.",
        "source": "office_plugins",
    },
]


def fetch():
    """Return Office plugin news from RSS + curated milestones."""
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
    """Scan Anthropic news RSS for Office plugin-related articles."""
    try:
        resp = requests.get(ANTHROPIC_NEWS_RSS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"    Warning: Could not fetch RSS for Office plugin news: {e}")
        return []

    items = []
    root = ET.fromstring(resp.text)

    for item_el in root.findall(".//item"):
        title = _text(item_el, "title")
        link = _text(item_el, "link")
        pub_date = _text(item_el, "pubDate")
        description = _text(item_el, "description")

        combined = (title + " " + description).lower()
        if not any(kw in combined for kw in OFFICE_KEYWORDS):
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
            "source": "office_plugins",
        })

    return items


def _text(el, tag):
    child = el.find(tag)
    return child.text.strip() if child is not None and child.text else ""
