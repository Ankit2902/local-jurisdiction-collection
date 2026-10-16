"""Full collectors for browser-rendered municipal-code vendors.

The validation adapters in this package deliberately contain only parsers.  This
module is the production layer around them: it supplies browser-capable cached
transport, checkpoints every discovered page, and emits the 16-column municipal
provision schema.  It is intentionally not registered in ``municipal_code_scraper``
until batch orchestration is enabled.

The transport reuses the reviewed Chrome DevTools implementation from the
statutory-code project.  A visible Chromium window is opened on first use; an
operator can complete a publisher's normal verification challenge there.  This
is not a stealth or challenge-bypass mechanism.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Iterable, Protocol
from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup

from . import american_legal, codepublishing, codepublishing_legacy, ecode360, gridics_codehub, municipal_codes

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
SCHEMA = [
    "jurisdiction", "code_name", "division", "title", "subtitle", "chapter",
    "subchapter", "article", "part", "subpart", "section_number", "section_name",
    "citation", "full_text", "source_url", "scrape_date",
]
HIERARCHY = ("code_name", "division", "title", "subtitle", "chapter", "subchapter", "article", "part", "subpart")
LEVEL = {x: x for x in HIERARCHY}
# Some vendor shells label a top-level publication simply "Code".  It is a
# code-name ancestor, not a schema field named ``code``.
LEVEL["code"] = "code_name"


class RenderedTransport(Protocol):
    """A cache-aware source of browser-rendered HTML."""
    def get(self, url: str) -> str: ...
    def checkpoint(self, state: dict) -> None: ...
    def stats(self) -> dict: ...


class FixtureTransport:
    """In-memory rendered DOM transport used for deterministic collector tests."""
    def __init__(self, pages: dict[str, str]):
        self.pages, self.requested = pages, []
    def get(self, url: str) -> str:
        self.requested.append(url)
        if url not in self.pages:
            raise RuntimeError("fixture has no rendered DOM for %s" % url)
        return self.pages[url]
    def checkpoint(self, state: dict) -> None:  # pragma: no cover - test double
        return None
    def stats(self) -> dict:
        return {"fixture_fetches": len(self.requested)}


class ChromeRenderedTransport:
    """Cached visible-Chromium transport shared with legal-code-batch.

    The legal collector's Fetcher owns the CDP websocket implementation and
    cache/index behavior.  Importing it here avoids a divergent browser-control
    stack while keeping municipal collection isolated from its dispatcher.
    """
    def __init__(self, cache_dir: Path, *, debug_port: int = 9237, timeout: int = 90,
                 delay_min: float = 1.0, delay_max: float = 2.5):
        legal = PROJECT_ROOT / "legal-code-batch" / "legal_code_scraper.py"
        spec = importlib.util.spec_from_file_location("complisolv_legal_browser", legal)
        if not spec or not spec.loader:
            raise RuntimeError("Cannot load reviewed legal-code browser transport: %s" % legal)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        self._fetcher = module.Fetcher(str(cache_dir), delay_min, delay_max, 3, 60, 10000, 0,
                                       browser_fallback=True, browser_timeout=timeout,
                                       browser_debug_port=debug_port, browser_first=True,
                                       browser_reuse_tab=True, browser_cookie_sync=True)
        # Parallel jurisdiction samples must not contend for Chrome's profile
        # lock.  Keep the shared HTTP/cache index, but give each debugging
        # endpoint its own disposable browser profile.
        self._fetcher.browser_profile_dir = str(cache_dir / ("_browser_profile_%d" % debug_port))
        self._checkpoint_path = cache_dir / "collection-checkpoint.json"
    def get(self, url: str) -> str:
        # CodeHUB is an SPA whose document shell is a perfectly valid 200
        # response.  The statutory Fetcher intentionally accepts that shell
        # as "unknown" immediately; for a municipal CodeHUB route we instead
        # wait for the visible section headings that make the page collectible.
        # Do this before consulting its cache so an early shell is never
        # mistaken for a rendered route on a later resume.
        if "codehub.gridics.com" in url:
            return self._get_gridics_rendered(url)
        return self._fetcher.get(url, checkpoint=lambda: None)

    def _get_gridics_rendered(self, url: str) -> str:
        fetcher = self._fetcher
        if not fetcher._ensure_visible_browser():
            raise RuntimeError("Could not start visible Chromium for Gridics CodeHUB")
        target = ws = None
        close_after = True
        try:
            target, ws, close_after = fetcher._browser_connection()
            ws.call("Page.navigate", {"url": url})
            deadline = time.time() + fetcher.browser_timeout
            expression = (
                "(() => { const root=document.querySelector('#root');"
                " const headings=[...document.querySelectorAll('h2,h3,h4')]"
                ".map(x=>x.innerText.trim()).filter(Boolean);"
                " return {html:document.documentElement.outerHTML, headings,"
                " ready:document.readyState, text:(root?root.innerText:document.body.innerText)}; })()"
            )
            while time.time() < deadline:
                time.sleep(1)
                result = ws.call("Runtime.evaluate", {"expression": expression,
                                                        "returnByValue": True,
                                                        "awaitPromise": True})
                value = result.get("result", {}).get("value", {}) or {}
                headings = value.get("headings", []) or []
                # A section route must render a legal section number; TOC
                # routes at least render a TITLE heading.  Both are stronger
                # readiness signals than document.readyState for this SPA.
                if any(re.match(r"^\d+(?:\.\d+)+\s+", heading) or
                           re.match(r"^TITLE\s+\d+", heading, re.I)
                           for heading in headings):
                    html = value.get("html", "")
                    fetcher._cache_browser_html(url, html)
                    fetcher.browser_fetches += 1
                    fetcher._sync_browser_cookies(ws, url)
                    return html
            sample = (value.get("text", "") if 'value' in locals() else "")[:300]
            raise RuntimeError("Gridics CodeHUB did not render a Title/section route before timeout: %r" % sample)
        finally:
            if ws and close_after:
                ws.close()
            if target and close_after:
                fetcher._close_browser_tab(target.get("id"))
    def checkpoint(self, state: dict) -> None:
        self._checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._checkpoint_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, indent=2), encoding="utf-8")
        os.replace(temporary, self._checkpoint_path)
    def stats(self) -> dict:
        return {"network_fetches": self._fetcher.fetches, "cached_fetches": self._fetcher.from_cache,
                "browser_fetches": self._fetcher.browser_fetches,
                "browser_reused_tab_fetches": self._fetcher.browser_reused_tab_fetches}


def _clean(value: str) -> str:
    return " ".join((value or "").split())


def _absolute(base: str, href: str, keep_fragment: bool = False) -> str | None:
    href = (href or "").strip()
    if not href or href.startswith(("javascript:", "mailto:")):
        return None
    value = urljoin(base, href)
    return value if keep_fragment else urldefrag(value)[0]


def _hierarchy(labels: Iterable[str]) -> dict[str, str]:
    result = {name: "" for name in HIERARCHY}
    for raw in labels:
        label = _clean(raw)
        hit = re.match(r"^(code|division|title|subtitle|chapter|subchapter|article|part|subpart)\b", label, re.I)
        if hit:
            field = LEVEL[hit.group(1).lower()]
            result[field] = "Code of Ordinances" if label.lower() in {"code", "code code"} else label
        elif re.search(r"\b(?:code|codes|charter)\b", label, re.I):
            # Vendor landing pages often name a publication as "Zoning Code"
            # or "Home Rule Charter" instead of prefixing it with "Code".
            # It is still the family name and should override the generic
            # Municipal Code placeholder inherited from the jurisdiction root.
            result["code_name"] = re.sub(r"^(?:link|code)\s+", "", label, flags=re.I)
    return result


def _parts(label: str) -> tuple[str, str]:
    label = _clean(label)
    hit = re.match(r"^(?:§\s*)?((?:sec(?:tion)?\.?\s*)?[A-Za-z0-9][A-Za-z0-9._-]*)\s*[-:—–]*\s*(.*)$", label, re.I)
    if not hit:
        return "", label
    number = re.sub(r"^sec(?:tion)?\.?\s*", "", hit.group(1), flags=re.I)
    return number, hit.group(2).strip() or label


@dataclass(frozen=True)
class Publication:
    slug: str
    jurisdiction: str
    adapter: str
    root_url: str
    code_name: str = "Municipal Code"
    max_pages: int = 50000


class BrowserVendorCollector:
    """Resumable rendered-DOM collector for one mapped publication."""
    def __init__(self, publication: Publication, transport: RenderedTransport, work_dir: Path):
        self.publication, self.transport, self.work_dir = publication, transport, work_dir
        self.checkpoint_path = work_dir / "checkpoint.json"
        self.rows: list[dict[str, str]] = []
        self.seen_sections: set[str] = set()

    def _state(self, pending: list[tuple[str, list[str]]], visited: set[str]) -> dict:
        return {"version": 1, "slug": self.publication.slug, "pending": pending, "visited": sorted(visited),
                "rows": self.rows, "seen_sections": sorted(self.seen_sections)}

    def _save(self, pending: list[tuple[str, list[str]]], visited: set[str]) -> None:
        self.work_dir.mkdir(parents=True, exist_ok=True)
        state = self._state(pending, visited)
        temp = self.checkpoint_path.with_suffix(".tmp")
        temp.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        os.replace(temp, self.checkpoint_path)
        self.transport.checkpoint(state)

    def _load(self) -> tuple[list[tuple[str, list[str]]], set[str]]:
        if not self.checkpoint_path.exists():
            return [(self.publication.root_url, [self.publication.code_name])], set()
        state = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
        if state.get("slug") != self.publication.slug:
            raise RuntimeError("Checkpoint belongs to another publication")
        self.rows = list(state.get("rows", [])); self.seen_sections = set(state.get("seen_sections", []))
        return [(u, list(a)) for u, a in state.get("pending", [])], set(state.get("visited", []))

    def _allowed(self, url: str) -> bool:
        root, candidate = urlparse(self.publication.root_url), urlparse(url)
        if candidate.netloc != root.netloc:
            return False
        if self.publication.adapter == "american_legal":
            product = root.path.split("/codes/", 1)[-1].split("/", 1)[0]
            marker = "/codes/%s/latest/" % product
            if candidate.path.rstrip("/") == root.path.rstrip("/"):
                return True
            remainder = candidate.path.split(marker, 1)[-1] if marker in candidate.path else ""
            return bool(re.fullmatch(r"[^/]+/0-0-0-\d+", remainder))
        if self.publication.adapter == "municipal_codes":
            base = root.path.rstrip("/")
            return candidate.path == base or candidate.path.startswith(base + "/")
        if self.publication.adapter == "ecode360":
            # General Code pages use stable numeric document IDs.  The site
            # shell also links account, help, law-ledger, and vendor terms
            # routes; following those is outside the publication and can
            # trigger needless bot challenges.  Keep only the publication
            # root and numeric code-document routes.
            publication_root = root.path.rstrip("/")
            code_root = publication_root[:-5] if publication_root.endswith("/home") else publication_root
            return candidate.path.rstrip("/") in {publication_root, code_root} or bool(
                re.fullmatch(r"/\d+/?", candidate.path)
            )
        return True

    def _links(self, html: str, url: str) -> list[tuple[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        # Gridics and older General Code/Code Publishing publications use
        # client-side hash routes; removing fragments would collapse their
        # entire TOC to the root page.
        keep_fragment = self.publication.adapter in {"gridics_codehub", "codepublishing_legacy"}
        links, seen = [], set()
        for anchor in soup.select("main a[href], article a[href], nav a[href], a[href]"):
            target = _absolute(url, str(anchor.get("href") or ""), keep_fragment)
            label = _clean(anchor.get_text(" ", strip=True))
            if not target or not label or target in seen or not self._allowed(target):
                continue
            if self.publication.adapter == "ecode360":
                at_publication_root = url.rstrip("/") == self.publication.root_url.rstrip("/")
                top_level_publication = at_publication_root and bool(
                    re.search(r"\b(?:code|charter)\b", label, re.I)
                )
                if (label not in {"Municipal Code", "Tables"} and
                        not top_level_publication and
                        not re.match(r"^(?:(?:Title|Chapter|Article|Part|Division|Appendix|Table)\b|§)", label, re.I)):
                    continue
            if target.lower().endswith((".pdf", ".doc", ".zip")):
                continue
            seen.add(target); links.append((target, label))
        if self.publication.adapter == "american_legal":
            at_overview = url.rstrip("/") == self.publication.root_url.rstrip("/")
            if at_overview:
                # A multi-code overview repeats every descendant in its global
                # navigation.  Start with named code/charter family roots so
                # descendants retain the right family and are not enqueued
                # once from the unscoped overview and again from that family.
                families = [(target, label) for target, label in links
                            if re.search(r"\b(?:code|charter)\b", label, re.I)]
                if families:
                    return families
            else:
                marker = "/latest/"
                current_tail = urlparse(url).path.split(marker, 1)[-1]
                current_family = current_tail.split("/", 1)[0]
                links = [(target, label) for target, label in links
                         if urlparse(target).path.split(marker, 1)[-1].split("/", 1)[0]
                         == current_family]
        return links

    def _add(self, label: str, text: str, url: str, ancestors: list[str], section_number: str = "", section_name: str = "") -> None:
        citation = _clean(label)
        # One rendered eCode360 chapter contains several provisions, and every
        # child section URL renders that same chapter bundle.  The citation is
        # the stable provision identity; including the currently rendered URL
        # would duplicate the whole bundle once per child link.
        key = citation if self.publication.adapter == "ecode360" else url + "\x1f" + citation
        if not text or key in self.seen_sections:
            return
        number, name = (section_number, section_name) if section_number else _parts(label)
        row = {field: "" for field in SCHEMA}
        row.update({"jurisdiction": self.publication.jurisdiction,
            "code_name": self.publication.code_name})
        row.update(_hierarchy(ancestors)); row.update({"section_number": number, "section_name": name,
            "citation": citation, "full_text": text, "source_url": url, "scrape_date": date.today().isoformat()})
        self.rows.append(row); self.seen_sections.add(key)

    def _sections(self, html: str, url: str, ancestors: list[str]) -> None:
        adapter = self.publication.adapter
        if adapter == "codepublishing":
            for item in codepublishing.parse_chapter_sections(html, url):
                self._add(item["label"], item["full_text"], item["source_url"], ancestors, item["section_number"], item["section_name"])
            return
        if adapter == "codepublishing_legacy":
            for item in codepublishing_legacy.parse_chapter_sections(html, url):
                self._add(item["label"], item["full_text"], item["source_url"], ancestors, item["section_number"], item["section_name"])
            return
        if adapter == "gridics_codehub":
            for item in gridics_codehub.parse_sections_html(html):
                self._add(item["section_number"] + " " + item["section_name"], item["full_text"], url,
                          ancestors + [item["title"], item["chapter"]], item["section_number"], item["section_name"])
            return
        if adapter == "american_legal":
            text = american_legal.parse_section_html(html)
        elif adapter == "municipal_codes":
            parsed = municipal_codes.parse_sections_html(html, url)
            for item in parsed:
                self._add(item["label"], item["full_text"], item["source_url"], ancestors,
                          item["section_number"], item["section_name"])
            # Older ICC pages may expose one provision as a simple heading and
            # body rather than a Section card.  Do not fall back on a TOC-only
            # page, though: its navigation text is not an enactment.
            soup = BeautifulSoup(html, "html.parser")
            text = municipal_codes.parse_section_text(html) if not parsed and soup.select_one("main h1, main h2, main h3, main h4, main h5, main h6") else ""
        elif adapter == "ecode360":
            parsed = ecode360.parse_rendered_sections(html)
            for item in parsed:
                self._add(item["label"], item["full_text"], url, ancestors)
            # Root/title pages are navigation documents, not provisions.  A
            # genuine rendered code page is handled by parse_rendered_sections;
            # do not fall back to storing a TOC or cookie dialog as one section.
            text = ""
        elif adapter == "elaws":
            soup = BeautifulSoup(html, "html.parser"); node = soup.select_one(".Daly.City_content, main, article")
            text = node.get_text("\n", strip=True) if node else ""
        else:
            raise RuntimeError("Unsupported browser vendor adapter: %s" % adapter)
        if text:
            soup = BeautifulSoup(html, "html.parser")
            scope = soup.select_one("#curr-section") if adapter == "american_legal" else soup
            heading = scope.select_one("h1, h2, h3, h4, h5, h6") if scope else None
            self._add(_clean(heading.get_text(" ", strip=True)) if heading else url.rsplit("/", 1)[-1], text, url, ancestors)

    def collect(self, *, max_pages: int | None = None) -> list[dict[str, str]]:
        pending, visited = self._load(); limit = max_pages or self.publication.max_pages
        while pending:
            if len(visited) >= limit:
                self._save(pending, visited)
                raise RuntimeError("Page safety limit reached (%d); resume with a reviewed larger limit." % limit)
            url, ancestors = pending.pop(0)
            if url in visited:
                continue
            html = self.transport.get(url); visited.add(url)
            self._sections(html, url, ancestors)
            if self.publication.adapter == "ecode360":
                known_numbers = {row["section_number"] for row in self.rows if row["section_number"]}
                # A chapter page emits all of its provisions at once.  Remove
                # already-covered child section URLs that an earlier title TOC
                # placed in the queue, while retaining chapter/container URLs.
                pending = [(queued_url, queued_ancestors) for queued_url, queued_ancestors in pending
                           if _parts(queued_ancestors[-1] if queued_ancestors else "")[0]
                           not in known_numbers]
            queued = {queued_url for queued_url, _ in pending}
            known_numbers = {row["section_number"] for row in self.rows}
            for target, label in self._links(html, url):
                if (self.publication.adapter == "ecode360" and
                        _parts(label)[0] in known_numbers):
                    continue
                if target not in visited and target not in queued:
                    pending.append((target, ancestors + [label]))
                    queued.add(target)
            self._save(pending, visited)
        return self.rows

    def write_outputs(self, output_dir: Path) -> dict:
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / (self.publication.slug + "-municipal-fulltext.json")
        csv_path = output_dir / (self.publication.slug + "-municipal-fulltext.csv")
        rows = [{field: row.get(field, "") for field in SCHEMA} for row in self.rows]
        metadata = {"jurisdiction": self.publication.jurisdiction, "adapter": self.publication.adapter,
                    "root_url": self.publication.root_url, "total_provisions": len(rows),
                    "full_text_complete": sum(bool(row["full_text"]) for row in rows), **self.transport.stats()}
        json_path.write_text(json.dumps({"metadata": metadata, "provisions": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
        with csv_path.open("w", newline="", encoding="utf-8-sig") as out:
            writer = csv.DictWriter(out, fieldnames=SCHEMA); writer.writeheader(); writer.writerows(rows)
        return {"metadata": metadata, "json": str(json_path), "csv": str(csv_path)}


def publication_from_registry(slug: str, jurisdiction: str, entry: dict) -> Publication:
    """Build an isolated collector target from an already-reviewed registry entry."""
    adapter = entry["adapter"]
    if adapter == "ca_bespoke_adapters" and "elaws.us" in entry["root_url"]:
        adapter = "elaws"
    return Publication(slug, jurisdiction, adapter, entry["root_url"])
