"""Tests for scraper.sources.claude_code — Atom parsing + highlight extraction."""

import requests as req_lib
import responses

from scraper.sources.claude_code import fetch, _extract_highlights, FEED_URL, FALLBACK_RELEASES


class TestExtractHighlights:
    def test_extracts_added_fixed(self):
        html = "<ul><li>Added code review</li><li>Fixed terminal bug</li></ul>"
        result = _extract_highlights(html)
        assert "Added code review" in result
        assert "Fixed terminal bug" in result

    def test_joins_with_period(self):
        html = "<li>Added feature A</li><li>Fixed bug B</li>"
        result = _extract_highlights(html)
        assert ". " in result

    def test_deduplicates(self):
        html = "<li>Added feature</li><li>Added feature</li><li>Fixed bug</li>"
        result = _extract_highlights(html)
        assert result.count("Added feature") == 1

    def test_skips_short_lines(self):
        html = "<p>OK</p><p>X</p><p>Added real feature here</p>"
        result = _extract_highlights(html)
        assert "Added real feature here" in result

    def test_fallback_to_first_lines(self):
        """When no recognized prefixes, use first 3 lines."""
        html = "<p>Release notes for v2.1.80</p><p>This version includes many changes</p>"
        result = _extract_highlights(html)
        assert "Release notes" in result

    def test_truncates_at_300(self):
        bullets = "".join(f"<li>Added feature number {i} with a long description here</li>" for i in range(50))
        result = _extract_highlights(f"<ul>{bullets}</ul>")
        assert len(result) <= 300

    def test_empty_html(self):
        result = _extract_highlights("")
        assert result == ""

    def test_bullet_markers(self):
        html = "- Added dash feature\n* Added star feature\n• Added bullet feature"
        result = _extract_highlights(html)
        assert "Added dash feature" in result


class TestFetch:
    @responses.activate
    def test_success(self, atom_xml):
        responses.add(responses.GET, FEED_URL, body=atom_xml, status=200)
        items = fetch()
        assert len(items) == 1
        assert items[0]["title"] == "v2.1.80"
        assert items[0]["source"] == "claude_code"
        assert items[0]["url"] == "https://github.com/anthropics/claude-code/releases/tag/v2.1.80"
        assert "Added new code review feature" in items[0]["summary"]

    @responses.activate
    def test_network_error_uses_fallback(self):
        responses.add(responses.GET, FEED_URL, body=req_lib.ConnectionError("timeout"))
        items = fetch()
        assert len(items) == len(FALLBACK_RELEASES)
        assert items[0]["title"] == FALLBACK_RELEASES[0]["title"]

    @responses.activate
    def test_http_500_uses_fallback(self):
        responses.add(responses.GET, FEED_URL, status=500)
        items = fetch()
        assert len(items) == len(FALLBACK_RELEASES)
