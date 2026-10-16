"""Fresh source regressions and receipt/hash refusal tests; no network."""
import tempfile,unittest,json,shutil
from pathlib import Path
from bs4 import BeautifulSoup
import municipal_codes_cli as m
import prepare_e2e as e
R=Path(__file__).resolve().parent
class FreshSourceTests(unittest.TestCase):
 def parse(self,slug):
  base=m.ROUTES[slug][2];r=e.load_capture(R/'live-final'/slug,'difficult');return m.parse_page(r[2],r[0]['job']['url'],base),r[2]
 def test_actual_sonoma_appendix_body_and_numbered_paragraphs(self):
  (rows,notes),html=self.parse('sonoma-ca');r=next(r for r in rows if r['node_id']=='dom:9.80_AppA');self.assertIn('IMPORTANT NOTICE TO PROSPECTIVE HOMEOWNER',r['full_text']);self.assertIn('(1)',r['full_text']);self.assertIn('(2)',r['full_text']);self.assertIn('(3)',r['full_text']);self.assertIn('72 HOURS',r['full_text']);self.assertFalse(any('Unknown article type' in n['reason'] for n in notes))
 def test_actual_petaluma_appendix_navigation_structural(self):
  (rows,notes),html=self.parse('petaluma-ca');self.assertEqual(rows,[]);self.assertTrue(any(n.get('node_id')=='dom:Appendices' and n['status']=='structural' for n in notes))
 def test_actual_tables_preserve_spans_and_cells(self):
  for slug in ('berkeley-ca','everett-wa'):
   (rows,_),html=self.parse(slug);source=BeautifulSoup(html,'html.parser');
   # Publisher floating-header clones are explicitly aria-hidden duplicate tables.
   for clone in source.select('table.floattable-header[aria-hidden="true"]'):clone.decompose()
   parsed=BeautifulSoup(''.join(r['content_html'] for r in rows),'html.parser');self.assertGreater(len(parsed.select('table')),0)
   self.assertEqual(len(source.select('main article.type-Section table')),len(parsed.select('table')))
   self.assertEqual([(c.name,c.get('rowspan'),c.get('colspan'),c.get_text(' ',strip=True)) for c in source.select('main article.type-Section table th, main article.type-Section table td')],[(c.name,c.get('rowspan'),c.get('colspan'),c.get_text(' ',strip=True)) for c in parsed.select('table th, table td')])
 def test_actual_images_exact_marker_alt_and_source_sidecar(self):
  (rows,_),html=self.parse('bellingham-wa');images=BeautifulSoup(html,'html.parser').select('main article.type-Section img');self.assertGreater(len(images),0);text='\n'.join(r['full_text'] for r in rows);self.assertEqual(text.count('[IMAGE]'),len(images));self.assertNotIn('[IMAGE:',text)
  for im in images:
   self.assertIn(im['src'],''.join(r['content_html'] for r in rows))
   if im.get('alt'):self.assertIn(im['alt'],text)
 def test_every_fresh_receipt_raw_sha_and_rejection(self):
  for p in (R/'live-final').rglob('*.receipt.json'):
   r=m.read_json(p);self.assertEqual(m.sha((p.parent/r['raw_artifact_path']).read_bytes()),r['sha256'])
   if r['accepted']:e.load_capture(p.parent,r['job']['id'])
   else:
    with self.assertRaises(m.QualificationError):e.load_capture(p.parent,r['job']['id'])
 def test_publications_include_primary_and_every_observed_family(self):
  for slug,expected in [('petaluma-ca',{'municipal-code','publisher:ZoningOrds','publisher:SmartCode','publisher:Charter'}),('bellingham-wa',{'municipal-code','publisher:Charter'})]:
   pubs=e.discover_publications(R/'live-final'/slug,m.ROUTES[slug][2],'observed currency')
   self.assertTrue(expected.issubset({p['publication_id'] for p in pubs}))
   for p in pubs:
    self.assertTrue(p['publication_title']);self.assertTrue(p['publication_base']);self.assertTrue(p['scope_disposition']);self.assertTrue(p['evidence']['raw_sha256']);self.assertIn('raw_currency_text',p)
 def test_tampered_capture_fails_closed(self):
  with tempfile.TemporaryDirectory() as t:
   d=Path(t);source=R/'live-final'/'berkeley-ca'
   for n in ('chapter.html','chapter.receipt.json'):shutil.copy(source/n,d/n)
   (d/'chapter.html').write_text('tampered')
   with self.assertRaises(m.QualificationError):e.load_capture(d,'chapter')
if __name__=='__main__':unittest.main()
