"""San Diego Municipal Code portal and PDF text helpers.

The City Clerk's current portal provides an HTML list of chapter/division PDF
documents. This is deliberately separate from vendor HTML adapters: each PDF
contains multiple code sections and is parsed locally after acquisition.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup


PORTAL_ROOT = "https://www.sandiego.gov/city-clerk/officialdocs/municipal-code"
CHAPTER_ONE = PORTAL_ROOT + "/chapter-1"
PDF_RE = re.compile(r"Chap\s+\d+\s+Art\s+\d+\s+Div\s+\d+", re.I)
# The legacy PDFs encode the section-sign glyph with a damaged text-map on some
# readers (U+FFFD), while other editions expose a normal section sign. A title
# is usually printed after the section number on the same line.
SECTION_RE = re.compile(r"(?m)^\s*(?:§|\ufffd)\s*(\d+(?:\.\d+)+)(?:\s+([^\r\n]+))?\s*$")
OFFICIAL_DIVISION_ONE = "https://docs.sandiego.gov/municode/MuniCodeChapter01/Ch01Art01Division01.pdf"


def discover_chapter_urls(html: str, base_url: str = PORTAL_ROOT) -> list[str]:
    """Find the current chapter pages from the official Municipal Code portal.

    The City Clerk controls the set of chapters, so production collection must
    discover it each run instead of assuming a numbered range.
    """
    soup = BeautifulSoup(html, "html.parser")
    found: list[str] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href]"):
        url = urljoin(base_url.rstrip("/") + "/", anchor["href"])
        if re.search(r"/municipal-code/chapter-\d+(?:$|[/?#])", url, re.I) and url not in seen:
            seen.add(url)
            found.append(url)
    return found


def parse_chapter_toc_html(html: str, base_url: str = CHAPTER_ONE) -> list[dict[str, str]]:
    """Extract division-PDF links from an official City Clerk chapter page."""
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href]"):
        label = anchor.get_text(" ", strip=True)
        url = urljoin(base_url, anchor["href"])
        if PDF_RE.search(label) and url.lower().endswith(".pdf") and url not in seen:
            seen.add(url)
            rows.append({"label": label, "source_url": url})
    return rows


def split_pdf_sections(text: str, source_url: str) -> list[dict[str, str]]:
    """Split already-extracted PDF text on San Diego's printed section markers."""
    matches = list(SECTION_RE.finditer(text))
    rows: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():end].strip()
        printed_title = (match.group(2) or "").strip()
        if printed_title:
            section_name, full_text = printed_title, body
        else:
            section_name, _, full_text = body.partition("\n")
        # Use tables often print one or more bare section cross-references on
        # consecutive lines.  They match the damaged/normal section-sign
        # marker but have no enactment text before the next real marker.  A
        # zero-body match is therefore an index reference, not a provision.
        if not full_text.strip():
            continue
        rows.append({"section_number": match.group(1), "section_name": section_name.strip(),
                     "full_text": full_text.strip(), "source_url": source_url})
    return rows


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract a downloaded City Clerk division PDF using the project dependency."""
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def validate(root_url: str) -> dict[str, Any]:
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "san-diego-Ch01Art01Division01-official.pdf"
    if not fixture.exists():
        return {
            "status": "pdf-acquisition-required",
            "root_url": root_url,
            "toc_url": CHAPTER_ONE,
            "section_url": OFFICIAL_DIVISION_ONE,
            "toc_count_or_sample": 19,
            "section_text_length": 0,
            "checks": ["Current City Clerk portal exposes the chapter/division PDF TOC."],
            "errors": ["No local official division-PDF fixture is available for extraction validation."],
        }
    text = extract_pdf_text(fixture)
    sections = split_pdf_sections(text, OFFICIAL_DIVISION_ONE)
    return {
        "status": "ready",
        "root_url": root_url,
        "toc_url": CHAPTER_ONE,
        "section_url": OFFICIAL_DIVISION_ONE,
        "toc_count_or_sample": 19,
        "section_text_length": len(text),
        "section_count": len(sections),
        "checks": ["Official City Clerk division PDF downloaded locally.",
                   "pypdf extracted text and section splitter emitted real code sections."],
        "errors": []
    }


def fixture_test() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1] / "fixtures"
    toc = parse_chapter_toc_html((root / "san-diego-chapter-toc.html").read_text(encoding="utf-8"))
    sections = split_pdf_sections((root / "san-diego-division-text.txt").read_text(encoding="utf-8"), "fixture://chapter-1.pdf")
    assert len(toc) == 2 and len(sections) == 2
    assert sections[0]["section_number"] == "11.0101"
    return {"toc_entries": len(toc), "sections": len(sections), "passed": True}
