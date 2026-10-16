"""Parser for the City of San Mateo's publisher-designated Open Law XML bulk data.

The San Mateo Law Library expressly tells users not to scrape its web pages and
instead links to this public XML repository.  A production caller should pin a
Git commit, download the XML tree once, and pass each local XML file to
``parse_title_xml``.  This module never crawls the Law Library website.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


BULK_REPOSITORY = "https://github.com/cityofsanmateo/law-xml"
BULK_PATH = "us/ca/cities/san-mateo/code"
PINNED_COMMIT = "08a2b2cbbc80f7ca584bca130c422327448d672f"


def _name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _clean(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return re.sub(r"\s+", " ", "".join(element.itertext())).strip()


def _child(element: ET.Element, tag: str) -> ET.Element | None:
    return next((item for item in element if _name(item) == tag), None)


def _label(element: ET.Element) -> str:
    return " ".join(part for part in (_clean(_child(element, "prefix")), _clean(_child(element, "num")), _clean(_child(element, "heading"))) if part)


def parse_title_xml(xml_text: str, source_url: str = "") -> list[dict[str, str]]:
    """Return leaf sections with title/chapter metadata from one bulk XML file."""
    root = ET.fromstring(xml_text)
    rows: list[dict[str, str]] = []

    def visit(node: ET.Element, trail: list[str]) -> None:
        node_name = _name(node)
        if node_name == "section":
            number = _clean(_child(node, "num"))
            heading = _clean(_child(node, "heading"))
            text = _clean(_child(node, "text"))
            title = next((x for x in trail if x.lower().startswith("title ")), "")
            chapter = next((x for x in reversed(trail) if x.lower().startswith("chapter ")), "")
            rows.append({"title": title, "chapter": chapter, "section_number": number,
                         "section_name": heading, "full_text": text, "source_url": source_url})
            return
        next_trail = trail + ([_label(node)] if node_name == "container" and _label(node) else [])
        for child in node:
            if _name(child) in {"container", "section"}:
                visit(child, next_trail)

    visit(root, [])
    return rows


def validate(root_url: str) -> dict[str, Any]:
    """Return the approved bulk-source plan; parsing is verified from local XML."""
    return {
        "status": "bulk-download-required",
        "root_url": root_url,
        "toc_url": f"{BULK_REPOSITORY}/tree/{PINNED_COMMIT}/{BULK_PATH}",
        "section_url": f"https://raw.githubusercontent.com/cityofsanmateo/law-xml/{PINNED_COMMIT}/{BULK_PATH}/1.xml",
        "toc_count_or_sample": 29,
        "section_text_length": 0,
        "checks": ["Publisher directs users to bulk HTML/XML rather than page scraping.",
                   f"Pinned repository commit: {PINNED_COMMIT}"],
        "errors": ["Download the repository at the pinned commit before production parsing."],
    }


def fixture_test() -> dict[str, Any]:
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "san-mateo-title-1.xml"
    rows = parse_title_xml(fixture.read_text(encoding="utf-8"), "fixture://san-mateo/1.xml")
    assert len(rows) == 2
    assert rows[0]["title"] == "Title 1 GENERAL PROVISIONS"
    assert rows[0]["chapter"] == "Chapter 1.01 CODE ADOPTION"
    assert rows[0]["section_number"] == "1.01.010"
    assert "San Mateo Municipal Code" in rows[0]["full_text"]
    return {"fixture": str(fixture), "sections": len(rows), "passed": True}
