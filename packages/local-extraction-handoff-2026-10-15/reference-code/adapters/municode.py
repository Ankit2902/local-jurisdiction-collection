"""Read public Municode Library API responses.

Municode's document routes return an Angular application shell.  The same public
application calls the JSON endpoints below to populate its table of contents and
document view.  This module uses those endpoints rather than attempting to parse
the shell.  It is deliberately a validation/pilot adapter: callers should keep
their production crawl polite and respect the publisher's terms and robots rules.
"""
from __future__ import annotations

import re
import json
from pathlib import Path
from html import unescape
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

BASE = "https://library.municode.com"
HEADERS = {"User-Agent": "CompliSolv municipal-code validation bot/0.1", "X-CSRF": "1"}
SECTION_RE = re.compile(r"^(?:§\s*)?(?:sec(?:tion)?\.?\s*)?\d+[\w.\-]*\s*(?:[-–—:]|$)", re.I)


def _result(root_url: str) -> dict[str, Any]:
    return {"status": "blocked", "root_url": root_url, "toc_url": "", "section_url": "",
            "toc_count_or_sample": 0, "section_text_length": 0, "checks": [], "errors": []}


def _client_from_root(root_url: str) -> tuple[str, str]:
    """Return the state abbreviation and client search name from a Library URL."""
    parts = [p for p in urlparse(root_url).path.split("/") if p]
    try:
        codes_index = parts.index("codes")
        state, client = parts[codes_index - 2:codes_index]
        # A Library URL preserves apostrophes as percent escapes; normalize it
        # before asking the keyword endpoint for the client record.
        from urllib.parse import unquote
        return state.upper(), unquote(client).replace("_", " ")
    except (ValueError, IndexError) as exc:
        raise ValueError("Municode root must include /<state>/<client>/codes/") from exc


def _get(session: requests.Session, path: str, **params: Any) -> Any:
    response = session.get(BASE + path, params=params, headers=HEADERS, timeout=45)
    response.raise_for_status()
    return response.json()


def _client(session: requests.Session, client_name: str, state: str) -> dict[str, Any]:
    clients = _get(session, "/api/Clients/keyword", keyword=client_name)
    matches = [c for c in clients if c.get("ClientName", "").casefold() == client_name.casefold()
               and c.get("State", {}).get("StateAbbreviation") == state]
    if len(matches) != 1:
        raise RuntimeError("expected one %s Municode client for %r; found %d" % (state, client_name, len(matches)))
    return matches[0]


def _publication(session: requests.Session, client_id: int) -> dict[str, Any]:
    publications = _get(session, "/api/ClientContent/%s" % client_id).get("codes", [])
    # Municode labels the same corpus differently by city (for example,
    # Redwood City publishes its general code as "City Code").  Keep zoning
    # and other specialty publications out of this general-code selection.
    preferred = ("code of ordinances", "municipal code", "city code")
    for name in preferred:
        for publication in publications:
            if publication.get("productName", "").casefold() == name:
                return publication
    raise RuntimeError("no general Code of Ordinances, Municipal Code, or City Code publication is available")


def _leaves(node: dict[str, Any]) -> list[dict[str, Any]]:
    children = node.get("Children") or []
    if not children:
        return [node]
    output: list[dict[str, Any]] = []
    for child in children:
        output.extend(_leaves(child))
    return output


def _canonical_node_url(root_url: str, node_id: str) -> str:
    parsed = urlparse(root_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["nodeId"] = node_id
    return urlunparse(parsed._replace(query=urlencode(query)))


def text_from_docs(docs: list[dict[str, Any]], node_id: str) -> str:
    """Return readable text for the requested document from CodesContent docs."""
    for doc in docs:
        if doc.get("Id") == node_id:
            return BeautifulSoup(unescape(doc.get("Content") or ""), "html.parser").get_text("\n", strip=True)
    return ""


def validate(root_url: str) -> dict[str, Any]:
    """Validate a root, resolved TOC, and representative section without crawling it."""
    result = _result(root_url)
    session = requests.Session()
    try:
        state, client_name = _client_from_root(root_url)
        client = _client(session, client_name, state)
        publication = _publication(session, int(client["ClientID"]))
        product_id = int(publication["productId"])
        toc_url = BASE + "/api/codesToc/fullTree/latest?" + urlencode({"productId": product_id, "nodeId": product_id})
        tree = _get(session, "/api/codesToc/fullTree/latest", productId=product_id, nodeId=product_id)
        leaves = _leaves(tree)
        sections = [node for node in leaves if SECTION_RE.match((node.get("Heading") or "").strip())]
        if not sections:
            raise RuntimeError("TOC contained no section-shaped leaf nodes")
        section = sections[0]
        node_id = section["Id"]
        docs = _get(session, "/api/codesContent", productId=product_id, nodeId=node_id)
        body = text_from_docs(docs.get("Docs") or [], node_id)
        if not body:
            raise RuntimeError("representative section returned no readable text")
        result.update({
            "status": "validated",
            "toc_url": toc_url,
            "section_url": _canonical_node_url(root_url, node_id),
            "toc_count_or_sample": len(sections),
            "section_text_length": len(body),
            "checks": [
                "%s client resolved through public Clients/keyword API" % state,
                "Code of Ordinances/Municipal Code publication resolved through public ClientContent API",
                "fullTree/latest returned section-shaped leaf nodes",
                "codesContent returned readable representative section text",
            ],
        })
    except (requests.RequestException, ValueError, RuntimeError, KeyError) as exc:
        result["errors"].append(str(exc))
    return result


def fixture_test() -> dict[str, Any]:
    """Verify the API-tree and content parsers without contacting Municode."""
    root = Path(__file__).resolve().parents[1] / "fixtures" / "municode"
    toc = json.loads((root / "toc-sample.json").read_text(encoding="utf-8"))
    content = json.loads((root / "content-sample.json").read_text(encoding="utf-8"))
    leaf = _leaves(toc)[0]
    text = text_from_docs(content["Docs"], leaf["Id"])
    assert SECTION_RE.match(leaf["Heading"]) and text == "There is adopted the Municipal Code."
    return {"fixture": str(root), "sections": 1, "section_text_length": len(text), "passed": True}
