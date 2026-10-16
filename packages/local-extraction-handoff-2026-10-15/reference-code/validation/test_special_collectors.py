"""Offline integration tests for the special-source full collectors."""
from __future__ import annotations

import io
import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters import baltimore_openlaw_bulk_xml, openlaw_bulk_xml, special_collectors
from adapters import nyc_amlegal_bulk_xml


def test_openlaw_collectors_emit_16_column_output() -> None:
    with tempfile.TemporaryDirectory() as temp:
        result = special_collectors.collect_openlaw_xml(
            Path(temp), jurisdiction="San Mateo, California", slug="san-mateo-ca",
            xml_files=[ROOT / "fixtures" / "san-mateo-title-1.xml"],
            parser=openlaw_bulk_xml.parse_title_xml, code_name="San Mateo Municipal Code")
        rows = json.loads(Path(result["json"]).read_text(encoding="utf-8"))["provisions"]
        assert len(rows) == 2
        assert list(rows[0]) == special_collectors.SCHEMA
        assert rows[0]["full_text"] and rows[0]["chapter"]


def test_baltimore_openlaw_collector_works_for_retained_research() -> None:
    with tempfile.TemporaryDirectory() as temp:
        fixture = ROOT / "validation" / "central-east" / "fixtures" / "baltimore-article-1.xml"
        result = special_collectors.collect_openlaw_xml(
            Path(temp), jurisdiction="Baltimore City, Maryland", slug="baltimore-city-md",
            xml_files=[fixture], parser=baltimore_openlaw_bulk_xml.parse_article_xml,
            code_name="Baltimore City Code")
        assert result["rows"] == 2 and result["full_text_rows"] == 2


def test_nyc_bulk_collector_keeps_families_separate() -> None:
    payload = io.BytesIO()
    fixture = (ROOT / "fixtures" / "nyc-amlegal-sample.xml").read_bytes()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("XML/sample.xml", fixture)
    with tempfile.TemporaryDirectory() as temp:
        result = special_collectors.collect_nyc_bulk(Path(temp), fetch=lambda _: payload.getvalue())
        assert [item["rows"] for item in result] == [1, 1, 1]
        assert all(Path(item["csv"]).exists() for item in result)


def test_king_county_collector_from_first_party_fixtures() -> None:
    fixtures = ROOT / "validation" / "washington-arizona" / "fixtures"
    landing_url = "https://kingcounty.gov/code"
    title_url = "https://aqua.kingcounty.gov/council/clerk/code/04_Title_1.htm"
    # The small landing fixture has a second title link; give it the same fixture
    # to exercise complete landing traversal without making a live request.
    mapping = {landing_url: (fixtures / "king-county-landing.html").read_text(encoding="utf-8"),
               title_url: (fixtures / "king-county-title-1.html").read_text(encoding="utf-8"),
               "https://aqua.kingcounty.gov/council/clerk/code/05_Title_2.htm": (fixtures / "king-county-title-1.html").read_text(encoding="utf-8")}
    with tempfile.TemporaryDirectory() as temp:
        result = special_collectors.collect_king_county(Path(temp), landing_url, fetch=lambda url: mapping[url])
        assert result["rows"] == 4 and result["full_text_rows"] == 4


def test_san_diego_pdf_collector_from_official_pdf_fixture() -> None:
    fixture_root = ROOT / "fixtures"
    chapter_url = "https://www.sandiego.gov/city-clerk/officialdocs/municipal-code/chapter-1"
    html = (fixture_root / "san-diego-chapter-toc.html").read_text(encoding="utf-8")
    pdf = (fixture_root / "san-diego-Ch01Art01Division01-official.pdf").read_bytes()
    with tempfile.TemporaryDirectory() as temp:
        result = special_collectors.collect_san_diego(
            Path(temp), [chapter_url], fetch=lambda _: html, fetch_bytes=lambda _: pdf)
        # Fixture links two divisions; feed the retained official division to both
        # only to exercise portal discovery + download + PDF extraction offline.
        assert result["rows"] == 10 and result["full_text_rows"] == 10


def test_civicplus_collectors_rediscover_documents_each_run() -> None:
    fixtures = ROOT / "validation" / "central-east" / "fixtures"
    pdf = (ROOT / "fixtures" / "san-diego-Ch01Art01Division01-official.pdf").read_bytes()
    calls: list[str] = []
    with tempfile.TemporaryDirectory() as temp:
        result = special_collectors.collect_portland_me(
            Path(temp), fetch_text=lambda _: (fixtures / "portland-city-code-root.html").read_text(encoding="utf-8"),
            fetch_bytes=lambda url: calls.append(url) or pdf)
        assert len(calls) == 10 and Path(result["json"]).exists()
    with tempfile.TemporaryDirectory() as temp:
        result = special_collectors.collect_rockland_me(
            Path(temp), fetch_text=lambda _: (fixtures / "rockland-index.html").read_text(encoding="utf-8"),
            fetch_bytes=lambda _: pdf)
        assert Path(result["csv"]).exists()
