"""Fetch Claude Code releases from GitHub Atom feed."""

import requests
import xml.etree.ElementTree as ET
import re


FEED_URL = "https://github.com/anthropics/claude-code/releases.atom"
ATOM_NS = "{http://www.w3.org/2005/Atom}"


def fetch():
    """Return list of recent Claude Code release items."""
    resp = requests.get(FEED_URL, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    items = []

    for entry in root.findall(f"{ATOM_NS}entry")[:2]:
        title = _text(entry, f"{ATOM_NS}title")
        updated = _text(entry, f"{ATOM_NS}updated")
        link_el = entry.find(f"{ATOM_NS}link")
        link = link_el.get("href", "") if link_el is not None else ""
        content_el = entry.find(f"{ATOM_NS}content")
        content_html = content_el.text if content_el is not None and content_el.text else ""

        items.append({
            "title": title,
            "date": updated,
            "url": link,
            "summary": _extract_highlights(content_html),
            "source": "claude_code",
        })

    return items


def _text(el, tag):
    child = el.find(tag)
    return child.text.strip() if child is not None and child.text else ""


def _extract_highlights(html):
    """Extract key highlights from release HTML content."""
    clean = re.sub(r"<[^>]+>", "\n", html)
    lines = [l.strip() for l in clean.splitlines() if l.strip()]
    highlights = []
    for line in lines[:10]:
        if line.startswith(("Added", "Fixed", "Changed", "Improved", "-", "*")):
            highlights.append(line.lstrip("-* "))
    if not highlights:
        highlights = lines[:3]
    return "; ".join(highlights[:5])[:300]
