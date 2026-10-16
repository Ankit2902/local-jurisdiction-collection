"""Browser-rendered parser helpers for Gridics CodeHUB municipal codes.

CodeHUB routes code nodes with hash fragments and UUIDs, so a browser-capable
collector supplies rendered HTML to these pure parsers.  The helpers preserve
the visible Title/Chapter/Section hierarchy without depending on UUIDs.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag


TITLE_RE = re.compile(r"^TITLE\s+\d+\s*:", re.I)
CHAPTER_RE = re.compile(r"^CHAPTER\s+\d+(?:\.\d+)+\s*:", re.I)
SECTION_RE = re.compile(r"^(\d+(?:\.\d+)+)\s+(.+)$")


def parse_toc_html(html: str) -> list[dict[str, str]]:
    """Return Title and Chapter labels from a rendered CodeHUB TOC."""
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, str]] = []
    title = ""
    for heading in soup.select("h2, h3"):
        label = heading.get_text(" ", strip=True)
        if TITLE_RE.match(label):
            title = label
        elif CHAPTER_RE.match(label):
            rows.append({"title": title, "chapter": label})
    return rows


def parse_sections_html(html: str) -> list[dict[str, str]]:
    """Extract section text between CodeHUB's visible H4 section headings."""
    soup = BeautifulSoup(html, "html.parser")
    title = ""
    chapter = ""
    rows: list[dict[str, str]] = []
    for heading in soup.select("h2, h3, h4"):
        label = heading.get_text(" ", strip=True)
        if TITLE_RE.match(label):
            title = label
            continue
        if CHAPTER_RE.match(label):
            chapter = label
            continue
        match = SECTION_RE.match(label)
        if not match:
            continue
        # Current CodeHUB wraps each heading and its text in a ``.section``
        # div.  The heading itself sits inside an anchor child, so scanning its
        # next siblings (the older markup) sees only share/print controls and
        # loses the provision body.  Retain the sibling fallback for saved
        # legacy pages, but prefer the semantic rendered section container.
        container = heading.find_parent("div", class_="section")
        if container:
            body_nodes = container.select("p, li, td, th, blockquote")
            parts = [_clean_text(node.get_text(" ", strip=True)) for node in body_nodes]
            parts = [part for part in parts if part]
        else:
            parts = []
            for sibling in heading.next_siblings:
                if isinstance(sibling, Tag) and sibling.name in {"h2", "h3", "h4"}:
                    break
                if isinstance(sibling, Tag):
                    value = sibling.get_text(" ", strip=True)
                else:
                    value = str(sibling).strip()
                if value:
                    parts.append(value)
        rows.append({"title": title, "chapter": chapter, "section_number": match.group(1),
                     "section_name": match.group(2), "full_text": "\n".join(parts)})
    return rows


def _clean_text(value: str) -> str:
    return " ".join((value or "").split())


def validate(root_url: str) -> dict[str, Any]:
    return {"status": "browser-rendered-required", "root_url": root_url, "toc_url": root_url,
            "section_url": "", "toc_count_or_sample": 0, "section_text_length": 0,
            "checks": ["Use rendered CodeHUB HTML; UUID hash routes are client-side."], "errors": []}


def fixture_test() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1] / "fixtures" / "gridics"
    toc = parse_toc_html((root / "cupertino-toc.html").read_text(encoding="utf-8"))
    sections = parse_sections_html((root / "cupertino-section.html").read_text(encoding="utf-8"))
    assert len(toc) == 2 and sections[0]["section_number"] == "1.01.010"
    return {"fixture": str(root), "toc_entries": len(toc), "sections": len(sections),
            "section_text_length": len(sections[0]["full_text"]), "passed": True}
