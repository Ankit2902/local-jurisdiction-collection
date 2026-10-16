"""Parser helpers for the King County Clerk's first-party HTML code.

King County publishes a landing page linking to one HTML file per title.  Each
title file carries both a contents listing and the enacted section text, so a
bulk collector should save the title HTML once, emit chapter/section TOC rows,
and split full text from that same artifact.  This avoids relying on the
Clerk's convenience PDFs or a non-official mirror.
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

TITLE_LINK = re.compile(r"^Title\s+[0-9]+[A-Z]?(?::|\s)", re.I)
SECTION = re.compile(r"^\s*(\d+(?:\.\d+){2,})\s+(.+?)\s*$", re.S)


def _clean(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def parse_landing_titles(html: str, base_url: str) -> list[dict[str, str]]:
    """Return first-party HTML title documents linked by the Clerk landing page."""
    soup = BeautifulSoup(html, "html.parser")
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href]"):
        label = _clean(anchor.get_text(" ", strip=True))
        url = urljoin(base_url, anchor["href"])
        if (not TITLE_LINK.match(label) or not url.lower().endswith(".htm")
                or "aqua.kingcounty.gov/council/clerk/code/" not in url.lower()
                or url in seen):
            continue
        seen.add(url)
        result.append({"label": label, "url": url})
    return result


def parse_title_sections(html: str, title_url: str) -> list[dict[str, str]]:
    """Extract substantive numbered sections from a single King County title.

    The title HTML repeats section numbers in a contents listing.  Only the
    later paragraph whose number/title is bold is an enacted provision, which
    keeps the TOC duplicate out of full-text output.
    """
    soup = BeautifulSoup(html, "html.parser")
    result: list[dict[str, str]] = []
    for paragraph in soup.select("p"):
        bold = paragraph.find(["b", "strong"])
        if not bold:
            continue
        leading = _clean(bold.get_text(" ", strip=True))
        match = SECTION.match(leading)
        if not match:
            continue
        full_text = _clean(paragraph.get_text(" ", strip=True))
        # Some Word-exported title pages place the body in following paragraphs.
        # This provision remains useful even where the first paragraph is short.
        result.append({
            "section_number": match.group(1),
            "section_name": match.group(2),
            "label": leading,
            "source_url": title_url + "#" + match.group(1),
            "full_text": full_text,
        })
    return result


def fixture_test() -> dict[str, object]:
    """Validate Clerk landing-to-title parsing against saved first-party HTML."""
    fixtures = Path(__file__).resolve().parents[1] / "validation" / "washington-arizona" / "fixtures"
    titles = parse_landing_titles((fixtures / "king-county-landing.html").read_text(encoding="utf-8"),
                                  "https://kingcounty.gov/code")
    sections = parse_title_sections((fixtures / "king-county-title-1.html").read_text(encoding="utf-8"),
                                    "https://aqua.kingcounty.gov/council/clerk/code/04_Title_1.htm")
    assert len(titles) == 2 and [section["section_number"] for section in sections] == ["1.02.005", "1.02.010"]
    return {"fixture": str(fixtures), "toc_entries": len(titles),
            "section_text_length": len(sections[0]["full_text"]), "passed": True}
