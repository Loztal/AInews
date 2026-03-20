"""Tests for scraper.sources.web_sources — RSS keyword categorization."""

import requests as req_lib
import responses

from scraper.sources.web_sources import fetch, _clean, ANTHROPIC_NEWS_RSS


class TestClean:
    def test_strips_html(self):
        assert _clean("<p>hello</p>") == "hello"

    def test_truncates(self):
        result = _clean("a" * 500)
        assert len(result) <= 303

    def test_empty(self):
        assert _clean("") == ""


class TestFetch:
    @responses.activate
    def test_categorizes_model_items(self, rss_xml):
        responses.add(responses.GET, ANTHROPIC_NEWS_RSS, body=rss_xml, status=200)
        items = fetch()
        model_items = [i for i in items if i["source"] == "ai_models"]
        assert any("Opus" in i["title"] for i in model_items)

    @responses.activate
    def test_categorizes_chrome_items(self, rss_xml):
        responses.add(responses.GET, ANTHROPIC_NEWS_RSS, body=rss_xml, status=200)
        items = fetch()
        chrome_items = [i for i in items if i["source"] == "chrome_extension"]
        assert any("Chrome" in i["title"] for i in chrome_items)

    @responses.activate
    def test_categorizes_office_items(self, rss_xml):
        responses.add(responses.GET, ANTHROPIC_NEWS_RSS, body=rss_xml, status=200)
        items = fetch()
        office_items = [i for i in items if i["source"] == "office_plugins"]
        assert any("Excel" in i["title"] for i in office_items)

    @responses.activate
    def test_uncategorized_items_excluded(self, rss_xml):
        responses.add(responses.GET, ANTHROPIC_NEWS_RSS, body=rss_xml, status=200)
        items = fetch()
        # "university partnerships" doesn't match any keyword
        titles = [i["title"] for i in items]
        assert "Anthropic partners with university research labs" not in titles

    @responses.activate
    def test_network_error_returns_empty(self):
        responses.add(responses.GET, ANTHROPIC_NEWS_RSS, body=req_lib.ConnectionError("fail"))
        items = fetch()
        assert items == []

    @responses.activate
    def test_empty_feed(self, empty_rss):
        responses.add(responses.GET, ANTHROPIC_NEWS_RSS, body=empty_rss, status=200)
        items = fetch()
        assert items == []
