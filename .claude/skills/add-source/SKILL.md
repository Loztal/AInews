---
name: add-source
description: Scaffold a new scraper source module with tests and all required integration points
argument-hint: <source-name> <category-key>
---

Create a new scraper source module. Arguments: $0 = source name (snake_case, e.g. "github_discussions"), $1 = category key (e.g. "github").

Follow these steps precisely:

1. **Create source module** `scraper/sources/$0.py`:
   - Module docstring explaining the source
   - Constants: `FEED_URL` or `API_URL`, `FALLBACK_ITEMS` (1-2 hardcoded items)
   - Private fetch function: `_fetch_from_rss()` or `_fetch_from_api()`
   - Public `fetch()` that wraps private in try/except `requests.RequestException`
   - On error: `print(f"Warning: ...")` then `return list(FALLBACK_ITEMS)`
   - Item schema: `{"title": str, "date": "ISO8601+00:00", "url": str, "summary": str, "source": "$1"}`

2. **Register in main.py** (`scraper/main.py`):
   - Add import at line ~11
   - Add entry to `sources` list at line ~26
   - Add `"$1"` to ensure-all-categories list at line ~62

3. **Add labels in summarizer.py** (`scraper/summarizer.py`):
   - Add to `category_labels` dict in `_format_items_for_prompt()` (line ~49)
   - Add to `category_labels` dict in `_template_summary()` (line ~74)

4. **Add to frontend** (`docs/js/app.js`):
   - Add to `CATEGORY_META` object (line ~9) with label and icon color
   - Add to `CATEGORY_ORDER` array (line ~19)

5. **Add CSS category color** (`docs/css/style.css`):
   - Add `.cat-$1 .category-dot { background: <color>; }` rule

6. **Create tests** `tests/test_$0.py`:
   - `TestFetch`: success with mocked HTTP, network error uses fallback, empty feed returns empty/fallback
   - Use `@responses.activate` for HTTP mocking
   - Verify item schema compliance

7. **Add fixtures** to `tests/fixtures/` if the source parses XML/HTML

8. **Run tests**: `python -m pytest tests/test_$0.py -v --tb=short`
