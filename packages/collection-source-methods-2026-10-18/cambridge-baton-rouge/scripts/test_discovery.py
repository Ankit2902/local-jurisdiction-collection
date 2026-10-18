import sys
sys.dont_write_bytecode=True
import unittest,json,hashlib
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup
import source_inventory as inv
ROOT=Path(__file__).resolve().parents[1]
class ActualSources(unittest.TestCase):
 def test_exact_thirty_and_seven_unlinked_metadata(self):
  d=inv.inventory((ROOT/'source/95-152a3da8bd28.html').read_bytes())
  self.assertEqual((d['document_count'],d['chapter_count'],d['appendix_count']),(30,19,11))
  self.assertEqual({x['source_document_id']for x in d['unlinked_widget_metadata']},{'2277','2262','12715','16522','2289','22979','23039'})
  self.assertFalse(d['full_publication_qualification'])
 def test_changed_source_edition_missing_duplicate_links_refuse(self):
  raw=(ROOT/'source/95-152a3da8bd28.html').read_bytes()
  for bad in [raw+b' ',raw.replace(b'Chapter 1 - General Provisions',b'Unknown source label',1),raw.replace(b'/DocumentCenter/View/2263/',b'/DocumentCenter/View/9999/',1)]:
   with self.assertRaisesRegex(AssertionError,'Source bytes/version'):inv.inventory(bad)
 def test_config_current_collector_inventory_exact_without_network(self):
  sys.path.insert(0,str(ROOT/'runtime'));import collect
  c=json.loads((ROOT/'configs/brla-udc-current-visible-documents.json').read_text());raw=(ROOT/'source/95-152a3da8bd28.html').read_bytes()
  expected=inv.inventory(raw)['selected_visible_documents']
  self.assertEqual(collect.inventory_projection(raw,c),sorted((x['url'],x['label'])for x in expected))
  self.assertEqual(collect.currency(raw,c),'Unified Development Code')
  self.assertEqual(c['coverage_level'],'file_pages')
 def test_cambridge_observed_twenty_three_articles_and_stopped_archive(self):
  d=json.loads((ROOT/'source/90-5918edb057f6.analysis.json').read_text())
  urls={x['url']for x in d['anchors']}
  arts={u for u in urls if'library.municode.com/'in u and'nodeId=ZOOR_ART'in u}
  self.assertEqual(len(arts),23);self.assertIn('https://library.municode.com/downloadarchive/15643',urls)
  self.assertIn('PDF (Supplement Only)',d['text'])
 def test_code_observed_municode_route_and_uncodified_warning(self):
  d=json.loads((ROOT/'source/95-4408caae6a9e.analysis.json').read_text())
  self.assertIn('http://library.municode.com/index.aspx?clientId=10107',{x['url']for x in d['anchors']})
  self.assertIn('not included in the Code of Ordinances',d['text'])
 def test_no_native_images_downloaded_in_discovery(self):
  for p in (ROOT/'source').glob('*.receipt.json'):
   m=json.loads(p.read_text());self.assertEqual(m['status'],200);self.assertFalse(m.get('policy_omitted_image'));self.assertNotIn('image/',m['headers'].get('Content-Type','').lower())
  for p in (ROOT/'headers').glob('*.json'):
   m=json.loads(p.read_text());self.assertFalse(m['body_read']);self.assertEqual(m['method'],'HEAD')
if __name__=='__main__':unittest.main(verbosity=2)
