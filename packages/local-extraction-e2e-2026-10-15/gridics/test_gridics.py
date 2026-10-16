"""Meaningful source-contract regressions; no network/browser needed."""
import csv,json,shutil,tempfile,unittest
from pathlib import Path
import gridics as g
from acquire import route_ready,wait_ready
ROOT=Path(__file__).parent
T='90d493fe-25f4-4aef-a519-710b1e0055c6'
C='af1e5183-6492-4f14-a5d9-0c3cde710367'
S='011aa4f1-de39-4414-9d76-38d0e105a203'
S2='111aa4f1-de39-4414-9d76-38d0e105a203'
U=g.BASE+'#/'+T

def node(uid,path,heading,body):return '<div class="section" id="section-'+uid+'" data-path="'+path+'">'+heading+body+'</div>'
def fixture():
 a=node(S,'/'+T+'/'+C+'/'+S,'<h4>1.01.010 Repeated.</h4>','<ol start="2" type="A"><li><p>Nested exactly once.</p><ul><li>Child item.</li></ul></li></ol><table><tr><th rowspan="2">Header</th><th>Limit</th></tr><tr><td colspan="2">3<sup>2</sup> H<sub>2</sub>O</td></tr></table><p>Before<img src="diagram.png" alt="Diagram"/>After <a href="#target">§ 2</a>.</p><aside>Footnote 1.</aside>')
 b=node(S2,'/'+T+'/'+C+'/'+S2,'<h4>1.01.010 Repeated.</h4>','<p>Distinct second publisher node.</p>')
 c=node(C,'/'+T+'/'+C,'<h3>CHAPTER 1.01: SAMPLE</h3>','<p>Substantive chapter introduction.</p>'+a+b)
 return node(T,'/'+T,'<h2>TITLE 1: SAMPLE</h2>','<span class="share-print">Print navigation poison</span>'+c)

