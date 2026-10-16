"""Actual standalone acquisition and publisher-download regressions; no network."""
import unittest,tempfile,shutil
from pathlib import Path
import municipal_codes_cli as m
import prepare_standalone as p
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parent
class StandaloneTests(unittest.TestCase):
 def test_actual_legal_pre_post_brackets(self):
  for slug in ('berkeley-ca','petaluma-ca','sonoma-ca'):
   q=p.qualify(R/'headed-legal-stable'/slug,slug,'page');self.assertTrue(q['bracket_stable']);self.assertGreater(len(q['rows']),0);self.assertIn('current through',q['raw_currency_text'])
 def test_actual_bellingham_single_capture_and_rate_limit(self):
  q=p.qualify(R/'headed-pilot'/'bellingham-wa','bellingham-wa','page');self.assertEqual(len(q['rows']),13);self.assertIsNone(q['bracket_stable']);r=m.read_json(R/'headed-legal-stable'/'bellingham-wa'/'receipt.json');self.assertEqual(r['stages'][0]['http_status'],429);self.assertFalse(r['stages'][0]['accepted'])
 def test_actual_html_export_selected_section_not_chapter_title(self):
  for slug in ('berkeley-ca','everett-wa'):
   q=p.qualify(R/'headed-ui-export'/slug,slug,'download');self.assertEqual([r['node_id'] for r in q['rows']],['dom:1.01.010']);self.assertEqual(q['rows'][0]['section_number'],'1.01.010');self.assertTrue(q['receipt']['accepted']);self.assertFalse(q['receipt']['operator_assisted'])
 def test_berkeley_download_matches_fresh_browser_body(self):
  download=p.qualify(R/'headed-ui-export'/'berkeley-ca','berkeley-ca','download');page=p.qualify(R/'headed-legal-stable'/'berkeley-ca','berkeley-ca','page');row=next(r for r in page['rows'] if r['node_id']=='dom:1.01.010');self.assertEqual(download['rows'][0]['body_sha256'],row['body_sha256']);self.assertEqual(download['raw_currency_text'],page['raw_currency_text'])
 def test_everett_currency_uses_site_footer_not_statutory_note(self):
  from prepare_e2e import currency
  text=(R/'live-final'/'everett-wa'/'chapter.html').read_text();value=currency(text);self.assertIn('4203-26',value);self.assertIn('September 16, 2026',value);self.assertNotIn('statutory provisions',value)
 def test_missing_current_through_rejected(self):
  from prepare_e2e import currency
  self.assertEqual(currency('<html><main><article><footer>statutory note</footer></article></main><footer id="site-footer">City website only</footer></html>'),'')
  with tempfile.TemporaryDirectory() as t:
   d=Path(t)/'source';shutil.copytree(R/'headed-ui-export'/'everett-wa',d);path=d/'download.html';soup=BeautifulSoup(path.read_text(),'html.parser');soup.select_one('#site-footer').decompose();path.write_text(str(soup));r=m.read_json(d/'receipt.json');r['raw_sha256']=m.sha(path.read_bytes());m.write_json(d/'receipt.json',r)
   with self.assertRaises(m.QualificationError):p.qualify(d,'everett-wa','download')
 def test_selected_export_anchor_matches_only_exact_inventory_route(self):
  q=p.qualify(R/'headed-ui-export'/'everett-wa','everett-wa','download');record=q['rows'][0];node={'node_id':'url:https://everett.municipal.codes/EMC/1.01.010','source_url':'https://everett.municipal.codes/EMC/1.01.010'};self.assertTrue(m.inventory_matches_record(node,record))
  wrong=dict(record,node_id='dom:1.01.020',source_url='https://everett.municipal.codes/EMC/1.01.010#1.01.020');self.assertFalse(m.inventory_matches_record(node,wrong));wrong=dict(record,locator={'kind':'attribute'});self.assertFalse(m.inventory_matches_record(node,wrong))
 def test_tampered_file_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);shutil.copytree(R/'headed-ui-export'/'everett-wa',d/'source');(d/'source'/'download.html').write_text('tampered')
   with self.assertRaises(m.QualificationError):p.qualify(d/'source','everett-wa','download')
 def test_changed_pre_post_body_rejected_even_with_correct_raw_hash(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t)/'source';shutil.copytree(R/'headed-legal-stable'/'berkeley-ca',d);path=d/'page-after.html';soup=BeautifulSoup(path.read_text(),'html.parser');card=soup.find('article',id='1.01.010');card.append(soup.new_tag('p'));card.find_all('p')[-1].string='Changed source text';path.write_text(str(soup));r=m.read_json(d/'receipt.json');r['stages'][0]['after_sha256']=m.sha(path.read_bytes());m.write_json(d/'receipt.json',r)
   with self.assertRaises(m.QualificationError):p.qualify(d,'berkeley-ca','page')
 def test_failed_ui_or_direct_export_never_accepted(self):
  for slug in ('berkeley-ca','petaluma-ca','everett-wa'):
   r=m.read_json(R/'headed-download-recovery'/slug/'receipt.json');self.assertFalse(any(s['accepted'] for s in r['stages']))
if __name__=='__main__':unittest.main()
