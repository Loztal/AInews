"""Tests for scraper.sources.sdk_releases — GitHub Atom feed for Anthropic SDK."""

import requests as req_lib
import responses

from scraper.sources.sdk_releases import fetch, FEED_URL, FALLBACK_RELEASES


class TestFetch:
    @responses.activate
    def test_parses_atom_feed(self, atom_xml):
        responses.add(responses.GET, FEED_URL, body=atom_xml, status=200)
        items = fetch()
        assert len(items) > 0
        for item in items:
            assert item["source"] == "sdk_releases"

    @responses.activate
    def test_network_error_returns_fallback(self):
        responses.add(responses.GET, FEED_URL, body=req_lib.ConnectionError("fail"))
        items = fetch()
        assert len(items) == len(FALLBACK_RELEASES)
        assert items[0]["title"] == FALLBACK_RELEASES[0]["title"]

    @responses.activate
    def test_http_error_returns_fallback(self):
        responses.add(responses.GET, FEED_URL, status=500)
        items = fetch()
        assert len(items) == len(FALLBACK_RELEASES)

    @responses.activate
    def test_item_schema(self):
        responses.add(responses.GET, FEED_URL, body=req_lib.ConnectionError("fail"))
        items = fetch()
        for item in items:
            assert "title" in item
            assert "date" in item
            assert "url" in item
            assert "summary" in item
            assert "source" in item
            assert item["source"] == "sdk_releases"


class TestEmptyFeed:
    @responses.activate
    def test_empty_feed_returns_fallback(self, empty_rss):
        # Atom feed with no entries should return fallback
        empty_atom = '<?xml version="1.0" encoding="UTF-8"?><feed xmlns="http://www.w3.org/2005/Atom"><title>Releases</title></feed>'
        responses.add(responses.GET, FEED_URL, body=empty_atom, status=200)
        items = fetch()
        assert len(items) == len(FALLBACK_RELEASES)
