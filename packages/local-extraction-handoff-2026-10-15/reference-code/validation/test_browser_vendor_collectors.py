"""End-to-end fixture tests for the isolated browser-vendor full collectors."""
from __future__ import annotations
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from adapters.browser_vendor_collectors import BrowserVendorCollector, FixtureTransport, Publication, SCHEMA, _hierarchy  # noqa:E402
from adapters import american_legal  # noqa:E402


class BrowserVendorCollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="municipal-browser-collector-"))
        self.fixtures = ROOT / "fixtures"
    def tearDown(self):
        shutil.rmtree(self.temp)
    def _run(self, adapter, root, pages):
        collector = BrowserVendorCollector(Publication("sample", "Sample City", adapter, root), FixtureTransport(pages), self.temp / adapter)
        rows = collector.collect(max_pages=20)
        output = collector.write_outputs(self.temp / "out")
        self.assertTrue(rows); self.assertEqual(set(rows[0]), set(SCHEMA)); self.assertTrue(Path(output["csv"]).exists())
    def test_generic_code_ancestor_maps_to_code_name(self):
        self.assertEqual(_hierarchy(["code Code"])["code_name"], "Code of Ordinances")
        self.assertEqual(_hierarchy(["Municipal Code", "Home Rule Charter"])["code_name"], "Home Rule Charter")
        self.assertEqual(_hierarchy(["Municipal Code", "Zoning Code"])["code_name"], "Zoning Code")
        self.assertEqual(_hierarchy(["Municipal Code", "link Home Rule Charter"])["code_name"], "Home Rule Charter")
        collector = BrowserVendorCollector(
            Publication("sample", "Sample City", "ecode360", "https://ecode360.com/ROOT"),
            FixtureTransport({}), self.temp / "family-name")
        collector._add("§ 1.01 Rule", "Enacted text.", "https://ecode360.com/1",
                       ["Municipal Code", "Home Rule Charter"])
        self.assertEqual(collector.rows[0]["code_name"], "Home Rule Charter")
    def test_ecode360(self):
        root, section = "https://ecode360.com/44587767", "https://ecode360.com/44507298"
        section_html = "<main><h1>§ 1.04.010 Definitions.</h1><p>City means the City of Burlingame.</p></main>"
        self._run("ecode360", root, {root:(self.fixtures/"ecode360/root-sample.html").read_text(), section:section_html})
    def test_ecode360_rejects_site_chrome_outside_the_publication(self):
        collector = BrowserVendorCollector(
            Publication("sample", "Sample City", "ecode360", "https://ecode360.com/ME4536"),
            FixtureTransport({}), self.temp / "ecode-links")
        self.assertTrue(collector._allowed("https://ecode360.com/47069287"))
        self.assertFalse(collector._allowed("https://ecode360.com/ME4536/home"))
        self.assertFalse(collector._allowed("https://ecode360.com/docs/TOS.html"))
    def test_ecode360_home_allows_named_top_level_code_and_charter(self):
        root = "https://ecode360.com/PI6865/home"
        collector = BrowserVendorCollector(
            Publication("pittsburgh-pa", "Pittsburgh", "ecode360", root),
            FixtureTransport({}), self.temp / "ecode-home-links")
        html = """
        <a href='/45480664'>Home Rule Charter</a>
        <a href='/45474054'>Zoning Code</a>
        <a href='/PI6865'>Code</a>
        <a href='/PI6865/laws'>New Laws</a>
        <a href='/help/PI6865/about'>Help</a>
        """
        links = collector._links(html, root)
        self.assertEqual(
            {target for target, _ in links},
            {"https://ecode360.com/45480664", "https://ecode360.com/45474054", "https://ecode360.com/PI6865"})
    def test_ecode360_deduplicates_a_rendered_chapter_across_child_urls(self):
        html = "<main><h1>§ 1.04.010 Definitions.</h1><p>Enacted definition.</p></main>"
        collector = BrowserVendorCollector(
            Publication("sample", "Sample City", "ecode360", "https://ecode360.com/ME4536"),
            FixtureTransport({}), self.temp / "ecode-dedup")
        collector._sections(html, "https://ecode360.com/44507298", ["Municipal Code"])
        expected = len(collector.rows)
        collector._sections(html, "https://ecode360.com/44507299", ["Municipal Code"])
        self.assertGreater(expected, 0)
        self.assertEqual(expected, len(collector.rows))
    def test_american_legal(self):
        root = "https://codelibrary.amlegal.com/codes/paloalto/latest/overview"
        section = "https://codelibrary.amlegal.com/codes/paloalto/latest/paloalto_ca/0-0-0-59578"
        self._run("american_legal", root, {root:(self.fixtures/"amlegal/palo-alto-toc.html").read_text(), section:(self.fixtures/"amlegal/palo-alto-section.html").read_text(), "https://codelibrary.amlegal.com/codes/paloalto/latest/paloalto_ca/0-0-0-59584":(self.fixtures/"amlegal/palo-alto-section.html").read_text()})
    def test_american_legal_overview_starts_with_family_roots_and_stays_in_family(self):
        root = "https://codelibrary.amlegal.com/codes/san_francisco/latest/overview"
        collector = BrowserVendorCollector(
            Publication("san-francisco-ca", "San Francisco", "american_legal", root),
            FixtureTransport({}), self.temp / "amlegal-family-links")
        overview = """
        <a href='/codes/san_francisco/latest/sf_admin/0-0-0-15'>San Francisco Administrative Code</a>
        <a href='/codes/san_francisco/latest/sf_charter/0-0-0-1'>San Francisco Charter</a>
        <a href='/codes/san_francisco/latest/sf_admin/0-0-0-16'>Chapter 1 General Provisions</a>
        """
        self.assertEqual(
            [label for _, label in collector._links(overview, root)],
            ["San Francisco Administrative Code", "San Francisco Charter"])
        family_url = "https://codelibrary.amlegal.com/codes/san_francisco/latest/sf_admin/0-0-0-15"
        family = """
        <a href='/codes/san_francisco/latest/sf_admin/0-0-0-16'>Chapter 1</a>
        <a href='/codes/san_francisco/latest/sf_charter/0-0-0-2'>Article I</a>
        <a href='/codes/san_francisco/latest/sf_admin/history/1'>History</a>
        """
        self.assertEqual(
            collector._links(family, family_url),
            [("https://codelibrary.amlegal.com/codes/san_francisco/latest/sf_admin/0-0-0-16", "Chapter 1")])
    def test_american_legal_link_only_index_is_not_full_text(self):
        index_html = "<div id='curr-section'><h1>Chapter 1</h1><a href='/one'>Sec. 1.1</a><a href='/two'>Sec. 1.2</a></div>"
        section_html = "<div id='curr-section'><h5>Sec. 1.1.</h5><p>Enacted provision text.</p></div>"
        self.assertEqual("", american_legal.parse_section_html(index_html))
        self.assertIn("Enacted provision text.", american_legal.parse_section_html(section_html))
    def test_gridics(self):
        root = "https://codehub.gridics.com/us/ca/cupertino#/x"
        self._run("gridics_codehub", root, {root:(self.fixtures/"gridics/cupertino-section.html").read_text()})
    def test_icc(self):
        root, section = "https://sonoma.municipal.codes/SMC", "https://sonoma.municipal.codes/SMC/1"
        section_html = (self.fixtures/"municipal_codes/sonoma-section-sample.html").read_text()
        self._run("municipal_codes", root, {root:(self.fixtures/"municipal_codes/sonoma-root-sample.html").read_text(), section:section_html, "https://sonoma.municipal.codes/SMC/2":section_html})
    def test_icc_rendered_chapter_splits_section_cards(self):
        root, chapter = "https://sample.municipal.codes/Code", "https://sample.municipal.codes/Code/1.01.010"
        root_html = '<main><a href="/Code/1.01.010">Chapter 1.01</a></main>'
        chapter_html = '''<main><article class="type-Section" data-short-cite="1.01.010" data-history="/Code/1.01.010/history"><header><span class="num">1.01.010</span><span class="name">First rule.</span></header><p>First enacted text.</p></article><article class="type-Section" data-short-cite="1.01.020" data-history="/Code/1.01.020/history"><header><span class="num">1.01.020</span><span class="name">Second rule.</span></header><p>Second enacted text.</p></article></main>'''
        collector = BrowserVendorCollector(Publication("sample", "Sample City", "municipal_codes", root),
                                           FixtureTransport({root: root_html, chapter: chapter_html}), self.temp / "icc-split")
        rows = collector.collect(max_pages=4)
        self.assertEqual([row["section_number"] for row in rows], ["1.01.010", "1.01.020"])
        self.assertEqual([row["source_url"] for row in rows], [chapter, "https://sample.municipal.codes/Code/1.01.020"])
    def test_codepublishing_and_legacy(self):
        current = ROOT / "validation" / "fixtures" / "codepublishing"
        root = "https://www.codepublishing.com/CA/Fremont/"
        title = "https://www.codepublishing.com/CA/Fremont/html/Fremont01/Fremont01.html"
        chapter = "https://www.codepublishing.com/CA/Fremont/html/Fremont01/Fremont0105.html"
        root_html = (current/"root.html").read_text().replace('<a href="html/Fremont18/Fremont18.html">Title 18 PLANNING</a>', '').replace('<a href="ordinances.html">ORDINANCE TABLE</a>', '')
        self._run("codepublishing", root, {root:root_html, title:(current/"title.html").read_text(), chapter:(current/"chapter.html").read_text(), "https://www.codepublishing.com/CA/Fremont/html/Fremont01/Fremont0110.html":(current/"chapter.html").read_text()})
        legacy = ROOT / "validation" / "washington-arizona" / "fixtures"
        root = "https://www.codepublishing.com/WA/Burien/"
        title = root + "#!/Burien01/Burien01.html"
        chapter = root + "#!/Burien01/Burien0101.html#1.01"
        root_html = (legacy/"burien-root.html").read_text().splitlines()[0]
        self._run("codepublishing_legacy", root, {root:root_html, title:(legacy/"burien-title.html").read_text(), chapter:(legacy/"burien-chapter.html").read_text(), root + "#!/Burien01/Burien0105.html#1.05":(legacy/"burien-chapter.html").read_text()})
    def test_elaws(self):
        root = "https://dalycity-ca.elaws.us/code/coor"
        self._run("elaws", root, {root:(self.fixtures/"daly-city-elaws-section.html").read_text()})


if __name__ == "__main__":
    unittest.main()
