"""Fetch AI model, Chrome extension, and Office plugin news from Anthropic news page."""

import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


ANTHROPIC_NEWS_RSS = "https://raw.githubusercontent.com/taobojlen/anthropic-rss-feed/main/anthropic_news_rss.xml"

MODEL_KEYWORDS = ["opus", "sonnet", "haiku", "claude 4", "claude 3", "model update",
                   "benchmark", "context window", "system prompt", "extended thinking"]
CHROME_KEYWORDS = ["claude for chrome", "claude in chrome", "chrome extension",
                   "browser extension", "chrome web store", "browser agent"]
OFFICE_KEYWORDS = ["excel", "powerpoint", "office 365", "office plugin", "office add-in",
                   "m365", "copilot", "add-in", "foundry", "microsoft 365"]


def fetch():
    """Fetch news items filtered for AI models, Chrome, and Office categories."""
    resp = requests.get(ANTHROPIC_NEWS_RSS, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    items = []

    for item_el in root.findall(".//item")[:30]:
        title = _text(item_el, "title")
        link = _text(item_el, "link")
        pub_date = _text(item_el, "pubDate")
        description = _text(item_el, "description")

        combined = (title + " " + description).lower()

        date_iso = ""
        if pub_date:
            try:
                date_iso = parsedate_to_datetime(pub_date).isoformat()
            except Exception:
                pass

        clean_summary = _clean(description)

        if any(kw in combined for kw in MODEL_KEYWORDS):
            items.append({
                "title": title,
                "date": date_iso,
                "url": link,
                "summary": clean_summary,
                "source": "ai_models",
            })
        elif any(kw in combined for kw in CHROME_KEYWORDS):
            items.append({
                "title": title,
                "date": date_iso,
                "url": link,
                "summary": clean_summary,
                "source": "chrome_extension",
            })
        elif any(kw in combined for kw in OFFICE_KEYWORDS):
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


def _clean(text):
    clean = re.sub(r"<[^>]+>", "", text)
    return clean[:300].strip() + ("..." if len(clean) > 300 else "")
