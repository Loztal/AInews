"""Fetch original tweets from @bcherny via RSSHub RSS bridge."""

import requests
import xml.etree.ElementTree as ET
import re
from email.utils import parsedate_to_datetime


RSSHUB_URL = "https://rsshub.app/twitter/user/bcherny/excludeReplies=1"
ACCOUNT = "bcherny"


def fetch():
    """Return original tweets (no replies) from @bcherny."""
    items = _fetch_from_rss()

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
    """Fetch tweets via RSSHub RSS feed."""
    try:
        resp = requests.get(RSSHUB_URL, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"    Warning: Could not fetch Twitter RSS for @{ACCOUNT}: {e}")
        return []

    items = []
    root = ET.fromstring(resp.text)

    for item_el in root.findall(".//item"):
        title = _text(item_el, "title")
        link = _text(item_el, "link")
        pub_date = _text(item_el, "pubDate")
        description = _text(item_el, "description")

        # Skip replies (safety net — RSSHub should already exclude them)
        text = (title or description).strip()
        if text.startswith("@"):
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
            "title": title[:120] if title else clean_summary[:120],
            "date": date_iso,
            "url": link,
            "summary": clean_summary,
            "source": "twitter",
        })

    return items


def _text(el, tag):
    child = el.find(tag)
    return child.text.strip() if child is not None and child.text else ""
