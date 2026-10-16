"""CivicPlus City Code collection helpers.

The current CivicPlus platform stores the collection membership in the official
landing page's widget configuration.  The asset UUID is stable enough for a
single run, but must always be discovered afresh from that landing page.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ASSET_URL = "https://content.civicplus.com/api/assets/{asset_id}"
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
CONFIG_IDS = re.compile(r'manualContentItemIds\s*:\s*\[(.*?)\]', re.S)
QUOTED_ID = re.compile(r'["\']([0-9a-f-]{36})["\']', re.I)
ROCKLAND_LABEL = re.compile(r"^(?:Chapter\s+\d{1,2}\b|City Charter\b)", re.I)


def asset_url(asset_id: str) -> str:
    if not UUID.fullmatch(asset_id):
        raise ValueError("not a CivicPlus asset UUID: %r" % asset_id)
    return ASSET_URL.format(asset_id=asset_id)


def parse_portland_asset_ids(html: str) -> list[str]:
    """Return the official City Code widget's PDF asset IDs, in display order."""
    for match in CONFIG_IDS.finditer(html):
        ids = QUOTED_ID.findall(match.group(1))
        # Portland's code widget has dozens of PDFs; ignore unrelated one-item
        # article widgets and retain page order for a reproducible run manifest.
        if len(ids) >= 10:
            return ids
    return []


def parse_rockland_index(html: str, base_url: str) -> list[dict[str, str]]:
    """Extract the Code Chapters plus Charter from Rockland's official index."""
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin

    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href]"):
        label = " ".join(anchor.get_text(" ", strip=True).split())
        href = urljoin(base_url, anchor["href"])
        if ROCKLAND_LABEL.match(label) and "/DocumentCenter/" in href and href not in seen:
            rows.append({"label": label, "url": href})
            seen.add(href)
    return rows


SECTION = re.compile(r"(?im)^\s*(?:Sec(?:tion)?\.?\s*)(\d+(?:[-.]\d+)+)\.?\s*(.+?)\s*$")


def parse_pdf_sections(text: str) -> list[dict[str, str]]:
    """Split CivicPlus-hosted city-code PDF text on printed section headers."""
    hits = list(SECTION.finditer(text))
    rows: list[dict[str, str]] = []
    for number, hit in enumerate(hits):
        end = hits[number + 1].start() if number + 1 < len(hits) else len(text)
        body = text[hit.end():end].strip()
        if body:
            rows.append({"section_number": hit.group(1), "section_name": hit.group(2).strip(), "full_text": body})
    return rows


def fixture_test() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1] / "validation" / "central-east" / "fixtures"
    portland = (root / "portland-city-code-root.html").read_text(encoding="utf-8")
    rockland = (root / "rockland-index.html").read_text(encoding="utf-8")
    body = (root / "portland-chapter-13.txt").read_text(encoding="utf-8")
    assert len(parse_portland_asset_ids(portland)) == 10
    assert len(parse_rockland_index(rockland, "https://www.rocklandmaine.gov/288/Charter-Code-Ordinances")) == 3
    sections = parse_pdf_sections(body)
    assert sections and sections[0]["section_number"] == "13-1"
    return {"passed": True, "portland_assets": 10, "rockland_documents": 3, "sections": len(sections)}
