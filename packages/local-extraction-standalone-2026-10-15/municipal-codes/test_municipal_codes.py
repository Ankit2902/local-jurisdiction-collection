import csv,tempfile,unittest
from pathlib import Path
import municipal_codes_cli as m
B='https://bellingham.municipal.codes/BMC'
def card(i='s1',history='/BMC/1.01.010/history',body='<p>Legal body.</p>'):
 return '<article class="type-Section" id="'+i+'" data-short-cite="1.01.010" data-history="'+history+'"><header><span class="num">1.01.010</span> <span class="name">Adoption.</span></header>'+body+'</article>'
class Regressions(unittest.TestCase):
 def parse(self,h,url=None):return m.parse_page('<main>'+h+'</main>',url or B+'/1.01',B)
 def test_R01_Bellingham(self):
  base=m.publication_base(B+'/contents');self.assertTrue(m.allowed(B+'/1.01.010',base));self.assertFalse(m.allowed(B+'2/1',base));self.assertFalse(m.allowed(B+'/../Charter/1',base));self.assertFalse(m.allowed(B+'/%2e%2e/Charter',base))
 def test_R02_Everett(self):
  base=m.publication_base('https://everett.municipal.codes/EMC/contents');self.assertTrue(m.allowed(base+'/1.01.010',base));self.assertFalse(m.allowed('https://everett.municipal.codes/Charter/1',base))
 def test_R03_Contents(self):
  r,n=self.parse('<h1>Contents</h1><a href="/BMC/1">Title 1</a>');self.assertEqual(r,[]);self.assertEqual(n[0]['status'],'structural')
 def test_unprofiled_main_is_unresolved(self):
  r,n=self.parse('<h1>Section 1</h1><p>Legal words</p>');self.assertEqual(r,[]);self.assertEqual(n[0]['status'],'unresolved')
 def test_repeated_labels_and_cards(self):
  r,n=self.parse(card()+card('s2','/BMC/other/history'));self.assertEqual(len(r),2);self.assertEqual(r[0]['section_number'],r[1]['section_number']);self.assertNotEqual(r[0]['node_id'],r[1]['node_id'])
 def test_bundle_identity_stable(self):
  a,_=self.parse(card());b,_=self.parse(card(),B+'/1.01.010');self.assertEqual(a,b)
 def test_missing_identity_unresolved(self):
  r,n=self.parse('<article class="type-Section"><h1>1 Adoption</h1><p>Body</p></article>');self.assertEqual(r,[]);self.assertEqual(n[0]['status'],'unresolved')
 def test_data_id_does_not_invent_anchor(self):
  r,n=self.parse('<article class="type-Section" data-id="uuid"><h1>1 Adoption</h1><p>Body</p></article>');self.assertEqual(r[0]['source_url'],B+'/1.01');self.assertEqual(r[0]['locator']['attribute'],'data-id')
 def test_semantic_structures_once(self):
  r,_=self.parse(card(body='<p>A<sup>2</sup> H<sub>2</sub>O <a href="/BMC/2">reference</a>.</p><ol start="3" type="A"><li value="4"><p>Nested once</p><ul><li>inner</li></ul></li></ol><table><tr><th rowspan="2">Header</th><td colspan="2">Cell</td></tr></table><p>Note<img alt="Map" src="/a.png"></p>'))
  t=r[0]['full_text'];self.assertEqual(t.count('Nested once'),1)
  for v in ('rowspan="2"','colspan="2"','start="3"','value="4"','<sup>2</sup>','<sub>2</sub>','[IMAGE] Map'):self.assertIn(v,t)
  self.assertIn('href="/BMC/2"',r[0]['content_html'])
 def test_parent_body_without_descendant_duplication(self):
  r,_=self.parse('<article class="type-Chapter" id="ch1" data-history="/BMC/1.01/history"><header>Chapter 1</header><p>Operative intro.</p>'+card()+'</article>');self.assertEqual(len(r),2);self.assertIn('Operative intro',r[0]['full_text']);self.assertNotIn('Legal body',r[0]['full_text']);self.assertEqual(r[0]['section_number'],'')
 def test_challenge_rejected(self):
  with self.assertRaises(m.QualificationError):m.parse_page('<title>Just a moment...</title><main>'+card()+'</main>',B+'/1',B)
 def test_independent_inventory(self):
  inv=m.inventory('<main><ul id="toc"><li><a href="/BMC/1">Title</a><ul><li><a href="/BMC/1.01">Chapter</a><button aria-expanded="false">Expand</button></li></ul></li><li><a href="/Charter/1">Other</a></li></ul></main>',B+'/contents',B,'#toc');self.assertEqual(len(inv['nodes']),2);self.assertEqual(inv['nodes'][1]['parent_node_id'],'url:'+B+'/1');self.assertGreater(inv['pending_controls'],0);self.assertEqual(inv['completeness'],'unverified')
 def fixture(self,p):
  raw=('<main>'+card()+'</main>').encode();(p/'a.html').write_bytes(raw);(p/'b.html').write_bytes(raw)
  inv={'publication_base':B,'completeness':'unverified','nodes':[{'node_id':'url:'+B+'/1.01.010','source_url':B+'/1.01.010','source_order':0},{'node_id':'url:'+B+'/missing','source_url':B+'/missing','source_order':1}]};m.write_json(p/'inventory.json',inv)
  obj={'jurisdiction_slug':'bellingham-wa','jurisdiction':'Bellingham','publication_id':'municipal-code','publication_title':'Municipal Code','publication_base':B,'source_version':'synthetic-v1','retrieved_at':'2026-10-15','inventory':{'path':'inventory.json','sha256':m.sha(m.canonical(inv))},'snapshots':[{'path':'a.html','source_url':B+'/1.01','sha256':m.sha(raw)},{'path':'b.html','source_url':B+'/1.01.010','sha256':m.sha(raw)}]};m.write_json(p/'manifest.json',obj);return obj
 def test_clean_resume_dedup_and_exports(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);self.fixture(p);m.replay(p/'manifest.json',p/'clean');m.replay(p/'manifest.json',p/'resume',1);m.replay(p/'manifest.json',p/'resume')
   for n in ('aggregate-fulltext.json','node-dispositions.jsonl','record-provenance.jsonl'):self.assertEqual((p/'clean'/n).read_bytes(),(p/'resume'/n).read_bytes())
   o=m.read_json(p/'clean/aggregate-fulltext.json');self.assertEqual(len(o['provisions']),1);self.assertFalse(o['metadata']['whole_corpus_validated']);self.assertEqual(m.read_json(p/'clean/validation-report.json')['unresolved_dispositions'],1)
   with (p/'clean/aggregate-fulltext.csv').open(encoding='utf-8-sig',newline='') as f:self.assertEqual(list(csv.DictReader(f)),o['provisions'])
 def test_version_checkpoint_mismatch(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);o=self.fixture(p);m.replay(p/'manifest.json',p/'out',1);o['source_version']='v2';m.write_json(p/'manifest.json',o)
   with self.assertRaisesRegex(m.QualificationError,'Checkpoint'):m.replay(p/'manifest.json',p/'out')
 def test_revalidates_cached_hash_on_resume(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);self.fixture(p);m.replay(p/'manifest.json',p/'out',1);(p/'a.html').write_text('changed')
   with self.assertRaisesRegex(m.QualificationError,'hash'):m.replay(p/'manifest.json',p/'out')
 def test_conflicting_body_same_identity(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);o=self.fixture(p);raw=('<main>'+card(body='<p>Changed.</p>')+'</main>').encode();(p/'b.html').write_bytes(raw);o['snapshots'][1]['sha256']=m.sha(raw);m.write_json(p/'manifest.json',o)
   with self.assertRaisesRegex(m.QualificationError,'Conflicting'):m.replay(p/'manifest.json',p/'out')
if __name__=='__main__':unittest.main(verbosity=2)
