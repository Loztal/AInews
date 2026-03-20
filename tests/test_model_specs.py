"""Tests for scraper.sources.model_specs — API parsing + fallback."""

import os
from unittest.mock import patch

import responses

from scraper.sources.model_specs import fetch, _format_tokens, _fetch_from_api, API_URL, FALLBACK_SPECS


class TestFormatTokens:
    def test_millions(self):
        assert _format_tokens(1_000_000) == "1M tokens"

    def test_millions_fractional(self):
        assert _format_tokens(1_500_000) == "1.5M tokens"

    def test_thousands(self):
        assert _format_tokens(200_000) == "200K tokens"

    def test_thousands_exact(self):
        assert _format_tokens(64_000) == "64K tokens"

    def test_small_number(self):
        assert _format_tokens(500) == "500 tokens"

    def test_zero(self):
        assert _format_tokens(0) == "0 tokens"


class TestFetchFromApi:
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""})
    def test_no_api_key_returns_none(self):
        result = _fetch_from_api()
        assert result is None

    @responses.activate
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    def test_success(self):
        responses.add(responses.GET, API_URL, json={
            "data": [
                {"id": "claude-opus-4-6-20260301", "max_input_tokens": 1_000_000, "max_tokens": 128_000},
                {"id": "claude-sonnet-4-6-20260301", "max_input_tokens": 1_000_000, "max_tokens": 64_000},
                {"id": "claude-haiku-4-5-20251001", "max_input_tokens": 200_000, "max_tokens": 64_000},
            ]
        }, status=200)
        result = _fetch_from_api()
        assert result is not None
        assert len(result) == 3
        assert result[0]["name"] == "Claude Opus 4.6"
        assert result[0]["context_window"] == "1M tokens"

    @responses.activate
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    def test_partial_response_returns_none(self):
        """If not all 3 target models found, return None (fallback)."""
        responses.add(responses.GET, API_URL, json={
            "data": [
                {"id": "claude-opus-4-6-20260301", "max_input_tokens": 1_000_000, "max_tokens": 128_000},
            ]
        }, status=200)
        result = _fetch_from_api()
        assert result is None

    @responses.activate
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    def test_api_error_returns_none(self):
        responses.add(responses.GET, API_URL, status=500)
        result = _fetch_from_api()
        assert result is None


class TestFetch:
    @patch("scraper.sources.model_specs._fetch_from_api", return_value=None)
    def test_uses_fallback(self, mock_api):
        items = fetch()
        assert len(items) == len(FALLBACK_SPECS)
        for item in items:
            assert item["source"] == "ai_models"
            assert "tiers" in item
            assert "model_id" in item

    @patch("scraper.sources.model_specs._fetch_from_api")
    def test_api_success_items(self, mock_api):
        mock_api.return_value = [
            {"name": "Claude Opus 4.6", "model_id": "claude-opus-4-6",
             "context_window": "1M tokens", "max_output": "128K tokens",
             "pricing_input": "$5/MTok", "pricing_output": "$25/MTok"},
        ]
        items = fetch()
        assert len(items) == 1
        assert items[0]["title"] == "Claude Opus 4.6"
        assert items[0]["tiers"]  # Should have tier data
