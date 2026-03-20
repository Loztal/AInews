---
name: validate-briefing
description: Validate the structure and content of briefing.json without running the scraper
allowed-tools: Read, Bash
---

Validate `docs/data/briefing.json` without running the scraper.

## Checks

1. **Read** `docs/data/briefing.json`

2. **Structure check**:
   - `generated`: must be an ISO 8601 timestamp string
   - `briefing_summary`: must be a non-empty string
   - `categories`: must be an object

3. **Category check** — all 7 must exist as arrays:
   `anthropic_blog`, `ai_models`, `claude_code`, `desktop`, `office_plugins`, `chrome_extension`, `twitter`

4. **Item schema check** — for each item in every category:
   - `title`: non-empty string
   - `date`: ISO 8601 with timezone, or empty string
   - `url`: string (may be empty for curated items)
   - `summary`: string

5. **Duplicate check**: case-insensitive title comparison across all categories

6. **Date consistency**: flag items with dates in the future or older than 90 days

7. **Report**: item counts per category, total items, any issues found
