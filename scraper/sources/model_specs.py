"""Fetch Claude model specs from Anthropic's API or use curated fallback."""

import os
import requests


DOCS_URL = "https://platform.claude.com/docs/en/about-claude/models/overview"
API_URL = "https://api.anthropic.com/v1/models"

# Tier availability — not available as structured API data.
TIER_CONFIG = {
    "Claude Opus 4.6": {
        "Free": "-", "Pro": "1M", "Max 5x": "1M", "Max 20x": "1M",
        "Team Std": "1M", "Team Prem": "1M", "Enterprise": "Custom", "API": "1M",
    },
    "Claude Sonnet 4.6": {
        "Free": "-", "Pro": "1M", "Max 5x": "1M", "Max 20x": "1M",
        "Team Std": "1M", "Team Prem": "1M", "Enterprise": "Custom", "API": "1M",
    },
    "Claude Haiku 4.5": {
        "Free": "-", "Pro": "200K", "Max 5x": "200K", "Max 20x": "200K",
        "Team Std": "200K", "Team Prem": "200K", "Enterprise": "Custom", "API": "200K",
    },
}

# Target model IDs and their display names / known pricing.
TARGET_MODELS = {
    "claude-opus-4-6": {
        "name": "Claude Opus 4.6",
        "pricing_input": "$5/MTok",
        "pricing_output": "$25/MTok",
    },
    "claude-sonnet-4-6": {
        "name": "Claude Sonnet 4.6",
        "pricing_input": "$3/MTok",
        "pricing_output": "$15/MTok",
    },
    "claude-haiku-4-5": {
        "name": "Claude Haiku 4.5",
        "pricing_input": "$1/MTok",
        "pricing_output": "$5/MTok",
    },
}

# Hardcoded fallback (sourced from platform.claude.com/docs, March 2026).
FALLBACK_SPECS = [
    {
        "name": "Claude Opus 4.6",
        "model_id": "claude-opus-4-6",
        "context_window": "1M tokens",
        "max_output": "128K tokens",
        "pricing_input": "$5/MTok",
        "pricing_output": "$25/MTok",
    },
    {
        "name": "Claude Sonnet 4.6",
        "model_id": "claude-sonnet-4-6",
        "context_window": "1M tokens",
        "max_output": "64K tokens",
        "pricing_input": "$3/MTok",
        "pricing_output": "$15/MTok",
    },
    {
        "name": "Claude Haiku 4.5",
        "model_id": "claude-haiku-4-5",
        "context_window": "200K tokens",
        "max_output": "64K tokens",
        "pricing_input": "$1/MTok",
        "pricing_output": "$5/MTok",
    },
]


def fetch():
    """Return list of model spec items for current Claude models."""
    specs = _fetch_from_api()
    if not specs:
        print("    Using fallback model specs")
        specs = FALLBACK_SPECS

    items = []
    for spec in specs:
        name = spec["name"]
        tiers = TIER_CONFIG.get(name, {})
        items.append({
            "title": name,
            "date": "",
            "url": DOCS_URL,
            "summary": "",
            "source": "ai_models",
            "model_id": spec.get("model_id", ""),
            "context_window": spec.get("context_window", ""),
            "max_output": spec.get("max_output", ""),
            "pricing_input": spec.get("pricing_input", ""),
            "pricing_output": spec.get("pricing_output", ""),
            "tiers": tiers,
        })
    return items


def _fetch_from_api():
    """Try to get model specs from the Anthropic API."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None

    try:
        resp = requests.get(API_URL, timeout=15, headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        })
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"    Warning: Could not fetch models API: {e}")
        return None

    models = data.get("data", [])
    specs = []

    for model_id, meta in TARGET_MODELS.items():
        # Find matching model in API response (match by prefix)
        match = None
        for m in models:
            if m.get("id", "").startswith(model_id):
                match = m
                break

        if not match:
            continue

        max_input = match.get("max_input_tokens", 0)
        max_output = match.get("max_tokens", 0)

        specs.append({
            "name": meta["name"],
            "model_id": match.get("id", model_id),
            "context_window": _format_tokens(max_input),
            "max_output": _format_tokens(max_output),
            "pricing_input": meta["pricing_input"],
            "pricing_output": meta["pricing_output"],
        })

    return specs if len(specs) == len(TARGET_MODELS) else None


def _format_tokens(n):
    """Format token count like '1M tokens' or '200K tokens'."""
    if n >= 1_000_000:
        val = n / 1_000_000
        return f"{val:g}M tokens"
    if n >= 1_000:
        val = n / 1_000
        return f"{val:g}K tokens"
    return f"{n} tokens"
