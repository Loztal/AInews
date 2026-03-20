---
name: run-scraper
description: Run the full scraper pipeline with tests and output validation
allowed-tools: Bash, Read, Grep
---

Run the full AInews scraper pipeline with validation.

## Steps

1. **Run tests first** — stop if any fail:
   ```bash
   python -m pytest tests/ -v --tb=short
   ```

2. **Run the scraper**:
   ```bash
   python -m scraper.main
   ```

3. **Validate output** — read `docs/data/briefing.json` and check:
   - Top-level keys: `generated` (ISO timestamp), `briefing_summary` (non-empty string), `categories` (object)
   - All 7 categories exist: `anthropic_blog`, `ai_models`, `claude_code`, `desktop`, `office_plugins`, `chrome_extension`, `twitter`
   - Each item has required keys: `title` (non-empty), `date`, `url`, `summary`
   - No duplicate titles (case-insensitive) across categories

4. **Report results**: item counts per category, total items, any validation issues found.