class ParserTests(unittest.TestCase):
 def test_nested_blocks_once_and_parent_body_separate(self):
  ns,rs,ds=g.parse_html(fixture(),U);texts=[r['row']['full_text'] for r in rs]
  self.assertEqual(len(rs),3);self.assertEqual(sum(t.count('Nested exactly once.') for t in texts),1)
  self.assertEqual(texts[0],'Substantive chapter introduction.');self.assertNotIn('Print navigation poison',''.join(texts))
 def test_same_citation_distinct_node_survives(self):
  _,rs,_=g.parse_html(fixture(),U);self.assertEqual(rs[1]['row']['citation'],rs[2]['row']['citation']);self.assertNotEqual(rs[1]['record_id'],rs[2]['record_id'])
 def test_table_lists_notation_images_and_crossreferences(self):
  ns,rs,_=g.parse_html(fixture(),U);text=rs[1]['row']['full_text']
  for expected in ['<ol type="A" start="2">','<ul>','rowspan="2"','colspan="2"','3<sup>2</sup>','H<sub>2</sub>O','Before[IMAGE]After','§ 2','Footnote 1.']:self.assertIn(expected,text)
  self.assertEqual(text.count('[IMAGE]'),1);self.assertIn('diagram.png',ns[2]['structured_html'])
 def test_requested_uuid_not_merely_title(self):
  bad=U+'/'+C+'/'+S2.replace('111','222',1)
  self.assertFalse(route_ready(fixture(),bad,bad));self.assertFalse(route_ready(fixture(),U,U+'/'+C));self.assertFalse(route_ready(fixture(),U,U,'WRONG HEADING'))
  self.assertTrue(route_ready(fixture(),U,U,'TITLE 1: SAMPLE'))
 def test_shell_and_wrong_identity_fail_closed(self):
  for html in ['<h2>TITLE 1: SAMPLE</h2>',fixture().replace('section-'+S,'section-WRONG')]:
   with self.assertRaises(ValueError):g.parse_html(html,U)
 def test_scope_and_hash_identity(self):
  self.assertTrue(g.valid_route(U));self.assertNotEqual(g.digest(U),g.digest(U+'/'+C))
  for u in [g.BASE, U.replace('cupertino','miami'),U.replace('https','http'),U+'?wrong',U.replace('codehub.gridics.com','evil.example')]:self.assertFalse(g.valid_route(u))
 def test_real_retained_hierarchy_and_difficult_content(self):
  raw=(ROOT/'evidence/69693e089359e5b49b3d0bb00451050780864143.html').read_text();ns,rs,ds=g.parse_html(raw,U)
  self.assertEqual(len(ns),65);self.assertEqual(len(rs),58);self.assertEqual(sum(bool(r['row']['section_number']) for r in rs),56)
  self.assertEqual(sum(n['node_kind']=='container' and d['disposition']=='included' for n,d in zip(ns,ds)),2)
  table=next(r['row'] for r in rs if r['row']['section_number']=='1.09.030');self.assertIn('<table',table['full_text']);self.assertIn('<ol',table['full_text'])
 def test_real_nonanchor_inventory_retains_closed_branches(self):
  raw=(ROOT/'evidence/69693e089359e5b49b3d0bb00451050780864143.html').read_text();inv=g.inventory_html(raw)
  self.assertEqual(len(inv),30);self.assertEqual(sum(not r['children_enumerated'] for r in inv),25)
  chapter=next(n for n in inv if n['node_id']==C);self.assertEqual(chapter['parent_node_id'],T);self.assertEqual(chapter['source_url'],U+'/'+C)
 def test_async_readiness_waits_for_uuid_and_stable_legal_content(self):
  class FakePage:
   url=U
   samples=['<h2>TITLE 99: OLD ROUTE</h2>',fixture(),fixture(),fixture()]
   waits=0
   def content(self):return self.samples.pop(0) if len(self.samples)>1 else self.samples[0]
   def wait_for_timeout(self,n):self.waits+=1
  page=FakePage();html=wait_ready(page,U,5,'TITLE 1: SAMPLE')
  self.assertEqual(html,fixture());self.assertEqual(page.waits,3)
 def test_truncated_real_export_rejected(self):
  raw=(ROOT/'evidence/truncated-export.html').read_text()
  with self.assertRaisesRegex(ValueError,'Truncated browser export'):g.parse_html(raw,U)
 def test_fresh_live_title_inventory_reconciles_uuid_set(self):
  inv=json.loads((ROOT/'evidence/live-navigation.json').read_text());title={n['node_id'] for n in inv if n['path'].startswith('/'+T)}
  self.assertEqual(len(title),65);self.assertTrue(all(n['children_enumerated'] for n in inv if n['node_id'] in title))
  manifest=json.loads((ROOT/'live-manifest.json').read_text())
  for artifact in manifest['artifacts']:
   raw=(ROOT/artifact['path']).read_bytes();self.assertEqual(g.digest(raw),artifact['sha256'])
   ns,rs,ds=g.parse_html(raw.decode(),artifact['url']);self.assertEqual({n['node_id'] for n in ns},title);self.assertEqual(len(rs),58)
   self.assertTrue(route_ready(raw.decode(),artifact['url'],artifact['url']))
 def test_observed_compound_class_is_not_an_invented_uuid_route(self):
  f=next((ROOT/'standalone-failed-compound-identity/raw').glob('failed-*.html'));rows=g.inventory_html(f.read_text())
  group=next(n for n in rows if '--' in n['publisher_class_identity'] and n['display_heading']=='GENERAL PROVISIONS')
  self.assertEqual(group['node_id'],group['publisher_class_identity']);self.assertEqual(group['source_url'],'');self.assertEqual(group['candidate_source_url'],'')
  children=[n for n in rows if n['parent_node_id']==group['node_id']];self.assertGreater(len(children),0);self.assertTrue(all(not n['source_url'] and not n['candidate_source_url'] for n in children))
 def test_standalone_completed_routes_and_consistency_receipts(self):
  manifest=json.loads((ROOT/'standalone-final/snapshot-manifest.json').read_text())
  self.assertEqual(manifest['acquisition_status'],'completed_bounded_routes');self.assertEqual(len(manifest['artifacts']),3)
  for artifact in manifest['artifacts']:
   self.assertTrue(artifact['consistency']['equal']);self.assertEqual(artifact['consistency']['start_semantic_sha256'],artifact['consistency']['end_semantic_sha256'])
   self.assertEqual(g.digest((ROOT/'standalone-final'/artifact['path']).read_bytes()),artifact['sha256'])
 def test_cua_and_standalone_title1_semantics_match(self):
  def fingerprints(manifest):
   a=json.loads(manifest.read_text())['artifacts'][0];nodes,_,_=g.parse_html((manifest.parent/a['path']).read_text(),a['url'])
   return {n['node_id']:n['semantic_body_sha256'] for n in nodes}
  self.assertEqual(fingerprints(ROOT/'cua-acquisition/snapshot-manifest.json'),fingerprints(ROOT/'standalone-final/snapshot-manifest.json'))
 def test_all_observed_navigation_expanded_and_candidates_unqualified(self):
  rows=json.loads((ROOT/'navigation-acquisition/navigation-current.json').read_text());self.assertGreater(len(rows),1000)
  self.assertTrue(all(n['children_enumerated'] for n in rows));self.assertEqual(len(rows),len({n['node_id'] for n in rows}))
  self.assertTrue(all(n['route_qualification']=='matching_rendered_publisher_data_path' for n in rows if n['source_url']))
 def test_reserved_node_has_explicit_disposition(self):
  html=node(T,'/'+T,'<h2>TITLE 4: (RESERVED)</h2>','<p><br/></p>');ns,rs,ds=g.parse_html(html,U)
  self.assertFalse(rs);self.assertEqual(ds[0]['disposition'],'reserved_or_repealed')

class ReplayTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)
  (self.p/'a.html').write_text(fixture());(self.p/'b.html').write_text(fixture())
  self.m={'snapshot_id':'offline-test','source_version':'fixed-test-v1','artifacts':[{'path':f,'sha256':g.digest((self.p/f).read_bytes()),'url':U if f=='a.html' else U+'/'+C+'/'+S,'retrieved_at':'2026-10-15T00:00:00Z'} for f in ['a.html','b.html']]}
  g.save(self.p/'manifest.json',self.m)
 def tearDown(self):self.tmp.cleanup()
 def test_clean_resumed_replay_identical_and_deduped(self):
  clean=self.p/'clean';resume=self.p/'resume';g.replay(self.p/'manifest.json',clean);g.replay(self.p/'manifest.json',resume,1);g.replay(self.p/'manifest.json',resume)
  files=['aggregate-fulltext.json','aggregate-fulltext.csv','source-nodes.jsonl','node-dispositions.jsonl','record-provenance.jsonl']
  for f in files:self.assertEqual((clean/f).read_bytes(),(resume/f).read_bytes())
  j=json.loads((clean/'aggregate-fulltext.json').read_text());self.assertEqual(len(j['provisions']),3)
  with (clean/'aggregate-fulltext.csv').open(encoding='utf-8-sig',newline='') as f:self.assertEqual(list(csv.DictReader(f)),j['provisions'])
  self.assertEqual(len((clean/'node-dispositions.jsonl').read_text().splitlines()),4)
 def test_checkpoint_rejects_version_change(self):
  g.replay(self.p/'manifest.json',self.p/'out',1);self.m['source_version']='new-version';g.save(self.p/'manifest.json',self.m)
  with self.assertRaisesRegex(ValueError,'binding mismatch'):g.replay(self.p/'manifest.json',self.p/'out')
 def test_raw_hash_tamper_rejected(self):
  (self.p/'a.html').write_text('tampered')
  with self.assertRaisesRegex(ValueError,'hash mismatch'):g.replay(self.p/'manifest.json',self.p/'out')
 def test_source_path_escape_rejected(self):
  with self.assertRaisesRegex(ValueError,'escapes'):g.source_path(self.p,'../outside')
 def test_conflicting_duplicate_source_rejected(self):
  raw=fixture().replace('Distinct second publisher node.','Changed version.');(self.p/'b.html').write_text(raw);self.m['artifacts'][1]['sha256']=g.digest(raw);g.save(self.p/'manifest.json',self.m)
  with self.assertRaisesRegex(ValueError,'Conflicting'):g.replay(self.p/'manifest.json',self.p/'out')

if __name__=='__main__':unittest.main(verbosity=2)
