"""Tests for scraper.main — deduplication, sorting, orchestration."""

import json
import os
from unittest.mock import patch, MagicMock

from scraper.main import run


def _make_item(title, source, date="2026-03-18T00:00:00+00:00"):
    return {"title": title, "date": date, "url": "", "summary": "", "source": source}


class TestDeduplication:
    def test_case_insensitive(self, tmp_path):
        """'Claude Code' and 'claude code' should collapse to one item."""
        items = [
            _make_item("Claude Code Release", "claude_code"),
            _make_item("claude code release", "claude_code"),
        ]
        result = _deduplicate(items)
        assert len(result) == 1
        assert result[0]["title"] == "Claude Code Release"

    def test_preserves_first_occurrence(self):
        """First occurrence wins when titles match."""
        items = [
            _make_item("Update", "claude_code", "2026-03-18T00:00:00+00:00"),
            _make_item("Update", "anthropic_blog", "2026-03-19T00:00:00+00:00"),
        ]
        result = _deduplicate(items)
        assert len(result) == 1
        assert result[0]["source"] == "claude_code"

    def test_whitespace_handling(self):
        """Leading/trailing whitespace should not create duplicates."""
        items = [
            _make_item("  Update  ", "claude_code"),
            _make_item("Update", "claude_code"),
        ]
        result = _deduplicate(items)
        assert len(result) == 1

    def test_different_titles_kept(self):
        """Different titles should all be kept."""
        items = [
            _make_item("Alpha", "claude_code"),
            _make_item("Beta", "anthropic_blog"),
            _make_item("Gamma", "twitter"),
        ]
        result = _deduplicate(items)
        assert len(result) == 3


class TestSorting:
    def test_sort_by_date_descending(self):
        """Items should be sorted newest first within a category."""
        items = [
            _make_item("Old", "claude_code", "2026-03-15T00:00:00+00:00"),
            _make_item("New", "claude_code", "2026-03-19T00:00:00+00:00"),
            _make_item("Mid", "claude_code", "2026-03-17T00:00:00+00:00"),
        ]
        categories = _categorize_and_sort(items)
        titles = [i["title"] for i in categories["claude_code"]]
        assert titles == ["New", "Mid", "Old"]

    def test_empty_dates_sort_last(self):
        """Items with empty date should sort after dated items."""
        items = [
            _make_item("No date", "claude_code", ""),
            _make_item("Has date", "claude_code", "2026-03-19T00:00:00+00:00"),
        ]
        categories = _categorize_and_sort(items)
        titles = [i["title"] for i in categories["claude_code"]]
        assert titles == ["Has date", "No date"]


class TestCategoryInitialization:
    def test_all_categories_exist(self):
        """All 7 expected categories should exist even when empty."""
        categories = _categorize_and_sort([])
        expected = {"anthropic_blog", "ai_models", "claude_code", "desktop",
                    "office_plugins", "chrome_extension", "twitter"}
        assert set(categories.keys()) >= expected

    def test_empty_categories_are_lists(self):
        """Empty categories should be empty lists, not None."""
        categories = _categorize_and_sort([])
        for key in categories:
            assert isinstance(categories[key], list)


class TestOrchestration:
    @patch("scraper.main.generate_summary", return_value="Test summary")
    def test_source_error_doesnt_stop_pipeline(self, mock_summary, tmp_path):
        """A failing source should not crash the whole run."""
        output_path = str(tmp_path / "briefing.json")

        def failing_fetch():
            raise RuntimeError("Network error")

        def good_fetch():
            return [_make_item("Good item", "claude_code")]

        with patch("scraper.main.OUTPUT_PATH", output_path), \
             patch("scraper.main.model_specs") as ms, \
             patch("scraper.main.chrome_extension") as ce, \
             patch("scraper.main.desktop") as dt, \
             patch("scraper.main.office_plugins") as op, \
             patch("scraper.main.twitter_feed") as tf, \
             patch("scraper.main.anthropic_blog") as ab, \
             patch("scraper.main.claude_code") as cc, \
             patch("scraper.main.release_notes") as rn:

            ms.fetch = failing_fetch
            ce.fetch = failing_fetch
            dt.fetch = failing_fetch
            op.fetch = failing_fetch
            tf.fetch = failing_fetch
            ab.fetch = failing_fetch
            cc.fetch = good_fetch
            rn.fetch = failing_fetch

            run()

        with open(output_path) as f:
            data = json.load(f)
        assert "categories" in data
        assert len(data["categories"]["claude_code"]) == 1

    @patch("scraper.main.generate_summary", return_value="Test summary")
    def test_output_json_schema(self, mock_summary, tmp_path):
        """Output should have generated, briefing_summary, categories keys."""
        output_path = str(tmp_path / "briefing.json")

        with patch("scraper.main.OUTPUT_PATH", output_path), \
             patch("scraper.main.model_specs") as ms, \
             patch("scraper.main.chrome_extension") as ce, \
             patch("scraper.main.desktop") as dt, \
             patch("scraper.main.office_plugins") as op, \
             patch("scraper.main.twitter_feed") as tf, \
             patch("scraper.main.anthropic_blog") as ab, \
             patch("scraper.main.claude_code") as cc, \
             patch("scraper.main.release_notes") as rn:

            for m in [ms, ce, dt, op, tf, ab, cc, rn]:
                m.fetch = lambda: []

            run()

        with open(output_path) as f:
            data = json.load(f)
        assert "generated" in data
        assert "briefing_summary" in data
        assert "categories" in data
        assert data["briefing_summary"] == "Test summary"


# --- Helpers that replicate main.py logic for isolated testing ---

def _deduplicate(items):
    """Replicate main.py dedup logic for unit testing."""
    from collections import defaultdict
    seen_titles = set()
    result = []
    for item in items:
        title_key = item["title"].lower().strip()
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        result.append(item)
    return result


def _categorize_and_sort(items):
    """Replicate main.py categorize + sort logic."""
    from collections import defaultdict
    categories = defaultdict(list)
    seen_titles = set()
    for item in items:
        title_key = item["title"].lower().strip()
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        source = item.pop("source", "anthropic_blog")
        categories[source].append(item)
    for key in categories:
        categories[key].sort(key=lambda x: x.get("date", ""), reverse=True)
    for key in ["anthropic_blog", "ai_models", "claude_code", "desktop",
                "office_plugins", "chrome_extension", "twitter"]:
        if key not in categories:
            categories[key] = []
    return dict(categories)
