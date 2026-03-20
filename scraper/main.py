"""Main orchestrator for the daily Claude briefing scraper."""

import json
import logging
import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

from scraper.sources import anthropic_blog, chrome_extension, claude_code, desktop, model_specs, office_plugins, release_notes, twitter_feed, sdk_releases, community
from scraper.summarizer import generate_summary


OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "data", "briefing.json")
ARCHIVE_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "data", "archive")


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
        ("SDK Releases", sdk_releases.fetch),
        ("Community", community.fetch),
    ]

    # Fetch all sources in parallel
    def _fetch_source(name, fetcher):
        try:
            items = fetcher()
            return name, items, None
        except Exception as e:
            return name, [], e

    with ThreadPoolExecutor(max_workers=len(sources)) as executor:
        futures = {
            executor.submit(_fetch_source, name, fetcher): name
            for name, fetcher in sources
        }
        for future in as_completed(futures):
            name, items, error = future.result()
            if error:
                log.error("  Error fetching %s: %s", name, error)
            else:
                log.info("  Got %d items from %s", len(items), name)
                all_items.extend(items)

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

    # Ensure all categories exist
    for key in ["anthropic_blog", "ai_models", "claude_code", "desktop", "office_plugins", "chrome_extension", "twitter", "sdk_releases", "community"]:
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

    # Archive a dated copy
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    archive_path = os.path.join(ARCHIVE_DIR, f"briefing-{date_str}.json")
    shutil.copy2(OUTPUT_PATH, archive_path)
    log.info("Archived to %s", archive_path)

    # Generate Atom feed
    from scraper.feed_generator import generate_feed
    feed_path = os.path.join(os.path.dirname(__file__), "..", "docs", "feed.xml")
    generate_feed(output, feed_path)
    log.info("Wrote Atom feed to %s", feed_path)

    total = sum(len(v) for v in categories.values())
    log.info("Done! Wrote %d items to %s", total, OUTPUT_PATH)


if __name__ == "__main__":
    run()
