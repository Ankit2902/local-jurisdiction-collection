"""Small, source-specific pilots for California municipal-code publishers.

This module intentionally does not modify the shared runner or registry.  Its
``validate`` entry point makes a short, read-only request sequence and returns
evidence suitable for a per-jurisdiction validation manifest.  Only the Daly
City eLaws pilot is currently approved for an HTML scraper: the other sources
are retained as guarded discovery adapters until their browser-rendered or
anti-bot responses can be inspected by an operator.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "daly-city-elaws-section.html"
HEADERS = {
    "User-Agent": "CompliSolv municipal-code validation bot/0.1",
    "Accept-Language": "en-US,en;q=0.9",
}

# Roots and representative pages were verified on 2026-08-28.  A 403 is not
# treated as a parsable page: it explicitly leaves the source unvalidated.
SOURCES = {
    "berkeley": {
        "root": "https://berkeley.municipal.codes/",
        "toc": "https://berkeley.municipal.codes/BMC/1",
        "section": "https://berkeley.municipal.codes/BMC/1.01.010",
        "platform": "ICC Code Solutions / municipal.codes",
    },
    "daly-city": {
        "root": "https://dalycity-ca.elaws.us/code/coor",
        "toc": "https://dalycity-ca.elaws.us/code/coor_title1_ch1.01",
        "section": "https://dalycity-ca.elaws.us/code/coor_title1_ch1.01_sec1.01.010",
        "platform": "eLaws",
    },
    "el-cerrito": {
        "root": "https://library.municode.com/ca/el_cerrito/codes/code_of_ordinances",
        "toc": "https://library.municode.com/ca/el_cerrito/codes/code_of_ordinances",
        "section": "https://library.municode.com/ca/el_cerrito/codes/code_of_ordinances?nodeId=TIT4REFI_CH4.36COTA",
        "platform": "Municode",
    },
    "los-angeles": {
        "root": "https://codelibrary.amlegal.com/codes/los_angeles/latest/overview",
        "toc": "https://codelibrary.amlegal.com/codes/los_angeles/latest/lamc/0-0-0-422835",
        "section": "https://codelibrary.amlegal.com/codes/los_angeles/latest/lamc/0-0-0-107510",
        "platform": "American Legal Publishing",
    },
    "san-francisco": {
        "root": "https://codelibrary.amlegal.com/codes/san_francisco/latest/overview",
        "toc": "https://codelibrary.amlegal.com/codes/san_francisco/latest/sf_admin/0-0-0-2",
        "section": "https://codelibrary.amlegal.com/codes/san_francisco/latest/sf_admin/0-0-0-15",
        "platform": "American Legal Publishing",
    },
    "san-diego": {
        "root": "https://www.sandiego.gov/city-clerk/officialdocs/municipal-code",
        "toc": "https://docs.sandiego.gov/municode/MuniCodeChapter01/Ch01Art01Division01.pdf",
        "section": "https://docs.sandiego.gov/municode/MuniCodeChapter01/Ch01Art01Division02.pdf",
        "platform": "City-hosted PDF municipal code",
    },
}


def _fetch(url: str) -> requests.Response:
    return requests.get(url, headers=HEADERS, timeout=45)


def _blank(source: dict[str, str]) -> dict[str, Any]:
    return {
        "status": "needs_browser_validation",
        "root_url": source["root"],
        "toc_url": source["toc"],
        "section_url": source["section"],
        "toc_count_or_sample": 0,
        "section_text_length": 0,
        "checks": {"platform": source["platform"]},
        "errors": [],
    }


def parse_elaws_section(html: str) -> str:
    """Return enacted text, excluding the eLaws navigation and citation chrome."""
    soup = BeautifulSoup(html, "html.parser")
    node = soup.select_one(".Daly.City_content")
    return node.get_text("\n", strip=True) if node else ""


def parse_municipal_codes_sections(html: str) -> list[str]:
    """Extract rendered ICC Code Solutions section cards."""
    soup = BeautifulSoup(html, "html.parser")
    return [node.get_text("\n", strip=True) for node in soup.select("article.type-Section")]


def parse_amlegal_section(html: str) -> str:
    """Extract the live American Legal section container, without navigation."""
    soup = BeautifulSoup(html, "html.parser")
    node = soup.select_one("#curr-section")
    return node.get_text("\n", strip=True) if node else ""


def parse_municode_section(html: str) -> str:
    """Extract a CivicPlus Municode rendered section chunk."""
    soup = BeautifulSoup(html, "html.parser")
    node = soup.select_one("div.chunk[id^='c_']")
    return node.get_text("\n", strip=True) if node else ""


def _validate_daly_city(source: dict[str, str]) -> dict[str, Any]:
    result = _blank(source)
    result["checks"]["adapter"] = "eLaws link hierarchy + .Daly.City_content"
    try:
        root = _fetch(source["root"])
        result["checks"]["root_http_status"] = root.status_code
        if root.status_code != 200:
            result["errors"].append(f"root returned HTTP {root.status_code}")
            return result
        root_soup = BeautifulSoup(root.text, "html.parser")
        titles = [a.get("href") for a in root_soup.select("a[href]")
                  if a.get_text(" ", strip=True).startswith("Title ")]
        result["toc_count_or_sample"] = len(titles)
        if not titles:
            result["errors"].append("no title links found at root")
            return result
        title_url = urljoin(source["root"], titles[0])
        title = _fetch(title_url)
        result["checks"]["title_http_status"] = title.status_code
        title_soup = BeautifulSoup(title.text, "html.parser")
        chapters = [a.get("href") for a in title_soup.select("a[href]")
                    if "_ch" in (a.get("href") or "")]
        if not chapters:
            result["errors"].append("no chapter links found on representative title")
            return result
        chapter_url = urljoin(title_url, chapters[0])
        chapter = _fetch(chapter_url)
        result["checks"]["chapter_http_status"] = chapter.status_code
        chapter_soup = BeautifulSoup(chapter.text, "html.parser")
        sections = [a.get("href") for a in chapter_soup.select("a[href]")
                    if "_sec" in (a.get("href") or "")]
        if not sections:
            result["errors"].append("no section links found on representative chapter")
            return result
        section_url = urljoin(chapter_url, sections[0])
        page = _fetch(section_url)
        result["section_url"] = section_url
        result["checks"]["section_http_status"] = page.status_code
        text = parse_elaws_section(page.text) if page.status_code == 200 else ""
        result["section_text_length"] = len(text)
        result["checks"]["section_contains_enacted_phrase"] = "Pursuant to the provisions" in text
        if page.status_code == 200 and len(text) >= 100:
            result["status"] = "validated"
        else:
            result["errors"].append("representative section did not yield at least 100 characters")
    except requests.RequestException as exc:
        result["errors"].append(f"request failed: {exc}")
    return result


def validate(root_url: str) -> dict[str, Any]:
    """Validate the source identified by root_url; no bulk crawl is performed."""
    source = next((s for s in SOURCES.values() if s["root"].rstrip("/") == root_url.rstrip("/")), None)
    if source is None:
        raise ValueError(f"No California bespoke source is configured for {root_url}")
    if source["platform"] == "eLaws":
        return _validate_daly_city(source)
    result = _blank(source)
    try:
        response = _fetch(source["root"])
        result["checks"]["root_http_status"] = response.status_code
        if response.status_code == 200:
            result["errors"].append(
                "Root is reachable but this platform needs a browser/API traversal adapter and parser test."
            )
        else:
            result["errors"].append(
                f"Root returned HTTP {response.status_code}; do not infer a parser from an anti-bot response."
            )
    except requests.RequestException as exc:
        result["errors"].append(f"request failed: {exc}")
    return result


def fixture_test() -> dict[str, Any]:
    text = parse_elaws_section(FIXTURE.read_text(encoding="utf-8"))
    assert "Pursuant to the provisions" in text
    assert "eLaws" not in text
    municipal = parse_municipal_codes_sections((ROOT / "fixtures" / "berkeley-municipal-codes.html").read_text(encoding="utf-8"))
    assert len(municipal) == 1 and "Document adopted" in municipal[0]
    amlegal = parse_amlegal_section((ROOT / "fixtures" / "american-legal-section.html").read_text(encoding="utf-8"))
    assert "Short Title" in amlegal and "Navigation" not in amlegal
    municode = parse_municode_section((ROOT / "fixtures" / "el-cerrito-municode-section.html").read_text(encoding="utf-8"))
    assert "El Cerrito Municipal Code" in municode
    return {"fixture": str(FIXTURE), "section_text_length": len(text), "parser_tests": 4, "passed": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url")
    parser.add_argument("--fixture-test", action="store_true")
    args = parser.parse_args()
    if args.fixture_test:
        print(json.dumps(fixture_test(), indent=2))
    elif args.url:
        print(json.dumps(validate(args.url), indent=2))
    else:
        parser.error("provide --url or --fixture-test")
