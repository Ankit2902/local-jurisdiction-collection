"""Resumable full collectors for publisher-approved bulk and first-party sources.

This module is intentionally independent of :mod:`municipal_code_scraper`'s
dispatcher.  It is the production building block for sources which are not
ordinary HTML link trees: official XML archives, official document collections,
the King County Clerk title files, and San Diego's division PDFs.  Callers can
use the functions directly now; a future batch manager can register them
without duplicating parsing or output logic.
"""
from __future__ import annotations

import csv
import hashlib
import json
import io
import zipfile
from datetime import date
from pathlib import Path
from typing import Callable, Iterable

import requests

from . import baltimore_openlaw_bulk_xml, civicplus_assets, kingcounty_code
from . import nyc_amlegal_bulk_xml, openlaw_bulk_xml, san_diego_pdf


SCHEMA = [
    "jurisdiction", "code_name", "division", "title", "subtitle", "chapter",
    "subchapter", "article", "part", "subpart", "section_number",
    "section_name", "citation", "full_text", "source_url", "scrape_date",
]
HIERARCHY = ("code_name", "division", "title", "subtitle", "chapter",
             "subchapter", "article", "part", "subpart")
HEADERS = {"User-Agent": "CompliSolv municipal-code collector/1.0"}


class SpecialCollector:
    """Small cached transport plus a checkpointed writer for special sources."""

    def __init__(self, jurisdiction: str, slug: str, root: Path, *, session: requests.Session | None = None):
        self.jurisdiction, self.slug, self.root = jurisdiction, slug, Path(root)
        self.cache = self.root / "cache" / slug
        self.out = self.root / "outputs"
        self.checkpoint_path = self.root / "checkpoints" / f"{slug}.json"
        self.cache.mkdir(parents=True, exist_ok=True)
        self.out.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        self.session = session or requests.Session()
        self.session.headers.update(HEADERS)
        self.checkpoint = self._load_checkpoint()

    def _load_checkpoint(self) -> dict:
        if self.checkpoint_path.exists():
            return json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
        return {"jurisdiction": self.jurisdiction, "completed_documents": [], "failed_documents": []}

    def save_checkpoint(self) -> None:
        temp = self.checkpoint_path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.checkpoint, indent=2), encoding="utf-8")
        temp.replace(self.checkpoint_path)

    def fetch_bytes(self, url: str) -> bytes:
        """Fetch once, cache by URL, and preserve cache for a resumable re-run."""
        target = self.cache / hashlib.sha256(url.encode()).hexdigest()
        if target.exists():
            return target.read_bytes()
        response = self.session.get(url, timeout=90)
        response.raise_for_status()
        target.write_bytes(response.content)
        return response.content

    def fetch_text(self, url: str) -> str:
        raw = self.fetch_bytes(url)
        # Most official sites are UTF-8, but the King County Clerk's live
        # Word-exported code files explicitly use Windows-1252.  Replacing
        # invalid bytes can corrupt the visible section headings; fall back to
        # the declared legacy family rather than silently losing provisions.
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("cp1252")

    def mark(self, document: str, *, error: str = "") -> None:
        key = "failed_documents" if error else "completed_documents"
        item = {"document": document, "date": date.today().isoformat()}
        if error:
            item["error"] = error
        if not any(x["document"] == document for x in self.checkpoint[key]):
            self.checkpoint[key].append(item)
            self.save_checkpoint()

    def finished(self, document: str) -> bool:
        return any(x["document"] == document for x in self.checkpoint["completed_documents"])

    def write(self, rows: list[dict], code_name: str, family: str = "code") -> dict:
        clean: list[dict] = []
        for raw in rows:
            row = {field: "" for field in SCHEMA}
            row.update({field: raw.get(field, "") for field in SCHEMA})
            row["jurisdiction"] = self.jurisdiction
            row["code_name"] = raw.get("code_name") or code_name
            row["division"] = raw.get("division") or family
            row["citation"] = raw.get("citation") or raw.get("section_number", "")
            row["scrape_date"] = date.today().isoformat()
            clean.append(row)
        stem = f"{self.slug}-municipal-{family}"
        json_path, csv_path = self.out / f"{stem}.json", self.out / f"{stem}.csv"
        json_path.write_text(json.dumps({"metadata": {"jurisdiction": self.jurisdiction,
            "code_name": code_name, "family": family, "total_provisions": len(clean),
            "full_text_complete": sum(bool(x["full_text"]) for x in clean)},
            "provisions": clean}, ensure_ascii=False, indent=2), encoding="utf-8")
        with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=SCHEMA)
            writer.writeheader(); writer.writerows(clean)
        return {"json": str(json_path), "csv": str(csv_path), "rows": len(clean),
                "full_text_rows": sum(bool(x["full_text"]) for x in clean)}


