import contextlib, html, io, json, shutil, tempfile, unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import Mock, patch
import civicplus as cp

HERE=Path(__file__).resolve().parent
class InventoryTests(unittest.TestCase):
 def test_semantic_widget_survives_decoy_and_membership_changes(self):
  source=(HERE/'evidence/portland-index.html').read_text()
  ids=[f'00000000-0000-0000-0000-{i:012d}' for i in range(12)]
  decoy='<script>(function(){const n={options:{header:"Other Documents"},manualContentItemIds:'+json.dumps(ids)+'};})()</script>'
  actual=cp.portland_inventory(source,(HERE/'evidence/portland-widget-browser.html').read_text())
  self.assertEqual(cp.portland_inventory(decoy+source,(HERE/'evidence/portland-widget-browser.html').read_text()),actual)
  self.assertEqual(len(actual),44)
  self.assertTrue(all(x['label'] for x in actual))
  self.assertEqual(actual[0]['node_id'],'a921cc20-0587-4cf2-bf13-eba2a2fef41e')
  self.assertNotEqual(actual[0]['selection_order'],actual[0]['source_order'])
 def test_ambiguous_or_missing_widget_fails(self):
  source=(HERE/'evidence/portland-index.html').read_text()
  with self.assertRaises(ValueError): cp.portland_inventory(source+source)
  with self.assertRaises(ValueError): cp.portland_inventory('<html>Access denied</html>')
 def test_membership_not_hard_coded_to_44(self):
  ident='00000000-0000-0000-0000-000000000001'
  source='<script>const n={options:{header:"City Code Documents"},manualContentItemIds:["'+ident+'"],manualContentItemsOptions:{"'+ident+'":{contentType:"pdf",isAsset:!0}},columns:[["'+ident+'"]]};renderWidget(n,"widget-id")</script>'
  self.assertEqual(len(cp.portland_inventory(source)),1)
 def test_rockland_publications(self):
  rows=cp.rockland_inventory((HERE/'evidence/rockland-index-browser-main.html').read_text(),cp.ROOTS['rockland-me'])
  self.assertEqual(len(rows),21)
  self.assertEqual([x['node_id'] for x in rows if x['publication_id']=='charter'],['document-620'])
  self.assertEqual(len({x['node_id'] for x in rows}),21)
 def test_no_number_dedup(self):
  blocks=[{'kind':'line','page':1,'bbox':[54,120,500,132],'text':'Sec. 1-1. First'}, {'kind':'line','page':1,'bbox':[54,140,500,152],'text':'Body A'}, {'kind':'line','page':2,'bbox':[54,120,500,132],'text':'Sec. 1-1. Second'}, {'kind':'line','page':2,'bbox':[54,140,500,152],'text':'Body B'}]
  sections,_,_=cp.segment(blocks,'portland')
  self.assertEqual([s['number'] for s in sections],['1-1','1-1'])

class PdfRegressionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p,cls.b,cls.issues=cp.extract_document(HERE/'evidence/portland-ch13.pdf','portland')
  cls.sections,_,_=cp.segment(cls.b,'portland')
  cls.rp,cls.rb,cls.ri=cp.extract_document(HERE/'evidence/rockland-ch1.pdf','rockland-code')
  cls.rs,cls.rt,cls.rsi=cp.segment(cls.rb,'rockland-code')
  cls.cp,cls.cb,cls.ci=cp.extract_document(HERE/'evidence/rockland-charter.pdf','rockland-charter')
  cls.cs,cls.ct,cls.csi=cp.segment(cls.cb,'rockland-charter')
 def test_portland_real_headers_and_continuation(self):
  actual=[s for s in self.sections if s['number']]
  self.assertEqual([s['number'] for s in actual],[f'13-{i}' for i in range(1,13)])
  definition=next(s for s in actual if s['number']=='13-2')
  self.assertEqual({b['page'] for b in definition['blocks']},set(range(2,8)))
  text=cp.render_blocks(definition['blocks'])
  self.assertIn('is receiving general assistance at the time of application.',text)
  self.assertIn('Dwelling unit',text)
  self.assertIn('housekeeping',text)
  self.assertNotIn('Rev.',text)
  self.assertFalse(any('Rev.' in s['name'] for s in self.sections))
  self.assertEqual(len([x for x in self.p[2]['removed'] if x['reason']=='running_header']),3)
 def test_table_preserves_cells_and_never_duplicated_as_lines(self):
  tables=[b for b in self.b if b['kind']=='table' and b['page']==37]
  self.assertEqual(len(tables),2)
  t=tables[0];self.assertIn('<table>',t['html']);self.assertIn('colspan=',t['html']);self.assertTrue(t['cells']);self.assertIn('100',json.dumps(t['rows']))
  self.assertFalse(any(b['kind']=='line' and b['page']==37 and b['bbox'][1]>=t['bbox'][1] and b['bbox'][3]<=t['bbox'][3] for b in self.b))
 def test_mixed_page_gates_completion(self):
  self.assertIn('mixed_text_image',self.p[47]['review_reasons'])
  self.assertFalse(self.p[47]['ocr']['performed'])
  self.assertTrue(any(b['kind']=='image' and b['page']==48 for b in self.b))
 def test_rockland_toc_and_adopting_body_retained(self):
  self.assertEqual(len(self.rt),15)
  self.assertEqual([s['number'] for s in self.rs if s['number']],[f'1-{i}' for i in range(101,116)])
  self.assertFalse(self.rsi)
  self.assertIn('It is hereby ordained',cp.render_blocks(self.rs[0]['blocks']))
  one=next(s for s in self.rs if s['number']=='1-101')
  self.assertEqual(one['name'],'Adoption of Code')
  self.assertIn('1',cp.render_blocks(one['blocks'])) # source marker retained, not appended to heading
  definitions=next(s for s in self.rs if s['number']=='1-102')
  self.assertIn('"Street"',html.unescape(cp.render_blocks(definitions['blocks'])))
  self.assertEqual({b['page'] for b in definitions['blocks']},{2,3})
 def test_charter_independent_toc_and_overlapping_footer_review(self):
  self.assertEqual(len(self.ct),68)
  actual=[s for s in self.cs if s['number']]
  self.assertEqual(len(actual),68)
  self.assertFalse(self.csi)
  self.assertEqual(actual[0]['number'],'101')
  self.assertTrue(any(x['condition']=='source_footer_box_overlaps_legal_text' and x['page']==3 for x in self.ci))
  mayor=next(s for s in actual if s['number']=='203')
  self.assertIn('acting mayor who',cp.render_blocks(mayor['blocks']))
  self.assertNotIn('Sec. 101',cp.render_blocks(mayor['blocks']))
 def test_number_only_footer_not_legal_heading(self):
  for p in self.cp:
   for rem in p['removed']:
    if rem['reason']=='running_locator': self.assertGreater(rem['bbox'][0],612*.65)

