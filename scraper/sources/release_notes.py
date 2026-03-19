"""Scrape Claude Help Center release notes for Desktop, Models, Chrome updates."""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone


RELEASE_NOTES_URL = "https://support.claude.com/en/articles/12138966-release-notes"

CATEGORY_KEYWORDS = {
    "ai_models": ["model", "opus", "sonnet", "haiku", "context window", "token", "1m"],
    "desktop": ["desktop", "cowork", "dock", "memory", "inline", "visualization"],
    "chrome_extension": ["chrome", "browser", "extension", "tab", "web store"],
    "office_plugins": ["excel", "powerpoint", "office 365", "office plugin", "office add-in",
                       "m365", "copilot", "add-in", "foundry", "microsoft 365"],
}


def fetch():
    """Scrape release notes and categorize items."""
    try:
        resp = requests.get(RELEASE_NOTES_URL, timeout=30, headers={
            "User-Agent": "AInews-Briefing-Bot/1.0"
        })
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Warning: Could not fetch release notes: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    items = []

    article = soup.find("article") or soup.find("div", class_=re.compile(r"article|content"))
    if not article:
        article = soup.body or soup

    current_date = ""
    current_section = ""

    for element in article.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        text = element.get_text(strip=True)
        if not text:
            continue

        if element.name in ("h1", "h2", "h3"):
            date_match = re.search(
                r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4})",
                text
            )
            if date_match:
                try:
                    parsed = datetime.strptime(
                        date_match.group(1).replace(",", ""), "%B %d %Y"
                    )
                    current_date = parsed.replace(tzinfo=timezone.utc).isoformat()
                except ValueError:
                    pass
            current_section = text
            continue

        if element.name in ("p", "li") and len(text) > 20:
            category = _categorize(text, current_section)
            if category:
                items.append({
                    "title": text[:120] + ("..." if len(text) > 120 else ""),
                    "date": current_date,
                    "url": RELEASE_NOTES_URL,
                    "summary": text[:300],
                    "source": category,
                })

    return items[:30]


def _categorize(text, section):
    """Determine which category a text item belongs to."""
    combined = (text + " " + section).lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            return category
    return None