def _trail_to_fields(trail: str) -> dict[str, str]:
    fields = {key: "" for key in HIERARCHY}
    for label in (x.strip() for x in trail.split(">")):
        lower = label.lower()
        for key in HIERARCHY:
            if lower.startswith(key.replace("_", " ")):
                fields[key] = label
    return fields


def collect_nyc_bulk(root: Path, *, fetch: Callable[[str], bytes] | None = None) -> list[dict]:
    """Download each official NYC XML archive and emit one family output each."""
    collector = SpecialCollector("New York City, New York", "new-york-city-ny", root)
    getter = fetch or collector.fetch_bytes
    results = []
    for family, url in nyc_amlegal_bulk_xml.NYC_BULK_FAMILIES.items():
        document = f"{family}.zip"
        try:
            parsed = nyc_amlegal_bulk_xml.parse_bulk_zip(getter(url), family, url)
            rows = [{**_trail_to_fields(x["hierarchy"]), "section_number": x["section_heading"],
                     "section_name": x["section_heading"], "full_text": x["text"],
                     "source_url": x["source_url"]} for x in parsed]
            results.append(collector.write(rows, f"New York City {family.replace('_', ' ').title()}", family))
            collector.mark(document)
        except Exception as exc:  # checkpoint lets later families finish independently
            collector.mark(document, error=str(exc)); raise
    return results


def collect_openlaw_xml(root: Path, *, jurisdiction: str, slug: str, xml_files: Iterable[Path],
                        parser: Callable[[str, str], list[dict]], code_name: str) -> dict:
    """Collect a pinned, already-downloaded Open Law XML tree (San Mateo/Baltimore)."""
    collector = SpecialCollector(jurisdiction, slug, root)
    all_rows: list[dict] = []
    for path in xml_files:
        document = str(path)
        try:
            local_path = Path(path).resolve()
            for row in parser(local_path.read_text(encoding="utf-8"), local_path.as_uri()):
                hierarchy = _trail_to_fields(row.pop("hierarchy", ""))
                all_rows.append({**hierarchy, **row})
            collector.mark(document)
        except Exception as exc:
            collector.mark(document, error=str(exc)); raise
    return collector.write(all_rows, code_name)


def collect_san_mateo_bulk(root: Path) -> dict:
    """Acquire and parse the publisher-designated pinned San Mateo XML tree.

    The Law Library asks users not to crawl its web pages.  This uses the
    public repository snapshot named by :mod:`openlaw_bulk_xml`, caches the
    archive, and assigns each row the immutable raw-file source URL.
    """
    collector = SpecialCollector("San Mateo, California", "san-mateo-ca", root)
    archive_url = (f"https://github.com/cityofsanmateo/law-xml/archive/"
                   f"{openlaw_bulk_xml.PINNED_COMMIT}.zip")
    payload = collector.fetch_bytes(archive_url)
    prefix = f"law-xml-{openlaw_bulk_xml.PINNED_COMMIT}/{openlaw_bulk_xml.BULK_PATH}/"
    rows: list[dict] = []
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = [name for name in archive.namelist()
                 if name.startswith(prefix) and name.lower().endswith(".xml")]
        if not names:
            raise RuntimeError("Pinned San Mateo archive had no code XML files")
        for name in sorted(names):
            repository_path = name.split("/", 1)[1]
            raw_url = (f"https://raw.githubusercontent.com/cityofsanmateo/law-xml/"
                       f"{openlaw_bulk_xml.PINNED_COMMIT}/{repository_path}")
            for row in openlaw_bulk_xml.parse_title_xml(archive.read(name).decode("utf-8"), raw_url):
                rows.append(row)
    collector.mark(archive_url)
    return collector.write(rows, "San Mateo Municipal Code")


def collect_civicplus_pdfs(root: Path, *, jurisdiction: str, slug: str, documents: Iterable[dict], code_name: str,
                           fetch: Callable[[str], bytes] | None = None) -> dict:
    """Download discovered official CivicPlus assets/DocumentCenter PDFs and split sections."""
    collector = SpecialCollector(jurisdiction, slug, root)
    getter = fetch or collector.fetch_bytes
    all_rows: list[dict] = []
    for doc in documents:
        url, label = doc["url"], doc.get("label", "")
        try:
            pdf_path = collector.cache / (hashlib.sha256(url.encode()).hexdigest() + ".pdf")
            if not pdf_path.exists(): pdf_path.write_bytes(getter(url))
            for row in civicplus_assets.parse_pdf_sections(_pdf_text(pdf_path)):
                all_rows.append({"chapter": label, "source_url": url, **row})
            collector.mark(url)
        except Exception as exc:
            collector.mark(url, error=str(exc)); raise
    return collector.write(all_rows, code_name)


