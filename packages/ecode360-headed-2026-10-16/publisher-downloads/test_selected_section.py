import csv,json,tempfile,unittest
from pathlib import Path
import pdfplumber
from bs4 import BeautifulSoup
from export_intake import Rejected
from export_selected_section import export_section,normalize,parse_lines,source_text
BASE=Path(__file__).parent
class ActualSectionTests(unittest.TestCase):
 def test_all13_actual_pdf_native_exports(self):
  index=json.loads((BASE/'FRESH-FILE-INDEX.json').read_text());self.assertEqual(len(index),13)
  with tempfile.TemporaryDirectory() as tmp:
   for row in index:
    with self.subTest(city=row['slug']):
     d=BASE/'downloads'/row['slug'];out=Path(tmp)/row['slug'];record=export_section(d/'publisher-download-0.pdf',d/'canonical-receipt.json',d/'source.html',out)
     self.assertEqual(record['citation'],row['selected_citation']);self.assertEqual(record['source_pdf_sha256'],row['pdf_sha256'])
     expected='REVIEW_REQUIRED_NON_TEXT_OR_TABLE_LAYOUT' if row['slug']=='san-leandro-ca' else 'PASS_BOUNDED_SELECTED_SECTION_TEXT';self.assertEqual(record['semantic_status'],expected)
     comp=json.loads((out/'source-comparison.json').read_text());self.assertTrue(comp['full_body_equal_after_NFC_whitespace_normalization']);self.assertTrue(comp['section_title_equal_after_NFC_whitespace_normalization'])
     with (out/'section.csv').open() as f:csvrow=next(csv.DictReader(f));self.assertEqual(csvrow['body_text'],record['body_text'])
 def test_heading_words_are_operative_text_not_removed(self):
  d=BASE/'downloads/south-san-francisco-ca'
  with pdfplumber.open(d/'publisher-download-0.pdf') as pdf:r=parse_lines(pdf.pages[0].extract_text(),'South San Francisco')
  self.assertEqual(r['citation'],'1.01.070');self.assertIn('Title, chapter and section headings contained herein shall not be deemed to govern, limit,',r['body_text']);self.assertIn('(Ord. 875 § 7, 1981)',r['body_text']);self.assertNotIn('Downloaded from',r['body_text'])
 def test_emeryville_actual_heading_without_section_symbol(self):
  d=BASE/'downloads/emeryville-ca'
  with pdfplumber.open(d/'publisher-download-0.pdf') as pdf:r=parse_lines(pdf.pages[0].extract_text(),'Emeryville')
  self.assertEqual(r['citation'],'1-1.05');self.assertEqual(r['section_title'],'Headings.')
 def test_pdf_footer_must_be_observed_publisher_layout(self):
  with self.assertRaisesRegex(Rejected,'footer absent'):parse_lines('City of Example\n§ 1.01.010. Title.\nLegal body\nUnknown exporter footer','Example')
 def test_source_snapshot_hash_must_match_acquisition_receipt(self):
  d=BASE/'downloads/south-san-francisco-ca'
  with tempfile.TemporaryDirectory() as tmp:
   wrong=Path(tmp)/'wrong.html';wrong.write_text('<html>Different source</html>')
   with self.assertRaisesRegex(Rejected,'source DOM SHA256'):export_section(d/'publisher-download-0.pdf',d/'canonical-receipt.json',wrong,Path(tmp)/'out')
 def test_inline_history_punctuation_not_rewritten(self):
  s=BeautifulSoup('<div><p>Body.</p><div class="history">(<span>Ord. 1</span> § 2, 1981)</div></div>','html.parser')
  self.assertEqual(normalize(source_text(s)),'Body. (Ord. 1 § 2, 1981)')
if __name__=='__main__':unittest.main()
