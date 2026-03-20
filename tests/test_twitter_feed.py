"""Tests for scraper.sources.twitter_feed — reply filtering + fallback."""

import requests as req_lib
import responses

from scraper.sources.twitter_feed import fetch, _fetch_from_rss, RSSHUB_URL, FALLBACK_TWEETS


SAMPLE_TWITTER_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>bcherny's tweets</title>
    <item>
      <title>New in Claude Code: Code Review</title>
      <link>https://x.com/bcherny/status/123</link>
      <pubDate>Sun, 09 Mar 2026 00:00:00 GMT</pubDate>
      <description>Code review is amazing</description>
    </item>
    <item>
      <title>@someone this is a reply</title>
      <link>https://x.com/bcherny/status/456</link>
      <pubDate>Sat, 08 Mar 2026 00:00:00 GMT</pubDate>
      <description>@someone reply text</description>
    </item>
    <item>
      <title>Claude Code is 100% self-written</title>
      <link>https://x.com/bcherny/status/789</link>
      <pubDate>Fri, 07 Mar 2026 00:00:00 GMT</pubDate>
      <description>Can confirm it's all Claude</description>
    </item>
  </channel>
</rss>
"""


class TestFetchFromRss:
    @responses.activate
    def test_filters_replies(self):
        responses.add(responses.GET, RSSHUB_URL, body=SAMPLE_TWITTER_RSS, status=200)
        items = _fetch_from_rss()
        titles = [i["title"] for i in items]
        assert "@someone this is a reply" not in titles
        assert "New in Claude Code: Code Review" in titles

    @responses.activate
    def test_returns_correct_schema(self):
        responses.add(responses.GET, RSSHUB_URL, body=SAMPLE_TWITTER_RSS, status=200)
        items = _fetch_from_rss()
        for item in items:
            assert "title" in item
            assert "date" in item
            assert "url" in item
            assert "summary" in item
            assert item["source"] == "twitter"

    @responses.activate
    def test_network_error_returns_empty(self):
        responses.add(responses.GET, RSSHUB_URL, body=req_lib.ConnectionError("fail"))
        items = _fetch_from_rss()
        assert items == []


class TestFetch:
    @responses.activate
    def test_uses_fallback_on_failure(self):
        responses.add(responses.GET, RSSHUB_URL, body=req_lib.ConnectionError("fail"))
        items = fetch()
        assert len(items) == len(FALLBACK_TWEETS)

    @responses.activate
    def test_dedup_by_title(self):
        """Duplicate titles should be collapsed."""
        rss_with_dup = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0"><channel>
          <item>
            <title>Same Title</title>
            <link>https://x.com/1</link>
            <pubDate>Sun, 09 Mar 2026 00:00:00 GMT</pubDate>
            <description>First</description>
          </item>
          <item>
            <title>Same Title</title>
            <link>https://x.com/2</link>
            <pubDate>Sat, 08 Mar 2026 00:00:00 GMT</pubDate>
            <description>Second</description>
          </item>
        </channel></rss>"""
        responses.add(responses.GET, RSSHUB_URL, body=rss_with_dup, status=200)
        items = fetch()
        titles = [i["title"] for i in items]
        assert titles.count("Same Title") == 1

    def test_fallback_dates_have_timezone(self):
        """All fallback dates should include timezone offset."""
        for tweet in FALLBACK_TWEETS:
            assert "+00:00" in tweet["date"], f"Missing TZ in: {tweet['title']}"

    @responses.activate
    def test_title_truncated_at_120(self):
        long_title = "x" * 200
        rss = f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0"><channel>
          <item>
            <title>{long_title}</title>
            <link>https://x.com/1</link>
            <pubDate>Sun, 09 Mar 2026 00:00:00 GMT</pubDate>
            <description>Desc</description>
          </item>
        </channel></rss>"""
        responses.add(responses.GET, RSSHUB_URL, body=rss, status=200)
        items = _fetch_from_rss()
        assert len(items[0]["title"]) <= 120
