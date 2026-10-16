"""Code Publishing HTML adapter and lightweight live validation.

Code Publishing's California publications use a root page with title links,
title pages with chapter links, and chapter pages containing one or more
section headings.  A chapter page normally contains the complete text of each
of its sections; section URLs therefore use a stable fragment when one is
available.  This module does *not* treat redirect notices to another vendor as
Code Publishing publications.

``validate`` is intentionally a preflight, not a bulk crawler.  It makes only
three polite requests (root, one title, one chapter) and reports all evidence
needed before a registry entry can be enabled.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

USER_AGENT = "CompliSolv municipal-code validation/0.1"
TITLE_RE = re.compile(r"^\s*title\s+\S+", re.I)
CHAPTER_RE = re.compile(r"^\s*(?:chapter\s+)?\d+(?:\.\d+)+", re.I)
SECTION_RE = re.compile(r"^\s*(?:§\s*)?\d+(?:\.\d+){1,}", re.I)


@dataclass(frozen=True)
class Link:
    label: str
    url: str


def _absolute(base: str, href: str | None) -> str | None:
    if not href or href.startswith(("#", "javascript:", "mailto:")):
        return None
    return urljoin(base, href.split("#", 1)[0])


def _same_host(root_url: str, candidate: str) -> bool:
    return urlparse(root_url).netloc.lower() == urlparse(candidate).netloc.lower()


def _links(html: str, base_url: str, pattern: re.Pattern[str]) -> list[Link]:
    soup = BeautifulSoup(html, "html.parser")
    found: list[Link] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href]"):
        label = " ".join(anchor.get_text(" ", strip=True).split())
        url = _absolute(base_url, anchor.get("href"))
        if not url or not _same_host(base_url, url) or not pattern.search(label):
            continue
        if url not in seen:
            found.append(Link(label, url)); seen.add(url)
    return found


def parse_root_titles(html: str, root_url: str) -> list[Link]:
    """Return publication title pages; omit tables and uncodified ordinances."""
    return [x for x in _links(html, root_url, TITLE_RE)
            if "/html/" in x.url.lower()]


def parse_title_chapters(html: str, title_url: str) -> list[Link]:
    """Return chapter pages from a Code Publishing title page."""
    return [x for x in _links(html, title_url, CHAPTER_RE)
            if "/html/" in x.url.lower()]


def _heading_fragment(heading: Tag) -> str:
    for attr in ("id", "name"):
        value = heading.get(attr)
        if value:
            return str(value)
    anchor = heading.find("a", attrs={"name": True})
    return str(anchor["name"]) if anchor else ""


def parse_chapter_sections(html: str, chapter_url: str) -> list[dict[str, str]]:
    """Parse section headings/text from a chapter page without navigation chrome."""
    soup = BeautifulSoup(html, "html.parser")
    headings = [h for h in soup.select("h3, h4") if SECTION_RE.search(h.get_text(" ", strip=True))]
    sections: list[dict[str, str]] = []
    for index, heading in enumerate(headings):
        text_parts: list[str] = []
        for sibling in heading.next_siblings:
            if isinstance(sibling, Tag) and sibling in headings:
                break
            if isinstance(sibling, Tag) and sibling.name in {"script", "style", "nav", "footer"}:
                continue
            if isinstance(sibling, Tag):
                value = sibling.get_text(" ", strip=True)
            else:
                value = str(sibling).strip()
            if value:
                text_parts.append(value)
        label = " ".join(heading.get_text(" ", strip=True).split())
        number = re.match(r"(?:§\s*)?(\d+(?:\.\d+)+)", label)
        fragment = _heading_fragment(heading)
        sections.append({
            "section_number": number.group(1) if number else "",
            "section_name": label[number.end():].strip(" .—–-:") if number else label,
            "label": label,
            "source_url": chapter_url + ("#" + fragment if fragment else ""),
            "full_text": "\n".join(text_parts),
        })
    return sections


def _redirected_provider(html: str, final_url: str) -> str | None:
    haystack = (final_url + " " + BeautifulSoup(html, "html.parser").get_text(" ", strip=True)).lower()
    if "ecode360" in haystack:
        return "ecode360"
    if "municipal.codes" in haystack or "general code" in haystack:
        return "municipal.codes"
    return None


def validate(root_url: str) -> dict[str, Any]:
    """Validate root -> title TOC -> chapter/section live, returning evidence only."""
    result: dict[str, Any] = {
        "status": "error", "root_url": root_url, "toc_url": "", "section_url": "",
        "toc_count_or_sample": 0, "section_text_length": 0, "checks": [], "errors": [],
    }
    try:
        session = requests.Session()
        response = session.get(root_url, headers={"User-Agent": USER_AGENT}, timeout=30)
        result["checks"].append({"name": "root_http", "status_code": response.status_code, "final_url": response.url})
        if response.status_code != 200:
            result["status"] = "blocked" if response.status_code in (403, 429) else "error"
            result["errors"].append("Root request returned HTTP %s" % response.status_code)
            return result
        provider = _redirected_provider(response.text, response.url)
        if provider:
            result["status"] = "redirected_provider"
            result["errors"].append("Publication routes to %s; do not scrape with Code Publishing adapter." % provider)
            return result
        titles = parse_root_titles(response.text, response.url)
        result["toc_count_or_sample"] = len(titles)
        result["checks"].append({"name": "root_title_links", "count": len(titles), "sample": titles[0].label if titles else ""})
        if not titles:
            result["errors"].append("No Code Publishing title links found on root.")
            return result
        result["toc_url"] = titles[0].url
        title_response = session.get(titles[0].url, headers={"User-Agent": USER_AGENT}, timeout=30)
        result["checks"].append({"name": "title_http", "status_code": title_response.status_code})
        if title_response.status_code != 200:
            result["errors"].append("Title request returned HTTP %s" % title_response.status_code); return result
        chapters = parse_title_chapters(title_response.text, title_response.url)
        result["checks"].append({"name": "title_chapter_links", "count": len(chapters), "sample": chapters[0].label if chapters else ""})
        if not chapters:
            result["errors"].append("No chapter links found on title page."); return result
        chapter_response = session.get(chapters[0].url, headers={"User-Agent": USER_AGENT}, timeout=30)
        result["checks"].append({"name": "chapter_http", "status_code": chapter_response.status_code})
        if chapter_response.status_code != 200:
            result["errors"].append("Chapter request returned HTTP %s" % chapter_response.status_code); return result
        sections = parse_chapter_sections(chapter_response.text, chapter_response.url)
        result["checks"].append({"name": "chapter_sections", "count": len(sections), "sample": sections[0]["label"] if sections else ""})
        if not sections:
            result["errors"].append("No section headings found on chapter page."); return result
        result["section_url"] = sections[0]["source_url"]
        result["section_text_length"] = len(sections[0]["full_text"])
        if not result["section_text_length"]:
            result["errors"].append("Representative section has no extracted text."); return result
        result["status"] = "validated"
    except requests.RequestException as exc:
        result["status"] = "blocked"
        result["errors"].append("HTTP validation failed: %s" % exc)
    except Exception as exc:  # validation must return a manifest-shaped result
        result["errors"].append("Parser validation failed: %s" % exc)
    return result


def fixture_test() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1] / "validation" / "fixtures" / "codepublishing"
    titles = parse_root_titles((root / "root.html").read_text(encoding="utf-8"), "https://www.codepublishing.com/CA/Fremont/")
    chapters = parse_title_chapters((root / "title.html").read_text(encoding="utf-8"), titles[0].url)
    sections = parse_chapter_sections((root / "chapter.html").read_text(encoding="utf-8"), chapters[0].url)
    assert len(titles) == 2 and len(chapters) == 2 and sections[0]["section_number"] == "1.05.010"
    return {"fixture": str(root), "toc_entries": len(titles), "sections": len(sections),
            "section_text_length": len(sections[0]["full_text"]), "passed": True}
