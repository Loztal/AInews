"""Tests for scraper.sources.office_plugins — RSS + curated milestones."""

import requests as req_lib
import responses

from scraper.sources.office_plugins import fetch, _fetch_from_rss, ANTHROPIC_NEWS_RSS, CURATED_ITEMS


class TestFetchFromRss:
    @responses.activate
    def test_filters_by_keywords(self, rss_xml):
        responses.add(responses.GET, ANTHROPIC_NEWS_RSS, body=rss_xml, status=200)
        items = _fetch_from_rss()
        for item in items:
            assert item["source"] == "office_plugins"
        # Only the office-related item should match
        titles = [i["title"] for i in items]
        assert "Claude for Excel add-in improvements" in titles
        assert "Claude Opus 4.6 sets new benchmarks" not in titles

    @responses.activate
    def test_network_error_returns_empty(self):
        responses.add(responses.GET, ANTHROPIC_NEWS_RSS, body=req_lib.ConnectionError("fail"))
        items = _fetch_from_rss()
        assert items == []

    @responses.activate
    def test_empty_feed(self, empty_rss):
        responses.add(responses.GET, ANTHROPIC_NEWS_RSS, body=empty_rss, status=200)
        items = _fetch_from_rss()
        assert items == []


class TestFetch:
    @responses.activate
    def test_includes_curated(self):
        responses.add(responses.GET, ANTHROPIC_NEWS_RSS, body=req_lib.ConnectionError("fail"))
        items = fetch()
        # Should still have curated items even when RSS fails
        assert len(items) >= len(CURATED_ITEMS)
        curated_titles = {i["title"] for i in CURATED_ITEMS}
        fetched_titles = {i["title"] for i in items}
        assert curated_titles.issubset(fetched_titles)

    @responses.activate
    def test_dedup_rss_and_curated(self, rss_xml):
        responses.add(responses.GET, ANTHROPIC_NEWS_RSS, body=rss_xml, status=200)
        items = fetch()
        titles = [i["title"].lower().strip() for i in items]
        assert len(titles) == len(set(titles)), "Duplicate titles found"

    @responses.activate
    def test_item_schema(self):
        responses.add(responses.GET, ANTHROPIC_NEWS_RSS, body=req_lib.ConnectionError("fail"))
        items = fetch()
        for item in items:
            assert "title" in item
            assert "date" in item
            assert "url" in item
            assert "summary" in item
            assert "source" in item
            assert item["source"] == "office_plugins"
