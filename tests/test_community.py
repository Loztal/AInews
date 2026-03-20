"""Tests for scraper.sources.community — HackerNews and Reddit."""

import requests as req_lib
import responses

from scraper.sources.community import fetch, _fetch_hackernews, _fetch_reddit, HN_API_URL, REDDIT_URL, FALLBACK_ITEMS


class TestFetchHackerNews:
    @responses.activate
    def test_parses_hn_response(self):
        hn_data = {
            "hits": [
                {
                    "title": "Claude Code is amazing",
                    "url": "https://example.com/claude-code",
                    "objectID": "12345",
                    "points": 150,
                    "num_comments": 42,
                    "created_at": "2026-03-19T10:00:00.000Z",
                },
                {
                    "title": "Unrelated post about Python",
                    "url": "https://example.com/python",
                    "objectID": "12346",
                    "points": 50,
                    "num_comments": 10,
                    "created_at": "2026-03-19T09:00:00.000Z",
                },
            ]
        }
        responses.add(responses.GET, HN_API_URL, json=hn_data, status=200)
        items = _fetch_hackernews()
        # Only "Claude Code is amazing" matches the filter
        assert len(items) == 1
        assert items[0]["title"] == "Claude Code is amazing"
        assert items[0]["source"] == "community"
        assert "150 points" in items[0]["summary"]

    @responses.activate
    def test_network_error_returns_empty(self):
        responses.add(responses.GET, HN_API_URL, body=req_lib.ConnectionError("fail"))
        items = _fetch_hackernews()
        assert items == []


class TestFetchReddit:
    @responses.activate
    def test_parses_reddit_response(self):
        reddit_data = {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "Best Claude Code workflows",
                            "score": 200,
                            "num_comments": 55,
                            "permalink": "/r/ClaudeAI/comments/abc123/best_workflows/",
                            "created_utc": 1742400000,
                            "selftext": "Share your best workflows here.",
                        }
                    }
                ]
            }
        }
        responses.add(responses.GET, REDDIT_URL, json=reddit_data, status=200)
        items = _fetch_reddit()
        assert len(items) == 1
        assert items[0]["title"] == "Best Claude Code workflows"
        assert items[0]["source"] == "community"
        assert "200 upvotes" in items[0]["summary"]

    @responses.activate
    def test_network_error_returns_empty(self):
        responses.add(responses.GET, REDDIT_URL, body=req_lib.ConnectionError("fail"))
        items = _fetch_reddit()
        assert items == []


class TestFetch:
    @responses.activate
    def test_returns_fallback_when_both_fail(self):
        responses.add(responses.GET, HN_API_URL, body=req_lib.ConnectionError("fail"))
        responses.add(responses.GET, REDDIT_URL, body=req_lib.ConnectionError("fail"))
        items = fetch()
        assert len(items) == len(FALLBACK_ITEMS)

    @responses.activate
    def test_deduplicates_by_url(self):
        hn_data = {
            "hits": [
                {
                    "title": "Claude announcement",
                    "url": "https://example.com/same",
                    "objectID": "111",
                    "points": 100,
                    "num_comments": 20,
                    "created_at": "2026-03-19T10:00:00.000Z",
                }
            ]
        }
        reddit_data = {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "Claude announcement on Reddit",
                            "score": 50,
                            "num_comments": 10,
                            "permalink": "/r/ClaudeAI/comments/abc/claude/",
                            "created_utc": 1742400000,
                            "selftext": "",
                        }
                    }
                ]
            }
        }
        responses.add(responses.GET, HN_API_URL, json=hn_data, status=200)
        responses.add(responses.GET, REDDIT_URL, json=reddit_data, status=200)
        items = fetch()
        urls = [i["url"] for i in items]
        assert len(urls) == len(set(urls)), "Duplicate URLs found"

    @responses.activate
    def test_item_schema(self):
        responses.add(responses.GET, HN_API_URL, body=req_lib.ConnectionError("fail"))
        responses.add(responses.GET, REDDIT_URL, body=req_lib.ConnectionError("fail"))
        items = fetch()
        for item in items:
            assert "title" in item
            assert "date" in item
            assert "url" in item
            assert "summary" in item
            assert "source" in item
            assert item["source"] == "community"
