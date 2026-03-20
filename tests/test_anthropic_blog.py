"""Tests for scraper.sources.anthropic_blog — RSS parsing + fallback."""

import requests as req_lib
import responses

from scraper.sources.anthropic_blog import fetch, _clean, FEED_URL, FALLBACK_POSTS


class TestClean:
    def test_strips_html_tags(self):
        assert _clean("<b>bold</b> text") == "bold text"

    def test_strips_nested_tags(self):
        assert _clean("<p><a href='x'>link</a></p>") == "link"

    def test_truncates_at_300(self):
        long_text = "a" * 500
        result = _clean(long_text)
        assert len(result) <= 303  # 300 + "..."
        assert result.endswith("...")

    def test_short_text_no_ellipsis(self):
        result = _clean("short")
        assert not result.endswith("...")

    def test_empty_string(self):
        assert _clean("") == ""


class TestFetch:
    @responses.activate
    def test_parses_rss(self, rss_xml):
        responses.add(responses.GET, FEED_URL, body=rss_xml, status=200)
        items = fetch()
        assert len(items) > 0
        for item in items:
            assert "title" in item
            assert "date" in item
            assert "url" in item
            assert "summary" in item
            assert item["source"] == "anthropic_blog"

    @responses.activate
    def test_date_parsing(self, rss_xml):
        responses.add(responses.GET, FEED_URL, body=rss_xml, status=200)
        items = fetch()
        dated = [i for i in items if i["date"]]
        assert len(dated) > 0
        assert "2026-03-18" in dated[0]["date"]

    @responses.activate
    def test_network_error_uses_fallback(self):
        responses.add(responses.GET, FEED_URL, body=req_lib.ConnectionError("timeout"))
        items = fetch()
        assert len(items) == len(FALLBACK_POSTS)
        assert items[0]["title"] == FALLBACK_POSTS[0]["title"]

    @responses.activate
    def test_http_500_uses_fallback(self):
        responses.add(responses.GET, FEED_URL, status=500)
        items = fetch()
        assert len(items) == len(FALLBACK_POSTS)

    @responses.activate
    def test_empty_feed_returns_empty(self, empty_rss):
        responses.add(responses.GET, FEED_URL, body=empty_rss, status=200)
        items = fetch()
        assert items == []

    @responses.activate
    def test_html_stripped_from_summary(self, rss_xml):
        responses.add(responses.GET, FEED_URL, body=rss_xml, status=200)
        items = fetch()
        for item in items:
            assert "<" not in item["summary"]
