"""Actual partial source plus explicitly synthetic whole-publication controls."""
import copy,json,sys,unittest,socket,subprocess,base64
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import municipal_codes_html as mc
from common import artifacts,canonical,encoded,sha,validate_projection
ROOT,PROOF,SYNTH,SYNTHPROOF=map(Path,sys.argv[1:5]);sys.argv=sys.argv[:1]
class Reader(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.proof=json.loads(PROOF.read_text());c.family=json.loads((PROOF.parent/'family-verification.json').read_text());c.guards=[]
  def no(*a,**k):raise AssertionError('Network/process/pixel decoder forbidden')
  for obj,name in [(socket,'create_connection'),(socket.socket,'connect'),(subprocess,'Popen'),(base64,'b64decode'),(Image,'open')]:g=patch.object(obj,name,no);g.start();c.guards.append(g)
  c.p=mc.read_projection(ROOT,c.proof,c.family);c.records=mc.lines(ROOT/'records.jsonl');c.nodes=mc.load(ROOT/'inventory.json');c.ds=mc.load(ROOT/'dispositions.json');c.sp=json.loads(SYNTHPROOF.read_text());c.sf=json.loads((SYNTHPROOF.parent/'family-verification.json').read_text())
 @classmethod
 def tearDownClass(c):
  for g in reversed(c.guards):g.stop()
 def test_actual_full_inventory_and_missing_disps(self):
  validate_projection(self.p);self.assertEqual((len(self.p.rows),len(self.p.nodes),len(self.p.dispositions)),(73,279,279));self.assertEqual(sum(d['disposition']=='unresolved' for d in self.p.dispositions),198);self.assertEqual(sum(d['disposition']=='structural' for d in self.p.dispositions),8)
 def test_allcanonical_bodies_tables_notes_links_exact(self):
  for row,pr in zip(self.p.rows,self.p.provenance):
   r=self.records[pr['rich_ir']['line_ordinal']];self.assertEqual(row['full_text'],r['semantic_html'])
   for k in ['notes_html','tables_html','links','image_references']:self.assertEqual(pr[k],r[k])
 def test_literal_toc_order_not_urlsort(self):
  order=[n['source_order'] for n in self.p.nodes];self.assertEqual(order,list(range(279)));self.assertNotEqual([p['rich_ir']['line_ordinal'] for p in self.p.provenance],list(range(73)));self.assertEqual(self.p.nodes[2]['source_url'],ROOT and 'https://phoenix.municipal.codes/Charter/PRE')
 def test_three_heading_callouts_ordinary_provenance(self):
  refs=[(p,a) for p in self.p.provenance for a in p['source_heading_links']];self.assertEqual(len(refs),3)
  for p,a in refs:self.assertTrue(a['same_owner_fragment']);self.assertEqual(a['target_count_in_own_article'],1);self.assertIn('class="fn"',p['source_heading_html']);self.assertIn(a['target_id'],p['source_heading_html'] if False else next(r['semantic_html'] for r in self.records if r['id']==p['locator']['canonical_url']))
 def test_real_falsegates_429_missing_closing(self):
  r=json.loads(artifacts(self.p)['validation-report.json']);self.assertFalse(r['complete']);self.assertFalse(r['selected_publication_ready']);self.assertFalse(self.p.inherited_coverage['start_end_inventory_consistent']);self.assertIn('429',str(self.p.inherited_coverage['errors']))
 def test_missing_owned_record_refuses(self):
  with patch.object(mc,'lines',return_value=self.records[:-1]):
   with self.assertRaisesRegex(ValueError,'Duplicate/missing'):mc.read_projection(ROOT,self.proof,self.family)
 def test_missing_resolved_disposition_refuses(self):
  self.altered({'dispositions.json':self.ds[:-1]},'reconcile')
 def altered(self,values,error,root=ROOT,proof=None,family=None):
  original=mc.load
  def load(p):return values.get(Path(p).name,original(p))
  with patch.object(mc,'load',side_effect=load):
   with self.assertRaisesRegex(ValueError,error):mc.read_projection(root,proof or self.proof,family or self.family)
 def test_missing_inventory_node_refuses(self):self.altered({'inventory.json':self.nodes[:-1]},'Duplicate/missing')
 def test_duplicate_raw_toc_route_refuses(self):
  raw=b'<ul class="contents-toc"><li><a href="/Code/A">A</a></li><li><a href="/Code/A">A</a></li></ul>'
  with self.assertRaisesRegex(ValueError,'Duplicate source contents'):mc.contents(raw,'https://x.municipal.codes/Code/contents','https://x.municipal.codes/Code')
 def test_source_order_is_recomputed_from_raw_not_cached_IR(self):
  original=mc.contents
  def changed(*a,**k):return list(reversed(original(*a,**k)))
  with patch.object(mc,'contents',side_effect=changed):
   # Reordering alone remains a new source order, but retained independent parent/ordinal witness must change.
   p=mc.read_projection(ROOT,self.proof,self.family);self.assertNotEqual(p.nodes,self.p.nodes)
 def test_corrupt_proof_refuses(self):
  p=copy.deepcopy(self.proof);p['verification']['family_report_sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'Wrong family'):mc.read_projection(ROOT,p,self.family)
 def test_foreign_family_refuses(self):
  p=copy.deepcopy(self.proof);p['family']='ecode'
  with self.assertRaisesRegex(ValueError,'Unsupported verification'):mc.read_projection(ROOT,p,self.family)
 def test_active_body_image_refuses(self):
  p=copy.deepcopy(self.p);p.rows[0]['full_text']='<img src="data:application/octet-stream;base64,NEVER">';p.provenance[0]['corpus_row_sha256']=sha(canonical(p.rows[0]))
  with self.assertRaisesRegex(ValueError,'Active image'):artifacts(p)
 def test_recursive_note_multiline_image_refuses(self):
  p=copy.deepcopy(self.p);p.provenance[0]['notes_html']=['<p data-pixel="DATA:IMAGE/PNG;base64,QUJD\nPIXELS">Caption</p>']
  with self.assertRaisesRegex(ValueError,'Image payload'):artifacts(p)
 def test_recursive_opaque_payload_refuses(self):
  p=copy.deepcopy(self.p);p.provenance[0]['source_heading_links']=[{'tag':'image','url':'data:application/octet-stream;base64,NEVER'}]
  with self.assertRaisesRegex(ValueError,'Opaque data payload'):artifacts(p)
 def test_synthetic_complete_positive_only(self):
  p=mc.read_projection(SYNTH,self.sp,self.sf);validate_projection(p);self.assertTrue(p.inherited_coverage['complete']);self.assertEqual((len(p.rows),len(p.nodes)),(2,3));self.assertFalse(json.loads(artifacts(p)['validation-report.json'])['complete'])
 def test_synthetic_image_only_and_table_placeholders(self):
  p=mc.read_projection(SYNTH,self.sp,self.sf);self.assertEqual(sum(r['full_text'].count('[IMAGE]') for r in p.rows),2);self.assertTrue(any('Cell caption' in r['full_text'] and 'colspan="2"' in r['full_text'] for r in p.rows));self.assertTrue(any('Footnote body.' in r['full_text'] for r in p.rows));self.assertEqual(sum(len(pr['source_heading_links']) for pr in p.provenance),1)
 def test_source_header_image_placeholder_without_decoder(self):
  raw=b'<main><article class="type-Section" id="A" data-history="/Code/A/history"><header>Caption<img src="data:application/octet-stream;base64,NEVER"></header></article></main>'
  h=mc.own_heading(raw,'https://x.municipal.codes/Code/A','https://x.municipal.codes/Code','https://x.municipal.codes/Code/A',{'https://x.municipal.codes/Code/A':{}});self.assertIn('Caption[IMAGE]',h['source_heading_html']);self.assertNotIn('NEVER',h['source_heading_html']);self.assertEqual(h['source_heading_image_placeholders'],1)
 def test_LF_only_offsets_preserve_control_characters(self):
  raw='<main>prefix\u2028\x1e\r<header>notowner</header>\n<article class="type-Section" id="A" data-history="/Code/A/history"><header>Heading\u2028Caption\x1e</header><p>Law.</p></article></main>'.encode()
  h=mc.own_heading(raw,'https://x.municipal.codes/Code/A','https://x.municipal.codes/Code','https://x.municipal.codes/Code/A',{});self.assertEqual(h['source_heading_html'],'<header>Heading\u2028Caption\x1e</header>')
 def test_header_table_caption_and_image_positions(self):
  raw=b'<article class="type-Section" id="A" data-history="/Code/A/history"><header>Caption<picture><source srcset="data:application/octet-stream;base64,NEVER"><img src="/map.png"></picture><table><tr><td background="/a.png">Cell</td></tr></table></header></article>'
  h=mc.own_heading(raw,'https://x.municipal.codes/Code/A','https://x.municipal.codes/Code','https://x.municipal.codes/Code/A',{});self.assertEqual(h['source_heading_image_placeholders'],2);self.assertIn('Caption[IMAGE]',h['source_heading_html']);self.assertIn('[IMAGE]Cell',h['source_heading_html']);self.assertNotIn('NEVER',h['source_heading_html'])
 def test_header_image_anchor_caption_preserved_payload_omitted(self):
  raw=b'<article class="type-Section" id="A" data-history="/Code/A/history"><header><a type="IMAGE/PNG" href="data:application/octet-stream;base64,NEVER">Map caption</a></header></article>'
  h=mc.own_heading(raw,'https://x.municipal.codes/Code/A','https://x.municipal.codes/Code','https://x.municipal.codes/Code/A',{});self.assertIn('Map caption[IMAGE]',h['source_heading_html']);self.assertNotIn('NEVER',str(h));self.assertEqual(h['source_heading_links'][0]['source_href'],'[IMAGE]')
 def test_synthetic_missing_closing_refuses(self):
  cp=mc.load(SYNTH/'checkpoint.json');cp['artifacts']=[a for a in cp['artifacts'] if a['role']!='contents-end'];self.altered({'checkpoint.json':cp},'closing',SYNTH,self.sp,self.sf)
if __name__=='__main__':unittest.main()
