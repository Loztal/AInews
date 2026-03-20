"""Generate AI-powered daily briefing summary using Claude API."""

import os
import json


SYSTEM_PROMPT = """You are a concise tech news briefing writer. Given categorized Claude ecosystem updates,
write a 3-5 sentence daily briefing summary highlighting the most important items.
Focus on what matters to a Claude power user. Be specific about versions, features, and dates.
Write in a professional but approachable tone, like a morning news anchor."""


def generate_summary(categories):
    """Generate a natural-language briefing summary from categorized items.

    Falls back to template-based summary if Claude API is unavailable.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Warning: ANTHROPIC_API_KEY not set, using template summary")
        return _template_summary(categories)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        items_text = _format_items_for_prompt(categories)
        if not items_text.strip():
            return "No new updates found across Claude ecosystem sources today."

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Here are today's Claude ecosystem updates:\n\n{items_text}\n\nWrite a concise daily briefing summary."
            }]
        )
        return message.content[0].text.strip()

    except Exception as e:
        print(f"Warning: Claude API call failed ({e}), using template summary")
        return _template_summary(categories)


def _format_items_for_prompt(categories):
    """Format categorized items into text for the AI prompt."""
    category_labels = {
        "anthropic_blog": "Anthropic Blog",
        "ai_models": "AI Models",
        "claude_code": "Claude Code",
        "desktop": "Desktop App",
        "office_plugins": "MS Office Plugins",
        "chrome_extension": "Chrome Extension",
        "twitter": "Twitter",
        "sdk_releases": "SDK Releases",
        "community": "Community",
    }
    parts = []
    for key, label in category_labels.items():
        items = categories.get(key, [])
        if items:
            parts.append(f"## {label}")
            for item in items[:5]:
                parts.append(f"- {item['title']} ({item.get('date', 'unknown date')})")
                if item.get("summary"):
                    parts.append(f"  {item['summary'][:200]}")
            parts.append("")
    return "\n".join(parts)


def _template_summary(categories):
    """Generate a simple template-based summary as fallback."""
    counts = []
    category_labels = {
        "anthropic_blog": "blog posts",
        "ai_models": "model updates",
        "claude_code": "Claude Code releases",
        "desktop": "desktop updates",
        "office_plugins": "Office plugin updates",
        "chrome_extension": "Chrome extension updates",
        "twitter": "tweets",
        "sdk_releases": "SDK releases",
        "community": "community discussions",
    }
    for key, label in category_labels.items():
        n = len(categories.get(key, []))
        if n > 0:
            counts.append(f"{n} {label}")

    if not counts:
        return "No new updates found across Claude ecosystem sources today."

    latest = None
    for items in categories.values():
        for item in items:
            if item.get("title") and (latest is None or item.get("date", "") > latest.get("date", "")):
                latest = item

    summary = f"Today's briefing: {', '.join(counts)}."
    if latest:
        summary += f" Latest: {latest['title']}."
    return summary
