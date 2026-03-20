"""Shared fixtures for scraper tests."""

import os
import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def rss_xml():
    with open(os.path.join(FIXTURES_DIR, "rss_feed.xml")) as f:
        return f.read()


@pytest.fixture
def atom_xml():
    with open(os.path.join(FIXTURES_DIR, "atom_feed.xml")) as f:
        return f.read()


@pytest.fixture
def release_html():
    with open(os.path.join(FIXTURES_DIR, "release_notes.html")) as f:
        return f.read()


@pytest.fixture
def empty_rss():
    with open(os.path.join(FIXTURES_DIR, "empty_feed.xml")) as f:
        return f.read()
