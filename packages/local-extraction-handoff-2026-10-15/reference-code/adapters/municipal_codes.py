"""Parser helpers for the ICC Code Solutions / municipal.codes platform.

Some publications use client-side rendering and may present a Cloudflare bot
verification page to non-browser clients.  The parser is intentionally separate
from transport so a permitted browser-backed fetcher can supply the rendered HTML.
"""
from __future__ import annotations

from typing import Any
from pathlib import Path
from urllib.parse import urljoin
from urllib.parse import urlparse

from bs4 import BeautifulSoup


def parse_toc_html(html: str, base_url: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    entries: list[dict[str, str]] = []
    base = base_url.rstrip("/")
    parsed_base = urlparse(base)
    for anchor in soup.select("main a[href]"):
        label = anchor.get_text(" ", strip=True)
        href = urljoin(base_url, anchor["href"])
        parsed = urlparse(href)
        in_publication = (parsed.netloc == parsed_base.netloc and
                          (parsed.path == parsed_base.path or parsed.path.startswith(parsed_base.path + "/")))
        if label and in_publication and href.rstrip("/") != base:
            entries.append({"label": label, "url": href})
    return entries


def parse_section_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.select_one("main")
    return main.get_text("\n", strip=True) if main else ""


def parse_sections_html(html: str, page_url: str) -> list[dict[str, str]]:
    """Return every provision rendered on an ICC Municipal Codes page.

    ICC serves a whole chapter on routes such as ``/Code/1.01.010``.  The
    route name is therefore not a reliable indication that the DOM has only
    one provision: each actual provision is an ``article.type-Section``.
    Keeping those cards separate prevents a chapter from being emitted as one
    enormous, incorrectly cited full-text record.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, str]] = []
    for section in soup.select("article.type-Section"):
        number = section.get("data-short-cite", "").strip()
        heading = section.select_one("header .inner-header, h1, h2, h3, h4, h5, h6")
        if heading:
            number = section.select_one("header .num") and section.select_one("header .num").get_text(" ", strip=True) or number
            name_node = section.select_one("header .name")
            name = name_node.get_text(" ", strip=True) if name_node else heading.get_text(" ", strip=True)
        else:
            name = ""
        text = section.get_text("\n", strip=True)
        # The header is deliberately retained in full_text: it is part of the
        # publisher's rendered legal content and preserves a standalone read.
        if not number or not text:
            continue
        source_url = urljoin(page_url, section.get("data-history", "").removesuffix("/history"))
        # ``data-history`` is absent on a small number of old sections; their
        # canonical anchor is still stable enough to retain the fetched URL.
        if source_url == page_url:
            source_url = page_url
        rows.append({"section_number": number, "section_name": name,
                     "label": f"{number} {name}".strip(), "full_text": text,
                     "source_url": source_url})
    return rows


def validate(root_url: str) -> dict[str, Any]:
    """Return an explicit discovery result; transport is intentionally external."""
    return {"status": "browser-required", "root_url": root_url, "toc_url": root_url,
            "section_url": "", "toc_count_or_sample": 0, "section_text_length": 0,
            "checks": ["Use parse_toc_html and parse_section_text with browser-rendered HTML."],
            "errors": ["This platform may serve Cloudflare verification to non-browser clients."]}


def fixture_test() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1] / "fixtures" / "municipal_codes"
    entries = parse_toc_html((root / "sonoma-root-sample.html").read_text(encoding="utf-8"), "https://sonoma.municipal.codes/SMC")
    text = parse_section_text((root / "sonoma-section-sample.html").read_text(encoding="utf-8"))
    assert len(entries) == 2 and "Municipal Code is adopted" in text
    return {"fixture": str(root), "toc_entries": len(entries), "section_text_length": len(text), "passed": True}
