"""Tests for scraper.feed_generator — Atom feed generation."""

import os
import xml.etree.ElementTree as ET

from scraper.feed_generator import generate_feed


class TestGenerateFeed:
    def test_creates_valid_atom(self, tmp_path):
        data = {
            "generated": "2026-03-20T12:00:00+00:00",
            "briefing_summary": "Test summary",
            "categories": {
                "claude_code": [
                    {"title": "v2.1.80", "date": "2026-03-19T00:00:00+00:00",
                     "url": "https://example.com/1", "summary": "Release notes"},
                ],
                "twitter": [
                    {"title": "Tweet about Claude", "date": "2026-03-18T00:00:00+00:00",
                     "url": "https://example.com/2", "summary": "A tweet"},
                ],
            },
        }
        feed_path = str(tmp_path / "feed.xml")
        generate_feed(data, feed_path)

        assert os.path.exists(feed_path)
        tree = ET.parse(feed_path)
        root = tree.getroot()
        ns = "{http://www.w3.org/2005/Atom}"
        assert root.tag == ns + "feed"
        assert root.find(ns + "title").text == "Claude Daily Briefing"

        entries = root.findall(ns + "entry")
        assert len(entries) == 2

    def test_limits_to_50_entries(self, tmp_path):
        items = [
            {"title": f"Item {i}", "date": f"2026-03-{i:02d}T00:00:00+00:00",
             "url": f"https://example.com/{i}", "summary": f"Summary {i}"}
            for i in range(1, 31)
        ]
        data = {
            "generated": "2026-03-20T12:00:00+00:00",
            "briefing_summary": "Test",
            "categories": {"claude_code": items, "twitter": items},
        }
        feed_path = str(tmp_path / "feed.xml")
        generate_feed(data, feed_path)

        tree = ET.parse(feed_path)
        ns = "{http://www.w3.org/2005/Atom}"
        entries = tree.getroot().findall(ns + "entry")
        assert len(entries) == 50

    def test_empty_categories(self, tmp_path):
        data = {
            "generated": "2026-03-20T12:00:00+00:00",
            "briefing_summary": "No updates",
            "categories": {},
        }
        feed_path = str(tmp_path / "feed.xml")
        generate_feed(data, feed_path)

        assert os.path.exists(feed_path)
        tree = ET.parse(feed_path)
        ns = "{http://www.w3.org/2005/Atom}"
        entries = tree.getroot().findall(ns + "entry")
        assert len(entries) == 0