def collect_portland_me(root: Path, landing_url: str = "https://portlandmaine.gov/city-code", *,
                        fetch_text: Callable[[str], str] | None = None,
                        fetch_bytes: Callable[[str], bytes] | None = None) -> dict:
    """Rediscover Portland's official CivicPlus collection on every run."""
    collector = SpecialCollector("Portland, Maine", "portland-me", root)
    text_getter = fetch_text or collector.fetch_text
    ids = civicplus_assets.parse_portland_asset_ids(text_getter(landing_url))
    if not ids:
        raise RuntimeError("Portland City Code widget contained no document assets")
    documents = [{"label": f"Portland City Code document {i + 1}",
                  "url": civicplus_assets.asset_url(asset_id)} for i, asset_id in enumerate(ids)]
    return collect_civicplus_pdfs(root, jurisdiction="Portland, Maine", slug="portland-me",
                                  documents=documents, code_name="Portland City Code", fetch=fetch_bytes)


def collect_rockland_me(root: Path, landing_url: str = "https://www.rocklandmaine.gov/288/Charter-Code-Ordinances", *,
                        fetch_text: Callable[[str], str] | None = None,
                        fetch_bytes: Callable[[str], bytes] | None = None) -> dict:
    """Discover every Rockland Code/Charter document from its official index."""
    collector = SpecialCollector("Rockland, Maine", "rockland-me", root)
    text_getter = fetch_text or collector.fetch_text
    documents = civicplus_assets.parse_rockland_index(text_getter(landing_url), landing_url)
    if not documents:
        raise RuntimeError("Rockland code index contained no DocumentCenter chapters")
    return collect_civicplus_pdfs(root, jurisdiction="Rockland, Maine", slug="rockland-me",
                                  documents=documents, code_name="Rockland Code of Ordinances", fetch=fetch_bytes)


def collect_king_county(root: Path, landing_url: str, *, fetch: Callable[[str], str] | None = None) -> dict:
    collector = SpecialCollector("King County, Washington", "king-county-wa", root)
    getter = fetch or collector.fetch_text
    all_rows: list[dict] = []
    for title in kingcounty_code.parse_landing_titles(getter(landing_url), landing_url):
        try:
            for row in kingcounty_code.parse_title_sections(getter(title["url"]), title["url"]):
                all_rows.append({"title": title["label"], **row})
            collector.mark(title["url"])
        except Exception as exc:
            collector.mark(title["url"], error=str(exc)); raise
    return collector.write(all_rows, "King County Code")


def collect_san_diego(root: Path, chapter_urls: Iterable[str], *, fetch: Callable[[str], str] | None = None,
                       fetch_bytes: Callable[[str], bytes] | None = None) -> dict:
    collector = SpecialCollector("San Diego, California", "san-diego-ca", root)
    text_getter, bytes_getter = fetch or collector.fetch_text, fetch_bytes or collector.fetch_bytes
    all_rows: list[dict] = []
    for chapter_url in chapter_urls:
        for doc in san_diego_pdf.parse_chapter_toc_html(text_getter(chapter_url), chapter_url):
            url = doc["source_url"]
            try:
                pdf_path = collector.cache / (hashlib.sha256(url.encode()).hexdigest() + ".pdf")
                if not pdf_path.exists(): pdf_path.write_bytes(bytes_getter(url))
                for row in san_diego_pdf.split_pdf_sections(san_diego_pdf.extract_pdf_text(pdf_path), url):
                    all_rows.append({"chapter": doc["label"], **row})
                collector.mark(url)
            except Exception as exc:
                collector.mark(url, error=str(exc)); raise
    return collector.write(all_rows, "San Diego Municipal Code")


def collect_san_diego_all(root: Path, portal_url: str = san_diego_pdf.PORTAL_ROOT) -> dict:
    """Discover every current City Clerk chapter and collect its division PDFs."""
    collector = SpecialCollector("San Diego, California", "san-diego-ca", root)
    chapters = san_diego_pdf.discover_chapter_urls(collector.fetch_text(portal_url), portal_url)
    if not chapters:
        raise RuntimeError("San Diego Municipal Code portal had no chapter links")
    return collect_san_diego(root, chapters)


def _pdf_text(path: Path) -> str:
    from pypdf import PdfReader
    return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
