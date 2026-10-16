"""Small, isolated eCode360 extraction helpers.

eCode360 uses stable numeric page URLs.  A browser-capable transport is the
validated route in this project: it receives the rendered nested navigation
that direct requests may not.  The parser below deliberately consumes the
rendered HTML exported by that transport rather than assuming a public API.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

SECTION = re.compile(r"^[^0-9]*\d+(?:[-.]\d+)+(?:[-.]\d+)?")

def parse_rendered_sections(html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    # Current rendered eCode360 pages place the visible section heading inside
    # ``header > .contentTitle.sectionTitle`` and the enactment in its later
    # sibling ``.section_content.content``. It is not an H2 sibling, which is
    # why a heading-only traversal loses the live provision text.
    for title in soup.select(".contentTitle.sectionTitle[data-code-content-type='section']"):
        header = title.find_parent("header")
        content = None
        if header:
            for sibling in header.next_siblings:
                if getattr(sibling, "name", None) == "header":
                    break
                classes = sibling.get("class", []) if hasattr(sibling, "get") else []
                if "section_content" in classes:
                    content = sibling
                    break
        label = " ".join((title.get("data-full-title") or title.get_text(" ", strip=True)).split())
        text = content.get_text("\n", strip=True) if content else ""
        if label and text:
            rows.append({"label": label, "full_text": text})
    if rows:
        return rows
    for heading in soup.select("h1, h2, h3, h4"):
        label = " ".join(heading.get_text(" ", strip=True).split())
        if label.lower().startswith(("chapter", "article", "title")) or not SECTION.match(label):
            continue
        chunks = []
        for sibling in heading.next_siblings:
            if getattr(sibling, "name", None) in {"h1", "h2", "h3", "h4"}:
                break
            text = sibling.get_text(" ", strip=True) if hasattr(sibling, "get_text") else str(sibling).strip()
            if text:
                chunks.append(text)
        rows.append({"label": label, "full_text": "\n".join(chunks)})
    return rows


def parse_toc_html(html: str, base_url: str) -> list[dict[str, str]]:
    """Extract eCode360 code-node links from a saved rendered root fixture."""
    soup = BeautifulSoup(html, "html.parser")
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href]"):
        label = anchor.get_text(" ", strip=True)
        href = urljoin(base_url, anchor["href"])
        if not label or href in seen or "/laws/" in href or href.lower().endswith(".pdf"):
            continue
        leaf = href.rsplit("/", 1)[-1]
        if "ecode360.com/" in href and (any(char.isdigit() for char in leaf) or "/code" in href):
            entries.append({"label": label, "url": href})
            seen.add(href)
    return entries


def parse_section_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for selector in (".section_content.content", "main", "article", "#content", ".code-content", ".content"):
        node = soup.select_one(selector)
        if node:
            text = node.get_text("\n", strip=True)
            if text:
                return text
    return ""


def validate(root_url: str) -> dict[str, Any]:
    """Preflight direct HTTP; callers should use rendered-browser transport on 403."""
    result: dict[str, Any] = {"status": "blocked", "root_url": root_url, "toc_url": root_url,
                              "section_url": "", "toc_count_or_sample": 0, "section_text_length": 0,
                              "checks": [], "errors": []}
    try:
        response = requests.get(root_url, headers={"User-Agent": "CompliSolv municipal-code validation bot/0.1"}, timeout=45)
        if response.status_code in (401, 403, 429):
            result["errors"].append("eCode360 denied direct preflight with HTTP %s; rendered-browser transport required." % response.status_code)
            return result
        response.raise_for_status()
        entries = parse_toc_html(response.text, response.url)
        if not entries:
            raise RuntimeError("no code-node links identified in root HTML")
        section = requests.get(entries[0]["url"], headers={"User-Agent": "CompliSolv municipal-code validation bot/0.1"}, timeout=45)
        section.raise_for_status()
        text = parse_section_text(section.text)
        if not text:
            raise RuntimeError("representative node contained no readable text")
        result.update({"status": "validated", "toc_url": response.url, "section_url": section.url,
                       "toc_count_or_sample": len(entries), "section_text_length": len(text),
                       "checks": ["root HTML returned code-node links", "representative node returned readable text"]})
    except (requests.RequestException, RuntimeError) as exc:
        result["errors"].append(str(exc))
    return result


def fixture_test() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1] / "fixtures" / "ecode360"
    links = parse_toc_html((root / "root-sample.html").read_text(encoding="utf-8"), "https://ecode360.com/44587767")
    text = parse_section_text((root / "section-sample.html").read_text(encoding="utf-8"))
    assert len(links) == 1 and "City of Burlingame" in text
    return {"fixture": str(root), "toc_entries": len(links), "section_text_length": len(text), "passed": True}
