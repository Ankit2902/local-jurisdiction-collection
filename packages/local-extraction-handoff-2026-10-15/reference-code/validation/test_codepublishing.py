"""Offline parser checks; live evidence is recorded separately per jurisdiction."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from adapters.codepublishing import parse_chapter_sections, parse_root_titles, parse_title_chapters

FIXTURES = Path(__file__).parent / "fixtures" / "codepublishing"

class CodePublishingParserTests(unittest.TestCase):
    def test_root_title_links_exclude_tables(self):
        links = parse_root_titles((FIXTURES / "root.html").read_text(), "https://www.codepublishing.com/CA/Fremont/")
        self.assertEqual([x.label for x in links], ["Title 1 GENERAL PROVISIONS", "Title 18 PLANNING"])
    def test_title_chapter_links(self):
        links = parse_title_chapters((FIXTURES / "title.html").read_text(), "https://www.codepublishing.com/CA/Fremont/html/Fremont01/Fremont01.html")
        self.assertEqual(len(links), 2)
        self.assertTrue(links[0].url.endswith("Fremont0105.html"))
    def test_chapter_text_and_fragments(self):
        sections = parse_chapter_sections((FIXTURES / "chapter.html").read_text(), "https://www.codepublishing.com/CA/Fremont/html/Fremont01/Fremont0105.html")
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0]["section_number"], "1.05.010")
        self.assertIn("Municipal Code is adopted", sections[0]["full_text"])
        self.assertTrue(sections[0]["source_url"].endswith("#Fremont0105010"))

if __name__ == "__main__":
    unittest.main()
