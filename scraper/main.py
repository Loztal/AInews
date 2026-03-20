"""Main orchestrator for the daily Claude briefing scraper."""

import json
import logging
import os
from datetime import datetime, timezone
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

from scraper.sources import anthropic_blog, chrome_extension, claude_code, desktop, model_specs, office_plugins, release_notes, twitter_feed
from scraper.summarizer import generate_summary


OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "data", "briefing.json")


def run():
    """Fetch all sources, categorize, summarize, and write output JSON."""
    log = logging.getLogger(__name__)
    log.info("Starting daily briefing scraper...")

    all_items = []

    # Fetch from all sources
    sources = [
        ("Model Specs", model_specs.fetch),
        ("Chrome Extension", chrome_extension.fetch),
        ("Desktop App", desktop.fetch),
        ("Office Plugins", office_plugins.fetch),
        ("Twitter", twitter_feed.fetch),
        ("Anthropic Blog", anthropic_blog.fetch),
        ("Claude Code", claude_code.fetch),
        ("Release Notes", release_notes.fetch),
    ]

    for name, fetcher in sources:
        try:
            log.info("Fetching %s...", name)
            items = fetcher()
            log.info("  Got %d items from %s", len(items), name)
            all_items.extend(items)
        except Exception as e:
            log.error("  Error fetching %s: %s", name, e)

    # Categorize items
    categories = defaultdict(list)
    seen_titles = set()
    for item in all_items:
        title_key = item["title"].lower().strip()
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        source = item.pop("source", "anthropic_blog")
        categories[source].append(item)

    # Sort each category by date (newest first)
    for key in categories:
        categories[key].sort(key=lambda x: x.get("date", ""), reverse=True)

    # Ensure all 6 categories exist
    for key in ["anthropic_blog", "ai_models", "claude_code", "desktop", "office_plugins", "chrome_extension", "twitter"]:
        if key not in categories:
            categories[key] = []

    # Generate AI summary
    log.info("Generating briefing summary...")
    summary = generate_summary(dict(categories))

    # Build output
    output = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "briefing_summary": summary,
        "categories": dict(categories),
    }

    # Write JSON
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    total = sum(len(v) for v in categories.values())
    log.info("Done! Wrote %d items to %s", total, OUTPUT_PATH)


if __name__ == "__main__":
    run()
