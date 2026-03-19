"""Main orchestrator for the daily Claude briefing scraper."""

import json
import os
from datetime import datetime, timezone
from collections import defaultdict

from scraper.sources import anthropic_blog, claude_code, model_specs, release_notes, web_sources
from scraper.summarizer import generate_summary


OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "data", "briefing.json")


def run():
    """Fetch all sources, categorize, summarize, and write output JSON."""
    print("Starting daily briefing scraper...")

    all_items = []

    # Fetch from all sources
    sources = [
        ("Model Specs", model_specs.fetch),
        ("Web Sources", web_sources.fetch),
        ("Anthropic Blog", anthropic_blog.fetch),
        ("Claude Code", claude_code.fetch),
        ("Release Notes", release_notes.fetch),
    ]

    for name, fetcher in sources:
        try:
            print(f"  Fetching {name}...")
            items = fetcher()
            print(f"    Got {len(items)} items")
            all_items.extend(items)
        except Exception as e:
            print(f"    Error fetching {name}: {e}")

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
    for key in ["anthropic_blog", "ai_models", "claude_code", "desktop", "office_plugins", "chrome_extension"]:
        if key not in categories:
            categories[key] = []

    # Generate AI summary
    print("  Generating briefing summary...")
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
    print(f"Done! Wrote {total} items to {OUTPUT_PATH}")


if __name__ == "__main__":
    run()
