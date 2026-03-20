"""Generate an Atom feed from the briefing data."""

import os
from xml.etree.ElementTree import Element, SubElement, ElementTree


ATOM_NS = "http://www.w3.org/2005/Atom"


def generate_feed(briefing_data, output_path):
    """Generate an Atom feed XML file from briefing data.

    Args:
        briefing_data: dict with 'generated', 'briefing_summary', 'categories'.
        output_path: path to write feed.xml.
    """
    feed = Element("feed", xmlns=ATOM_NS)

    SubElement(feed, "title").text = "Claude Daily Briefing"
    SubElement(feed, "subtitle").text = briefing_data.get("briefing_summary", "")
    SubElement(feed, "updated").text = briefing_data.get("generated", "")
    SubElement(feed, "id").text = "urn:claude-daily-briefing"

    author = SubElement(feed, "author")
    SubElement(author, "name").text = "AInews Scraper"

    link = SubElement(feed, "link")
    link.set("rel", "self")
    link.set("href", "feed.xml")

    # Collect all items across categories, sorted by date descending
    all_items = []
    categories = briefing_data.get("categories", {})
    for category_key, items in categories.items():
        for item in items:
            all_items.append((category_key, item))

    all_items.sort(key=lambda x: x[1].get("date", ""), reverse=True)

    for category_key, item in all_items[:50]:
        entry = SubElement(feed, "entry")
        SubElement(entry, "title").text = item.get("title", "")

        entry_link = SubElement(entry, "link")
        entry_link.set("href", item.get("url", ""))

        item_id = item.get("url", "") or item.get("title", "")
        SubElement(entry, "id").text = item_id

        date = item.get("date", "")
        if date:
            SubElement(entry, "updated").text = date

        SubElement(entry, "summary").text = item.get("summary", "")

        cat = SubElement(entry, "category")
        cat.set("term", category_key)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tree = ElementTree(feed)
    tree.write(output_path, xml_declaration=True, encoding="unicode")
