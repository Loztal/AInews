"""Fetch original tweets from @bcherny via RSSHub RSS bridge."""

import requests
import xml.etree.ElementTree as ET
import re
from email.utils import parsedate_to_datetime


RSSHUB_URL = "https://rsshub.app/twitter/user/bcherny/excludeReplies=1"
ACCOUNT = "bcherny"

# Curated fallback tweets (sourced from x.com/@bcherny, March 2026).
FALLBACK_TWEETS = [
    {
        "title": "New in Claude Code: Code Review — a team of agents runs a deep review on every PR",
        "date": "2026-03-09T00:00:00",
        "url": "https://x.com/bcherny/status/2031089411820228645",
        "summary": "New in Claude Code: Code Review. A team of agents runs a deep review on every PR. Code output per Anthropic engineer is up 200% this year and reviews were the bottleneck.",
        "source": "twitter",
    },
    {
        "title": "Can confirm Claude Code is 100% written by Claude Code",
        "date": "2026-03-07T00:00:00",
        "url": "https://x.com/bcherny/status/2007179832300581177",
        "summary": "Boris Cherny confirmed that Claude Code is now 100% written by Claude Code itself, up from roughly 80% in May 2025.",
        "source": "twitter",
    },
    {
        "title": "Tips for using Claude Code, sourced directly from the Claude Code team",
        "date": "2026-02-19T00:00:00",
        "url": "https://x.com/bcherny/status/2017742741636321619",
        "summary": "Tips for using Claude Code sourced from the team. There is no one right way to use Claude Code — everyone's setup is different.",
        "source": "twitter",
    },
    {
        "title": "How I use Claude Code — my setup might be surprisingly vanilla",
        "date": "2026-02-05T00:00:00",
        "url": "https://x.com/bcherny/status/2007179832300581177",
        "summary": "I run 5 Claudes in parallel in my terminal. I number my tabs 1-5, and use system notifications to know when a Claude needs input. I exclusively use Opus 4.5 — it's the best coding model I've ever used.",
        "source": "twitter",
    },
]


def fetch():
    """Return original tweets (no replies) from @bcherny."""
    items = _fetch_from_rss()
    if not items:
        print("    Using fallback tweets")
        items = FALLBACK_TWEETS

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
