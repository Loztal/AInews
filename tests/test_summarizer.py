"""Tests for scraper.summarizer — template summary + prompt formatting."""

from scraper.summarizer import _template_summary, _format_items_for_prompt


def _make_categories(**kwargs):
    """Build a categories dict with items for specified keys."""
    cats = {}
    for key, items in kwargs.items():
        cats[key] = items
    return cats


def _item(title, date="2026-03-18T00:00:00+00:00", summary=""):
    return {"title": title, "date": date, "url": "", "summary": summary}


class TestTemplateSummary:
    def test_counts_per_category(self):
        cats = _make_categories(
            anthropic_blog=[_item("A"), _item("B")],
            claude_code=[_item("C")],
        )
        result = _template_summary(cats)
        assert "2 blog posts" in result
        assert "1 Claude Code releases" in result

    def test_latest_item_included(self):
        cats = _make_categories(
            anthropic_blog=[
                _item("Old Post", "2026-03-15T00:00:00+00:00"),
                _item("New Post", "2026-03-19T00:00:00+00:00"),
            ],
        )
        result = _template_summary(cats)
        assert "New Post" in result

    def test_empty_categories(self):
        result = _template_summary({})
        assert "No new updates" in result

    def test_skips_zero_count_categories(self):
        cats = _make_categories(
            anthropic_blog=[_item("A")],
            claude_code=[],
        )
        result = _template_summary(cats)
        assert "blog posts" in result
        assert "Claude Code" not in result

    def test_all_category_labels(self):
        """Each known category maps to the right label."""
        cats = _make_categories(
            twitter=[_item("T")],
            desktop=[_item("D")],
            office_plugins=[_item("O")],
            chrome_extension=[_item("C")],
            ai_models=[_item("M")],
        )
        result = _template_summary(cats)
        assert "tweets" in result
        assert "desktop updates" in result
        assert "Office plugin updates" in result
        assert "Chrome extension updates" in result
        assert "model updates" in result


class TestFormatItemsForPrompt:
    def test_max_5_items_per_category(self):
        cats = _make_categories(
            anthropic_blog=[_item(f"Post {i}") for i in range(10)],
        )
        result = _format_items_for_prompt(cats)
        # Should have at most 5 bullet lines for the category
        lines = [l for l in result.split("\n") if l.startswith("- ")]
        assert len(lines) <= 5

    def test_truncates_summary(self):
        long_summary = "x" * 500
        cats = _make_categories(
            anthropic_blog=[_item("Post", summary=long_summary)],
        )
        result = _format_items_for_prompt(cats)
        # No single line should contain the full 500-char summary
        for line in result.split("\n"):
            if line.strip().startswith("x"):
                assert len(line.strip()) <= 200

    def test_skips_empty_categories(self):
        cats = _make_categories(
            anthropic_blog=[],
            claude_code=[_item("Release")],
        )
        result = _format_items_for_prompt(cats)
        assert "Anthropic Blog" not in result
        assert "Claude Code" in result

    def test_includes_date(self):
        cats = _make_categories(
            anthropic_blog=[_item("Post", date="2026-03-18T00:00:00+00:00")],
        )
        result = _format_items_for_prompt(cats)
        assert "2026-03-18" in result

    def test_empty_input(self):
        result = _format_items_for_prompt({})
        assert result.strip() == ""
