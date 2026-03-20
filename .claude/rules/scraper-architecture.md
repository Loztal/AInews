# Scraper Architecture Rules

## Source Module Contract
Every file in `scraper/sources/` must:
1. Export a `fetch()` function returning `List[Dict]`
2. Never raise — catch `requests.RequestException`, return `[]` or `FALLBACK_*`
3. Set `"source"` key to one of: `anthropic_blog`, `ai_models`, `claude_code`, `desktop`, `office_plugins`, `chrome_extension`, `twitter`, `sdk_releases`, `community`
4. Strip HTML from summaries: `re.sub(r"<[^>]+>", "", text)`
5. Truncate summaries to ~300 chars, titles to ~120 chars
6. Use ISO 8601 dates with UTC timezone (`+00:00`), or empty string

## Fallback Pattern
Sources with network dependencies must have hardcoded `FALLBACK_*` data:
```python
FALLBACK_ITEMS = [{"title": ..., "date": "2026-...+00:00", ...}]

def fetch():
    try:
        resp = requests.get(URL, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Warning: Could not fetch ...: {e}")
        return list(FALLBACK_ITEMS)
    # parse and return
```

## Deduplication
- Happens in `main.py` (line ~48), not in individual sources (except internal dedup for RSS+curated)
- Case-insensitive, whitespace-stripped title matching
- First occurrence wins

## RSS Sources Pattern
Files using community RSS: `chrome_extension.py`, `desktop.py`, `office_plugins.py`, `web_sources.py`
- All share the same RSS URL: `https://raw.githubusercontent.com/taobojlen/anthropic-rss-feed/main/anthropic_news_rss.xml`
- Filter by keyword lists against `(title + " " + description).lower()`
- Append curated `CURATED_ITEMS` after RSS fetch
- Deduplicate internally before returning

## Adding a New Source (Checklist)
1. Create `scraper/sources/<name>.py` with `fetch()` function
2. Add import + entry to `sources` list in `scraper/main.py` (line ~11 and ~26)
3. Add category key to main.py's ensure-all-categories list (line ~62)
4. Add labels to both dicts in `scraper/summarizer.py` (lines ~49 and ~74)
5. Add to `CATEGORY_META` and `CATEGORY_ORDER` in `docs/js/app.js` (lines ~9 and ~19)
6. Add `.cat-<name> .category-dot` color rule in `docs/css/style.css`
7. Create `tests/test_<name>.py` with: fetch success, network error fallback, empty feed tests
8. Add fixture data to `tests/fixtures/` if needed