class PackageTests(unittest.TestCase):
 def test_raw_integrity_and_contract(self):
  for slug in ['portland-me','rockland-me']:
   with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(cp.verify_package(Namespace(package=HERE/'samples'/slug)),0)
 def test_interrupted_and_clean_replay_equivalence(self):
  # Replay one Charter/code package with one document first, then resume second;
  # compare records, identities, and disposition sequence to clean same snapshot.
  source=HERE/'samples/rockland-me'
  with tempfile.TemporaryDirectory() as td:
   clean=Path(td)/'clean';resume=Path(td)/'resume'
   for dest in [clean,resume]:
    dest.mkdir();shutil.copytree(source/'raw',dest/'raw')
    for name in ['inventory.json','publications.json','acquisition.json']:shutil.copy(source/name,dest/name)
   full=cp.readj(resume/'acquisition.json');cp.writej(resume/'acquisition.json',{'document-621':full['document-621']})
   with contextlib.redirect_stdout(io.StringIO()):cp.parse_package(Namespace(package=resume))
   cp.writej(resume/'acquisition.json',full)
   with contextlib.redirect_stdout(io.StringIO()):cp.parse_package(Namespace(package=resume));cp.parse_package(Namespace(package=clean))
   for name in ['aggregate-fulltext.json','aggregate-fulltext.csv','node-dispositions.jsonl','record-provenance.jsonl','source-nodes.jsonl']:
    self.assertEqual((resume/name).read_bytes(),(clean/name).read_bytes(),name)
 def test_http_cache_resumes_and_fails_closed_on_corruption(self):
  with tempfile.TemporaryDirectory() as td:
   response=Mock(status_code=200,content=b'%PDF-example',url='https://example.org/doc',history=[],headers={})
   with patch('requests.Session.get',return_value=response) as get:
    fetch=cp.Fetcher(td,delay=0);p,meta=fetch.get('https://example.org/doc','pdf');fetch.get('https://example.org/doc','pdf')
    self.assertEqual(get.call_count,1)
    p.write_bytes(b'corruption')
    with self.assertRaises(ValueError): fetch.get('https://example.org/doc','pdf')
 def test_404_retained_and_never_emits_pdf(self):
  with tempfile.TemporaryDirectory() as td:
   response=Mock(status_code=404,content=b'',url='https://example.org/doc',history=[],headers={})
   with patch('requests.Session.get',return_value=response):
    with self.assertRaises(ValueError): cp.Fetcher(td,delay=0).get('https://example.org/doc','pdf')
   self.assertEqual(len(list(Path(td).glob('*.response.json'))),1)
  with tempfile.TemporaryDirectory() as td:
   response=Mock(status_code=200,content=b'<html>verification page</html>',url='https://example.org/doc',history=[],headers={})
   with patch('requests.Session.get',return_value=response):
    fetch=cp.Fetcher(td,delay=0)
    with self.assertRaises(ValueError): fetch.get('https://example.org/doc','pdf')
    with self.assertRaises(ValueError): fetch.get('https://example.org/doc','pdf')

if __name__=='__main__':unittest.main(verbosity=2)
