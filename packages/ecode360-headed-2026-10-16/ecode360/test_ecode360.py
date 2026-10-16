import copy,csv,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup
import ecode360 as e
ROOT=Path(__file__).parent

class ParserTests(unittest.TestCase):
 def setUp(self):
  self.html=(ROOT/'fixtures/semantic.html').read_text()
  self.ident,self.rows=e.parse_page(self.html,'https://ecode360.com/101')
 def inventory(self):
  nodes=e.inventory_candidate(self.html,'https://ecode360.com/100')['nodes']
  for n in nodes:n['classification']='substantive'
  return {'jurisdiction_slug':'test-ca','jurisdiction':'Test','publication_id':'municipal-code','code_name':'Code',
          'identity':self.ident,'source_version':'fixture-v1','inventory_complete':False,'inventory_evidence':{'synthetic':True},'scrape_date':'2026-10-15','nodes':nodes}
 def sources(self,base,duplicate=True):
  (base/'one.html').write_text(self.html)
  artifacts=[{'path':'one.html','sha256':e.digest(self.html.encode()),'url':'https://ecode360.com/101'}]
  if duplicate:artifacts.append(dict(artifacts[0],url='https://ecode360.com/102'))
  e.dump(base/'inventory.json',self.inventory());e.dump(base/'artifacts.json',{'artifacts':artifacts})
  return base/'inventory.json',base/'artifacts.json'
 def test_repeated_printed_labels_and_family_identity(self):
  self.assertEqual(len(self.rows),4)
  self.assertEqual(self.rows[1]['citation'],self.rows[2]['citation'])
  self.assertNotEqual(self.rows[1]['node_id'],self.rows[2]['node_id'])
  self.assertNotEqual(e.node_key('test','code','101'),e.node_key('test','charter','101'))
 def test_semantic_fidelity_once_and_order(self):
  r=self.rows[1];body=r['full_text']
  for token in ('ALPHA-ONLY','NESTED-ONCE','INNER-ONCE','NOTE-ONCE'):
   self.assertEqual(body.count(token),1)
  for token in ('rowspan="2"','colspan="2"','<caption>Legal rates</caption>','<sup>2</sup>','<sub>2</sub>','<ol start="3">'):
   self.assertIn(token,body)
  self.assertLess(body.index('IMAGE-BEFORE'),body.index('[IMAGE]'));self.assertLess(body.index('[IMAGE]'),body.index('IMAGE-AFTER'))
  self.assertEqual(r['images'],[{'order':1,'url':'https://ecode360.com/map.png','alt':'District map'}])
  self.assertIn('https://ecode360.com/100#102',r['semantic_html'])
 def test_ecode_nested_litem_and_history_once(self):
  body=self.rows[2]['full_text'];self.assertEqual(body.count('DEEP-ONCE'),1);self.assertIn('(a)',body);self.assertIn('(1)',body);self.assertEqual(body.count('HISTORY-ONCE'),1)
  self.assertIn('class="litem"',self.rows[2]['semantic_html'])
 def test_parent_and_unnumbered_body(self):
  self.assertIn('PARENT-BODY',self.rows[0]['full_text']);self.assertNotIn('CHILD-CONTENT',self.rows[0]['full_text'])
  self.assertEqual(self.rows[3]['display_number'],'');self.assertIn('UNNUMBERED-OPERATIVE',self.rows[3]['full_text'])
 def test_missing_body_never_borrows_next_section(self):
  s=BeautifulSoup(self.html,'html.parser');s.find(id='101_content').decompose()
  _,rows=e.parse_page(str(s),'https://ecode360.com/100');self.assertNotIn('101',[r['node_id'] for r in rows]);self.assertIn('102',[r['node_id'] for r in rows])
 def test_navigation_no_legal_records(self):
  s=BeautifulSoup(self.html,'html.parser')
  for a in s.select('article'):a.decompose()
  self.assertEqual(e.parse_page(str(s),'https://ecode360.com/100')[1],[])
 def test_challenge_and_wrong_version_rejected(self):
  with self.assertRaises(e.ValidationError):e.parse_page('<title>Just a moment...</title>','https://ecode360.com/100')
  with self.assertRaises(e.ValidationError):e.parse_page(self.html,'https://ecode360.com/100',dict(self.ident,code_id='wrong'))
 def test_inventory_hierarchy_and_not_complete(self):
  c=e.inventory_candidate(self.html,'https://ecode360.com/100');self.assertFalse(c['inventory_complete']);self.assertEqual(c['nodes'][1]['parent_node_id'],'100')
 def test_host_only_scope_not_accepted(self):
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);ip,ap=self.sources(base)
   with self.assertRaises(e.ValidationError):e.import_snapshot(ip,base/'one.html','https://ecode360.com/999',base/'import')
  for bad in ('https://ecode360.com.evil.test/100','https://ecode360.com/laws/TE0000','http://ecode360.com/100','https://ecode360.com/100?code=other'):
   with self.assertRaises(e.ValidationError):e.fetch_url(bad)
 def test_snapshot_import_version_and_duplicate(self):
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);ip,ap=self.sources(base);dest=base/'import'
   e.import_snapshot(ip,base/'one.html','https://ecode360.com/101',dest)
   e.import_snapshot(ip,base/'one.html','https://ecode360.com/101',dest)
   self.assertEqual(len(e.load(dest/'artifacts.json')['artifacts']),1)
 def test_replay_deduplication_and_sidecars(self):
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);ip,ap=self.sources(base);out=base/'out';r=e.replay(ip,ap,out)
   self.assertEqual(r['included_record_count'],4);self.assertEqual(r['errors'],[])
   rows=e.load(out/'aggregate-fulltext.json')['provisions'];self.assertEqual(rows[1]['section_number'],rows[2]['section_number'])
   disp=[json.loads(x) for x in (out/'node-dispositions.jsonl').read_text().splitlines()]
   self.assertEqual(len(disp),4);self.assertEqual(len({d['node_key'] for d in disp}),4)
   with (out/'aggregate-fulltext.csv').open(encoding='utf-8-sig',newline='') as f:self.assertEqual(list(csv.DictReader(f)),rows)
 def test_clean_and_interrupted_resume_equal(self):
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);ip,ap=self.sources(base)
   e.replay(ip,ap,base/'clean');self.assertEqual(e.replay(ip,ap,base/'resumed',stop_after=1)['status'],'interrupted')
   e.replay(ip,ap,base/'resumed')
   for name in ('aggregate-fulltext.json','aggregate-fulltext.csv','aggregate-toc.json','node-dispositions.jsonl','record-provenance.jsonl','validation-report.json'):
    self.assertEqual((base/'clean'/name).read_bytes(),(base/'resumed'/name).read_bytes(),name)
 def test_checkpoint_refuses_version_config_artifact_change(self):
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);ip,ap=self.sources(base);out=base/'out';e.replay(ip,ap,out,stop_after=1)
   inv=e.load(ip);inv['source_version']='different';e.dump(ip,inv)
   with self.assertRaises(e.ValidationError):e.replay(ip,ap,out)
 def test_hash_tamper_remains_unresolved(self):
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);ip,ap=self.sources(base,False);(base/'one.html').write_text(self.html+'tamper')
   with self.assertRaisesRegex(e.ValidationError,'SHA-256'):e.replay(ip,ap,base/'out')
   self.assertFalse((base/'out/aggregate-fulltext.json').exists())
 def test_processed_checkpoint_rehashes_source_bytes(self):
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);ip,ap=self.sources(base);out=base/'out';e.replay(ip,ap,out)
   (base/'one.html').write_text(self.html+'tamper')
   with self.assertRaisesRegex(e.ValidationError,'SHA-256'):e.replay(ip,ap,out)
 def test_inventory_identity_collision_refused(self):
  inv=self.inventory();inv['nodes'].append(copy.deepcopy(inv['nodes'][0]))
  with self.assertRaises(e.ValidationError):e.validate_inventory(inv)
 def test_no_release_on_partial_inventory(self):
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);ip,ap=self.sources(base)
   with self.assertRaises(e.ValidationError):e.replay(ip,ap,base/'release',release=True)
   self.assertFalse((base/'release/aggregate-fulltext.json').exists())
   self.assertFalse(e.load(base/'release/validation-report.json')['release_eligible'])
 def test_no_hiding_parent_body_behind_structural_label(self):
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);ip,ap=self.sources(base);inv=e.load(ip);inv['nodes'][0].update(classification='structural',classification_evidence='synthetic test');e.dump(ip,inv)
   r=e.replay(ip,ap,base/'out');self.assertEqual(r['unresolved_node_count'],1);self.assertIn('operative body',r['errors'][0]['error'])
 def test_acquisition_queue_resumes_and_binds(self):
  with tempfile.TemporaryDirectory() as tmp:
   base=Path(tmp);ip,ap=self.sources(base);inv=e.load(ip);inv['acquisition_units']=[{'url':'https://ecode360.com/101','evidence':'fixture TOC'},{'url':'https://ecode360.com/102','evidence':'fixture TOC'}];e.dump(ip,inv)
   def fake(url,out):
    out.mkdir(parents=True,exist_ok=True);(out/'one.html').write_text(self.html)
    return {'route_verified':True,'identity':self.ident,'raw_path':'one.html','raw_sha256':e.digest(self.html.encode()),'final_url':url,'retrieved_at':'2026-10-15'}
   with patch.object(e,'acquire',fake):
    self.assertEqual(e.collect(ip,base/'queue',1,0)['acquired_artifacts'],1)
    self.assertEqual(e.collect(ip,base/'queue',1,0)['acquired_artifacts'],2)
   inv['source_version']='changed';e.dump(ip,inv)
   with self.assertRaises(e.ValidationError):e.collect(ip,base/'queue')
 def test_current_exact_dom_excerpt(self):
  folder=ROOT/'fixtures/current-santa-monica'
  with tempfile.TemporaryDirectory() as tmp:
   r=e.replay(folder/'inventory.json',folder/'artifacts.json',Path(tmp))
   self.assertEqual(r['errors'],[]);self.assertEqual(r['included_record_count'],1)
   self.assertEqual(r['unresolved_node_count'],0);self.assertFalse(r['inventory_complete'])
   records=e.load(Path(tmp)/'aggregate-fulltext.json')['provisions']
   self.assertEqual(records[0]['section_number'],'1.01.010')
   self.assertIn('Prior code § 1100',records[0]['full_text'])
   self.assertTrue(records[0]['full_text'].startswith('This Code shall be known as'))
 def test_family_candidates_not_silently_omitted(self):
  html=self.html.replace('<nav id="toc">','<nav id="toc"><div class="contentTitle" data-guid="900"><a class="titleLink" href="/900">The Charter</a></div>')
  candidate=e.inventory_candidate(html,'https://ecode360.com/100')
  self.assertEqual(candidate['unclassified_family_candidates'][0]['node_id'],'900')
  self.assertFalse(candidate['inventory_complete'])
 def test_parser_file_hash_binds_resume(self):
  inv=self.inventory();manifest={'artifacts':[]}
  with patch.object(e.Path,'read_bytes',return_value=b'parser old'):
   old=e.binding(inv,manifest)
  with patch.object(e.Path,'read_bytes',return_value=b'parser new'):
   self.assertNotEqual(old,e.binding(inv,manifest))
 def test_historical_dom_all_twelve(self):
  summaries=e.load(ROOT/'evidence/historical-fixtures.json');self.assertEqual(len(summaries),12)
  total=0
  with tempfile.TemporaryDirectory() as tmp:
   for summary in summaries:
    with self.subTest(slug=summary['slug']):
     folder=ROOT/'fixtures/historical'/summary['slug'];report=e.replay(folder/'inventory.json',folder/'artifacts.json',Path(tmp)/summary['slug'])
     self.assertEqual(report['errors'],[]);self.assertEqual(report['unresolved_node_count'],0)
     self.assertEqual(report['included_record_count'],summary['node_count']);self.assertEqual(report['included_record_count'],summary['parsed_record_count'])
     self.assertFalse(report['full_collection_verified']);total+=report['included_record_count']
  expected_counts={'burlingame-ca':1,'emeryville-ca':7,'half-moon-bay-ca':10,'malibu-ca':28,'san-leandro-ca':1,'santa-clara-ca':4,'santa-monica-ca':9,'santa-rosa-ca':13,'south-san-francisco-ca':8,'sunnyvale-ca':8,'west-hollywood-ca':10,'tukwila-wa':16}
  self.assertEqual({s['slug']:s['node_count'] for s in summaries},expected_counts)
  self.assertEqual(total,sum(expected_counts.values()))

if __name__=='__main__':unittest.main()
