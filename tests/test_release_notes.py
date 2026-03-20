"""Tests for scraper.sources.release_notes — HTML scraping + categorization."""

import requests as req_lib
import responses

from scraper.sources.release_notes import fetch, _categorize, RELEASE_NOTES_URL


class TestCategorize:
    def test_desktop_keyword(self):
        assert _categorize("Claude Desktop app update", "March 2026") == "desktop"

    def test_chrome_keyword(self):
        assert _categorize("New chrome extension feature", "Updates") == "chrome_extension"

    def test_model_keyword(self):
        assert _categorize("Claude Opus 4.6 with expanded context window", "Models") == "ai_models"

    def test_office_keyword(self):
        assert _categorize("Claude for Excel add-in improvements", "Plugins") == "office_plugins"

    def test_no_match(self):
        assert _categorize("General company news", "Updates") is None

    def test_section_context_helps(self):
        """Section title should also contribute to categorization."""
        assert _categorize("New features added", "Desktop App Updates") == "desktop"

    def test_cowork_maps_to_desktop(self):
        assert _categorize("Cowork mode now available", "Features") == "desktop"


class TestFetch:
    @responses.activate
    def test_parses_html(self, release_html):
        responses.add(responses.GET, RELEASE_NOTES_URL, body=release_html, status=200)
        items = fetch()
        assert len(items) > 0
        for item in items:
            assert "title" in item
            assert "date" in item
            assert "source" in item

    @responses.activate
    def test_extracts_dates(self, release_html):
        responses.add(responses.GET, RELEASE_NOTES_URL, body=release_html, status=200)
        items = fetch()
        dated = [i for i in items if i["date"]]
        assert len(dated) > 0
        assert "2026-03-11" in dated[0]["date"]

    @responses.activate
    def test_network_error_returns_empty(self):
        responses.add(responses.GET, RELEASE_NOTES_URL, status=500)
        items = fetch()
        assert items == []

    @responses.activate
    def test_connection_error_returns_empty(self):
        responses.add(responses.GET, RELEASE_NOTES_URL, body=req_lib.ConnectionError("fail"))
        items = fetch()
        assert items == []

    @responses.activate
    def test_short_text_filtered(self, release_html):
        """Text under 20 characters should be skipped."""
        responses.add(responses.GET, RELEASE_NOTES_URL, body=release_html, status=200)
        items = fetch()
        for item in items:
            # Title comes from text[:120], but original text was >20 chars
            assert len(item["title"]) > 10

    @responses.activate
    def test_limits_to_30(self):
        """Should return at most 30 items."""
        # Build a large HTML with many items
        paragraphs = "".join(
            f"<p>Claude Desktop update number {i} with many improvements and features</p>"
            for i in range(50)
        )
        big_html = f"<article><h2>March 11, 2026</h2>{paragraphs}</article>"
        responses.add(responses.GET, RELEASE_NOTES_URL, body=big_html, status=200)
        items = fetch()
        assert len(items) <= 30
