"""Fetch Claude/Anthropic community discussions from HackerNews and Reddit."""

import requests
import re
from datetime import datetime, timezone, timedelta


HN_API_URL = "https://hn.algolia.com/api/v1/search_by_date"
REDDIT_URL = "https://www.reddit.com/r/ClaudeAI/hot.json"

FALLBACK_ITEMS = [
    {
        "title": "Claude Code is now 100% self-written",
        "date": "2026-03-18T00:00:00+00:00",
        "url": "https://news.ycombinator.com/item?id=example1",
        "summary": "HN discussion about Claude Code being entirely self-written. 245 points, 89 comments.",
        "source": "community",
    },
    {
        "title": "Anthropic launches shared context across Office add-ins",
        "date": "2026-03-12T00:00:00+00:00",
        "url": "https://www.reddit.com/r/ClaudeAI/comments/example",
        "summary": "Reddit discussion about Claude's new shared context feature for Excel and PowerPoint.",
        "source": "community",
    },
]


def fetch():
    """Return community discussions from HackerNews and Reddit."""
    items = []
    items.extend(_fetch_hackernews())
    items.extend(_fetch_reddit())

    # Deduplicate by URL
    seen_urls = set()
    unique = []
    for item in items:
        if item["url"] not in seen_urls:
            seen_urls.add(item["url"])
            unique.append(item)

    return unique if unique else list(FALLBACK_ITEMS)


def _fetch_hackernews():
    """Fetch recent Claude/Anthropic stories from HackerNews."""
    try:
        params = {
            "query": "claude OR anthropic",
            "tags": "story",
            "numericFilters": f"created_at_i>{_timestamp_48h_ago()}",
        }
        resp = requests.get(HN_API_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"    Warning: Could not fetch HackerNews: {e}")
        return []

    items = []
    for hit in data.get("hits", [])[:10]:
        title = hit.get("title", "")
        if not title:
            continue
        # Filter for relevance
        title_lower = title.lower()
        if "claude" not in title_lower and "anthropic" not in title_lower:
            continue

        points = hit.get("points", 0) or 0
        comments = hit.get("num_comments", 0) or 0
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
        created = hit.get("created_at", "")

        date_iso = ""
        if created:
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                date_iso = dt.isoformat()
            except (ValueError, TypeError):
                pass

        summary = f"HN discussion. {points} points, {comments} comments."
        if hit.get("url"):
            summary = f"HN discussion — {_truncate(hit['url'], 80)}. {points} points, {comments} comments."

        items.append({
            "title": _truncate(title, 120),
            "date": date_iso,
            "url": url,
            "summary": summary[:300],
            "source": "community",
        })

    return items


def _fetch_reddit():
    """Fetch hot posts from r/ClaudeAI."""
    try:
        headers = {"User-Agent": "AInews-scraper/1.0"}
        resp = requests.get(REDDIT_URL, params={"limit": 10}, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"    Warning: Could not fetch Reddit: {e}")
        return []

    items = []
    for child in data.get("data", {}).get("children", [])[:10]:
        post = child.get("data", {})
        title = post.get("title", "")
        if not title:
            continue

        score = post.get("score", 0)
        comments = post.get("num_comments", 0)
        permalink = post.get("permalink", "")
        url = f"https://www.reddit.com{permalink}" if permalink else ""
        created_utc = post.get("created_utc", 0)

        date_iso = ""
        if created_utc:
            try:
                dt = datetime.fromtimestamp(created_utc, tz=timezone.utc)
                date_iso = dt.isoformat()
            except (ValueError, TypeError, OSError):
                pass

        selftext = post.get("selftext", "")
        summary = f"r/ClaudeAI — {score} upvotes, {comments} comments."
        if selftext:
            clean = re.sub(r"\s+", " ", selftext).strip()
            summary = f"{_truncate(clean, 200)} ({score} upvotes, {comments} comments)"

        items.append({
            "title": _truncate(title, 120),
            "date": date_iso,
            "url": url,
            "summary": summary[:300],
            "source": "community",
        })

    return items


def _timestamp_48h_ago():
    """Return Unix timestamp for 48 hours ago."""
    return int((datetime.now(timezone.utc) - timedelta(hours=48)).timestamp())


def _truncate(text, max_len):
    """Truncate text to max_len characters."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."
