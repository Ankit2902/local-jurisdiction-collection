"""Baltimore City Code bulk XML adapter.

The City's Open Law Library expressly directs bulk download rather than web
scraping.  This parser consumes the official repository files after a caller
has pinned a commit and resolved XIncludes locally.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


BULK_REPOSITORY = "https://github.com/baltimore-legref/law-xml"
PINNED_COMMIT = "3ca038ebbf35efd485e8c4abd10a679b5965a2a3"
BULK_PATH = "us/md/cities/baltimore/code"


def _name(item: ET.Element) -> str:
    return item.tag.rsplit("}", 1)[-1]


def _direct_text(item: ET.Element, tag: str) -> str:
    found = next((child for child in item if _name(child) == tag), None)
    return re.sub(r"\s+", " ", "".join(found.itertext()) if found is not None else "").strip()


def _body(item: ET.Element) -> str:
    """Preserve recursively numbered paragraphs while omitting editorial annotations."""
    parts: list[str] = []
    def visit(node: ET.Element) -> None:
        name = _name(node)
        if name == "annotations":
            return
        if name in {"text", "para"}:
            number = _direct_text(node, "num") if name == "para" else ""
            heading = _direct_text(node, "heading") if name == "para" else ""
            if heading:
                parts.append((number + " " + heading).strip())
            own = (node.text or "").strip()
            if own:
                parts.append((number + " " + own).strip())
        for child in node:
            if _name(child) not in {"num", "heading", "annotations"}:
                visit(child)
            if child.tail and child.tail.strip():
                parts.append(child.tail.strip())
    visit(item)
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def parse_article_xml(xml_text: str, source_url: str = "") -> list[dict[str, str]]:
    root = ET.fromstring(xml_text)
    rows: list[dict[str, str]] = []
    def visit(node: ET.Element, trail: list[str]) -> None:
        name = _name(node)
        if name == "section":
            number, heading = _direct_text(node, "num"), _direct_text(node, "heading")
            if number:
                rows.append({"section_number": number, "section_name": heading,
                             "full_text": _body(node), "hierarchy": " > ".join(trail),
                             "source_url": source_url})
            return
        next_trail = trail
        if name == "container":
            label = " ".join(filter(None, (_direct_text(node, "prefix"), _direct_text(node, "num"), _direct_text(node, "heading"))))
            next_trail = trail + ([label] if label else [])
        for child in node:
            if _name(child) in {"container", "section"}:
                visit(child, next_trail)
    visit(root, [])
    return rows


def fixture_test() -> dict[str, Any]:
    fixture = Path(__file__).resolve().parents[1] / "validation" / "central-east" / "fixtures" / "baltimore-article-1.xml"
    rows = parse_article_xml(fixture.read_text(encoding="utf-8"), "fixture://baltimore/1.xml")
    assert len(rows) == 2 and rows[0]["section_number"] == "1-1"
    assert "not be lawful" in rows[0]["full_text"] and "Form and procedure" in rows[1]["full_text"]
    return {"passed": True, "sections": len(rows), "first_section": rows[0]["section_number"]}
