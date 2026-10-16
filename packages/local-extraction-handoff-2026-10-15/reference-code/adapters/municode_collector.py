"""Resumable full-code collector for Municode's public Library API.

This is deliberately separate from the command dispatcher while the provider
collectors are being completed.  It writes the municipal 16-column interchange
schema and a small, auditable run manifest.  ``--limit`` is useful for a cheap
live acceptance sample; omit it to collect every section-shaped leaf.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
from datetime import date
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

if __package__ in (None, ""):
    # Also support the documented direct-script invocation from the project root.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adapters import municode

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ["jurisdiction", "code_name", "division", "title", "subtitle", "chapter",
          "subchapter", "article", "part", "subpart", "section_number", "section_name",
          "citation", "full_text", "source_url", "scrape_date"]
HIERARCHY = ("code_name", "division", "title", "subtitle", "chapter", "subchapter", "article", "part", "subpart")
LEVEL_RE = re.compile(r"^\s*(code|division|title|subtitle|chapter|subchapter|article|part|subpart)\b", re.I)
SECTION_RE = municode.SECTION_RE


def _atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def _cache_name(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest() + ".json"


def _canonical_url(root_url: str, node_id: str) -> str:
    parsed = urlparse(root_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["nodeId"] = node_id
    return urlunparse(parsed._replace(query=urlencode(query)))


def _section_parts(heading: str) -> tuple[str, str]:
    clean = re.sub(r"\s+", " ", heading).strip()
    match = re.match(r"^(?:§\s*)?(?:sec(?:tion)?\.?\s*)?([\d][\w.\-]*)\s*[-–—:]?\s*(.*)$", clean, re.I)
    return (match.group(1), match.group(2).strip() or clean) if match else ("", clean)


def _hierarchy(ancestors: list[str], code_name: str) -> dict[str, str]:
    row = {key: "" for key in HIERARCHY}
    row["code_name"] = code_name
    for label in ancestors:
        match = LEVEL_RE.match(label)
        if match:
            row[match.group(1).lower()] = label
    # Municode headings often say "ART." / "CH." instead of words.  Preserve
    # every ancestor in the closest available fields instead of discarding it.
    unclassified = [x for x in ancestors if not LEVEL_RE.match(x)]
    for field, label in zip(("title", "chapter", "article", "part", "subpart"), unclassified):
        if not row[field]:
            row[field] = label
    return row


def leaf_paths(node: dict[str, Any], ancestors: list[str] | None = None) -> list[tuple[dict[str, Any], list[str]]]:
    """Flatten a fullTree response, retaining the hierarchy for each leaf."""
    ancestors = list(ancestors or [])
    children = node.get("Children") or []
    if not children:
        return [(node, ancestors)]
    next_ancestors = ancestors + ([node.get("Heading", "").strip()] if node.get("Heading") else [])
    result: list[tuple[dict[str, Any], list[str]]] = []
    for child in children:
        result.extend(leaf_paths(child, next_ancestors))
    return result


class MunicodeCollector:
    def __init__(self, slug: str, jurisdiction: str, root_url: str, output_root: Path | None = None,
                 delay: float = 0.35, timeout: int = 45) -> None:
        self.slug, self.jurisdiction, self.root_url = slug, jurisdiction, root_url
        self.output_root = output_root or ROOT / "output" / slug
        self.cache_dir = self.output_root / "cache"
        self.delay, self.timeout = delay, timeout
        self.session = requests.Session()
        self.session.headers.update(municode.HEADERS)
        self.network_fetches = self.cached_fetches = 0

    def _api(self, path: str, **params: Any) -> dict[str, Any]:
        url = municode.BASE + path + "?" + urlencode(params)
        path_on_disk = self.cache_dir / _cache_name(url)
        if path_on_disk.exists():
            self.cached_fetches += 1
            return json.loads(path_on_disk.read_text(encoding="utf-8"))
        response = self.session.get(municode.BASE + path, params=params, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        path_on_disk.parent.mkdir(parents=True, exist_ok=True)
        path_on_disk.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        self.network_fetches += 1
        if self.delay:
            time.sleep(self.delay)
        return payload

    def resolve(self) -> tuple[dict[str, Any], dict[str, Any]]:
        state, client_name = municode._client_from_root(self.root_url)
        clients = self._api("/api/Clients/keyword", keyword=client_name)
        matches = [c for c in clients if c.get("ClientName", "").casefold() == client_name.casefold()
                   and c.get("State", {}).get("StateAbbreviation") == state]
        if len(matches) != 1:
            raise RuntimeError("expected one %s Municode client for %r; found %d" % (state, client_name, len(matches)))
        client = matches[0]
        publications = self._api("/api/ClientContent/%s" % client["ClientID"]).get("codes", [])
        for preferred in ("code of ordinances", "municipal code", "city code"):
            for publication in publications:
                if publication.get("productName", "").casefold() == preferred:
                    return client, publication
        raise RuntimeError("No general Municode code publication found")

    def enumerate(self) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        client, publication = self.resolve()
        product_id = int(publication["productId"])
        tree = self._api("/api/codesToc/fullTree/latest", productId=product_id, nodeId=product_id)
        code_name = publication.get("productName") or "Municipal Code"
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for leaf, ancestors in leaf_paths(tree):
            heading, node_id = (leaf.get("Heading") or "").strip(), str(leaf.get("Id") or "")
            if not node_id or node_id in seen or not SECTION_RE.match(heading):
                continue
            seen.add(node_id)
            number, name = _section_parts(heading)
            row = {key: "" for key in SCHEMA}
            row.update(_hierarchy(ancestors, code_name))
            row.update({"jurisdiction": self.jurisdiction, "section_number": number, "section_name": name,
                        "citation": heading, "source_url": _canonical_url(self.root_url, node_id),
                        "scrape_date": date.today().isoformat(), "_node_id": node_id})
            rows.append(row)
        if not rows:
            raise RuntimeError("TOC had no section-shaped leaves")
        return {"client": client, "publication": publication, "product_id": product_id}, rows

    def collect(self, limit: int | None = None, checkpoint_every: int = 25) -> dict[str, Any]:
        resolved, rows = self.enumerate()
        total_toc_sections = len(rows)
        if limit is not None:
            rows = rows[:limit]
        checkpoint = self.output_root / (self.slug + "-municipal-sample-checkpoint.json")
        # A checkpoint is intentionally keyed by stable provider node ID, while
        # the API cache makes an interrupted retry avoid repeat HTTP calls.
        if checkpoint.exists():
            previous = json.loads(checkpoint.read_text(encoding="utf-8"))
            prior_text = {x.get("_node_id"): x.get("full_text", "") for x in previous.get("rows", [])}
            for row in rows:
                row["full_text"] = prior_text.get(row["_node_id"], row["full_text"])
        product_id = resolved["product_id"]
        for index, row in enumerate(rows, 1):
            if not row["full_text"]:
                payload = self._api("/api/codesContent", productId=product_id, nodeId=row["_node_id"])
                row["full_text"] = municode.text_from_docs(payload.get("Docs") or [], row["_node_id"])
            if index % checkpoint_every == 0:
                _atomic(checkpoint, {"completed": index, "rows": rows})
        clean = [{key: row.get(key, "") for key in SCHEMA} for row in rows]
        self.output_root.mkdir(parents=True, exist_ok=True)
        stem = self.slug + "-municipal-" + ("sample" if limit is not None else "fulltext")
        json_path, csv_path = self.output_root / (stem + ".json"), self.output_root / (stem + ".csv")
        metadata = {"jurisdiction": self.jurisdiction, "slug": self.slug, "source_platform": "municode",
                    "root_url": self.root_url, "product_id": product_id,
                    "publication": resolved["publication"].get("productName"), "total_toc_sections": total_toc_sections,
                    "collected_sections": len(clean), "full_text_complete": sum(bool(x["full_text"]) for x in clean),
                    "network_fetches": self.network_fetches, "cached_fetches": self.cached_fetches,
                    "scrape_date": date.today().isoformat()}
        _atomic(json_path, {"metadata": metadata, "provisions": clean})
        with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=SCHEMA); writer.writeheader(); writer.writerows(clean)
        manifest = {"status": "sample-complete" if limit is not None else "full-collection-complete", "metadata": metadata,
                    "output_json": str(json_path), "output_csv": str(csv_path),
                    "representative_source_urls": [x["source_url"] for x in clean[:3]],
                    "empty_text_urls": [x["source_url"] for x in clean if not x["full_text"]],
                    "schema": SCHEMA}
        _atomic(self.output_root / (self.slug + "-municode-collector-manifest.json"), manifest)
        if checkpoint.exists():
            checkpoint.unlink()
        return manifest


def _jurisdiction_name(slug: str) -> str:
    import csv as _csv
    with (ROOT / "data" / "local-jurisdictions.csv").open(encoding="utf-8-sig", newline="") as handle:
        for row in _csv.DictReader(handle):
            if row["slug"] == slug:
                return row["jurisdiction"]
    return slug


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect a Municode local code")
    parser.add_argument("--slug", required=True); parser.add_argument("--root-url", required=True)
    parser.add_argument("--limit", type=int, help="collect only N sections as a live acceptance sample")
    parser.add_argument("--output-root", type=Path); parser.add_argument("--delay", type=float, default=.35)
    args = parser.parse_args()
    collector = MunicodeCollector(args.slug, _jurisdiction_name(args.slug), args.root_url, args.output_root, args.delay)
    print(json.dumps(collector.collect(args.limit), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
