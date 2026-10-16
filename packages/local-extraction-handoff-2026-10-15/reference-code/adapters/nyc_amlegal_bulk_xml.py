"""Parse the three American Legal bulk XML packages for New York City.

American Legal publishes separate archives for the Charter, Administrative
Code, and Rules.  They are intentionally separate output families: a caller
must never merge agency Rules into the Administrative Code just because both
are municipal legal material.  This adapter is deliberately offline; the
runner downloads an archive once, records the response metadata, and passes
its bytes to :func:`parse_bulk_zip`.
"""
from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import zipfile
from typing import Any


NYC_BULK_FAMILIES = {
    "charter": "https://files.amlegal.com/pdffiles/NewYorkCity/Charter/XML.zip",
    "administrative_code": "https://files.amlegal.com/pdffiles/NewYorkCity/Admin/XML.zip",
    "rules": "https://files.amlegal.com/pdffiles/NewYorkCity/Rules/XML.zip",
}


def _tag(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1].upper()


def _text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return re.sub(r"\s+", " ", "".join(element.itertext())).strip()


def _child(element: ET.Element, name: str) -> ET.Element | None:
    return next((item for item in element if _tag(item) == name), None)


def _level_label(level: ET.Element) -> str:
    return level.get("style-name", "").strip() or "Level"


SECTION_HEADING_RE = re.compile(
    r"^(?:§\s*)?(?:\d+[A-Za-z]?(?:[-.]\d+[A-Za-z]?)+\b|\d+\.|[A-Za-z]+-\d+\b)|^(?:Section|Sec\.)\s+\d",
    re.IGNORECASE,
)


def parse_document_xml(xml_text: str, code_family: str, source_url: str = "") -> list[dict[str, str]]:
    """Extract section-level text records from one ALP XML document.

    ALP splits a publication into many XML documents.  ``RECORD`` is its
    stable content unit, while nested ``LEVEL`` elements carry the hierarchy.
    Keeping both the archive member URL and the record id enables an
    incremental production run even when the publisher changes page URLs.
    """
    root = ET.fromstring(xml_text.lstrip("\ufeff"))
    records: list[dict[str, str]] = []

    def visit(node: ET.Element, trail: list[str]) -> None:
        if _tag(node) == "LEVEL":
            trail = [*trail, _level_label(node)]
        if _tag(node) == "RECORD":
            heading = _text(_child(node, "HEADING"))
            body = " ".join(_text(item) for item in node if _tag(item) == "PARA").strip()
            if body or heading:
                records.append({"id": node.get("id", ""), "heading": heading, "body": body,
                                "hierarchy": " > ".join(trail)})
        for child in node:
            if _tag(child) in {"LEVEL", "RECORD"}:
                visit(child, trail)

    visit(root, [])

    # In ALP XML, a provision heading and each following paragraph are
    # separate RECORDs.  Group continuation paragraphs under the provision
    # heading so a full-text CSV row means a legal section, not a paragraph.
    rows: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for record in records:
        if SECTION_HEADING_RE.match(record["heading"]):
            current = {
                "code_family": code_family,
                "source_node_id": record["id"],
                "section_id": record["id"],
                "section_heading": record["heading"],
                "text": record["body"],
                "hierarchy": record["hierarchy"],
                "source_url": source_url,
            }
            rows.append(current)
        elif current is not None and record["body"]:
            current["text"] = " ".join(part for part in (current["text"], record["body"]) if part)
    return rows


def _decode_xml(raw: bytes) -> str:
    """ALP archives nominally declare UTF-8 but some NYC members use cp1252."""
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252")


def parse_bulk_zip(zip_bytes: bytes, code_family: str, archive_url: str = "") -> list[dict[str, str]]:
    """Parse every XML member in one official NYC family archive."""
    rows: list[dict[str, str]] = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        for member in archive.namelist():
            if not member.lower().endswith(".xml"):
                continue
            member_url = f"{archive_url}!/{member}" if archive_url else member
            rows.extend(parse_document_xml(_decode_xml(archive.read(member)), code_family, member_url))
    return rows


def validate(root_url: str = "") -> dict[str, Any]:
    return {
        "status": "bulk-download-required",
        "root_url": root_url,
        "code_families": NYC_BULK_FAMILIES,
        "checks": [
            "Download each archive separately and record checksum/current-through text.",
            "Emit three output families; do not merge Charter, Administrative Code, and Rules.",
        ],
    }


def fixture_test() -> dict[str, Any]:
    """Offline contract test used by the shared validation dispatcher."""
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "nyc-amlegal-sample.xml"
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("XML/0-0-0-1.xml", fixture.read_bytes())
    rows = parse_bulk_zip(payload.getvalue(), "charter", "fixture://Charter/XML.zip")
    assert len(rows) == 1 and rows[0]["section_id"] == "0-0-0-2"
    return {"fixture": str(fixture), "sections": len(rows), "passed": True}
