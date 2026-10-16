"""Pure parser helpers for browser-rendered American Legal code pages."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup


TOC_RE = re.compile(r"^(?:Title|Chapter|Article)\s+\S+", re.I)


def parse_toc_html(html: str, base_url: str, product: str) -> list[dict[str, str]]:
    """Return title/chapter links belonging to one American Legal publication."""
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    marker = f"/codes/{product}/latest/"
    for anchor in soup.select("a[href]"):
        label = anchor.get_text(" ", strip=True)
        url = urljoin(base_url, anchor["href"])
        if label and TOC_RE.match(label) and marker in url and url not in seen:
            seen.add(url)
            rows.append({"label": label, "source_url": url})
    return rows


def parse_section_html(html: str) -> str:
    """Return enacted text from the dedicated American Legal section container."""
    soup = BeautifulSoup(html, "html.parser")
    node = soup.select_one("#curr-section")
    if not node:
        return ""
    # Family, title, and chapter routes can place a link-only child index in
    # the same container used by genuine provisions.  A navigation index is a
    # TOC, not full text; enacted pages contain substantive paragraph/list/table
    # structure even when they also include cross-reference links.
    if node.select("a[href]") and not node.select("p, table, ol, ul, blockquote"):
        return ""
    return node.get_text("\n", strip=True)


def validate(root_url: str) -> dict[str, Any]:
    return {"status": "browser-rendered-required", "root_url": root_url, "toc_url": root_url,
            "section_url": "", "toc_count_or_sample": 0, "section_text_length": 0,
            "checks": ["Resolve the moving /latest/ alias in a browser before collection."], "errors": []}


def fixture_test() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1] / "fixtures" / "amlegal"
    toc = parse_toc_html((root / "palo-alto-toc.html").read_text(encoding="utf-8"),
                         "https://codelibrary.amlegal.com/codes/paloalto/latest/paloalto_ca/0-0-0-59578", "paloalto")
    text = parse_section_html((root / "palo-alto-section.html").read_text(encoding="utf-8"))
    assert len(toc) == 2 and "Palo Alto" in text and "Site navigation" not in text
    return {"fixture": str(root), "toc_entries": len(toc), "section_text_length": len(text), "passed": True}
