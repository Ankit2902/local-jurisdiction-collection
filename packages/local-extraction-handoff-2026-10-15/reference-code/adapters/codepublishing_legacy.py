"""Parser for Code Publishing/General Code's legacy municipal-code pages.

This is deliberately separate from :mod:`codepublishing`: Washington's
General Code presentation uses hash-bang routes and, for Renton, Roman-title
and hyphenated section numbering.  Flagstaff's older publication additionally
uses a frameset.  Both still expose ordinary HTML once the browser has reached
the title or chapter document, so browser transport and this parser form one
production-capable pilot.
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

TITLE_RE = re.compile(r"^\s*title\s+(?:\d+|[ivxlcdm]+)\b", re.I)
CHAPTER_RE = re.compile(r"^\s*(?:chapter\s+)?\d+(?:[.-]\d+)*\b", re.I)
SECTION_RE = re.compile(r"^\s*\d+(?:[.-]\d+){1,}\b")


def _links(html: str, base_url: str, expression: re.Pattern[str]) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href]"):
        label = " ".join(anchor.get_text(" ", strip=True).split())
        href = anchor.get("href")
        if not href or not expression.search(label):
            continue
        url = urljoin(base_url, href)
        if url not in seen:
            result.append({"label": label, "source_url": url})
            seen.add(url)
    return result


def parse_root_titles(html: str, root_url: str) -> list[dict[str, str]]:
    return _links(html, root_url, TITLE_RE)


def parse_title_chapters(html: str, title_url: str) -> list[dict[str, str]]:
    return _links(html, title_url, CHAPTER_RE)


def parse_chapter_sections(html: str, chapter_url: str) -> list[dict[str, str]]:
    """Return all section headings and their following enacted text."""
    soup = BeautifulSoup(html, "html.parser")
    headings = [h for h in soup.select("h1,h2,h3,h4")
                if SECTION_RE.search(h.get_text(" ", strip=True))]
    result: list[dict[str, str]] = []
    for position, heading in enumerate(headings):
        parts: list[str] = []
        for sibling in heading.next_siblings:
            if isinstance(sibling, Tag) and sibling in headings:
                break
            if isinstance(sibling, Tag) and sibling.name in {"script", "style", "nav", "footer"}:
                continue
            value = sibling.get_text(" ", strip=True) if isinstance(sibling, Tag) else str(sibling).strip()
            if value:
                parts.append(value)
        label = " ".join(heading.get_text(" ", strip=True).split())
        number = SECTION_RE.search(label)
        result.append({
            "section_number": number.group(0) if number else "",
            "section_name": label[number.end():].strip(" .:—–-") if number else label,
            "label": label,
            "source_url": chapter_url,
            "full_text": "\n".join(parts),
        })
    return result


def fixture_test() -> dict[str, object]:
    """Exercise each numbering/navigation variant covered by the pilot fixtures."""
    fixtures = Path(__file__).resolve().parents[1] / "validation" / "washington-arizona" / "fixtures"
    bases = {
        "burien": "https://www.codepublishing.com/WA/Burien/",
        "renton": "https://www.codepublishing.com/WA/Renton/",
        "seatac": "https://www.codepublishing.com/WA/SeaTac/",
        "flagstaff": "https://www.codepublishing.com/AZ/Flagstaff/",
    }
    first_text_length = 0
    for slug, base in bases.items():
        titles = parse_root_titles((fixtures / (slug + "-root.html")).read_text(encoding="utf-8"), base)
        assert titles
        chapters = parse_title_chapters((fixtures / (slug + "-title.html")).read_text(encoding="utf-8"), titles[0]["source_url"])
        assert chapters
        sections = parse_chapter_sections((fixtures / (slug + "-chapter.html")).read_text(encoding="utf-8"), chapters[0]["source_url"])
        assert sections and sections[0]["section_number"] and len(sections[0]["full_text"]) > 40
        first_text_length = max(first_text_length, len(sections[0]["full_text"]))
    return {"fixture": str(fixtures), "publications": len(bases),
            "toc_entries": len(bases), "section_text_length": first_text_length, "passed": True}
