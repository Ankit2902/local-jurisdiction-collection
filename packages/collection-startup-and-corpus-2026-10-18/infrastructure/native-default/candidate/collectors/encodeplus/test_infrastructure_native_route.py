"""Repository-shaped tests for the source-qualified registered native route."""
import copy,gzip,json,pathlib,unittest
from collectors.encodeplus import infrastructure_contents as m
BASE=pathlib.Path(__file__).resolve().parent
class RegisteredInfrastructureRoute(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.cfg=json.loads((BASE/'configs/native-82-0c6b3dc40877.json').read_text())
  cls.ir=json.loads(gzip.decompress((BASE/'fixtures/infrastructure-four-region/selected-ir.json.gz').read_bytes()))
 def source(self,number=2):
  d=copy.deepcopy(next(x for x in self.ir if x['physical_page']==number));old=d['original_record']['document_id'];r=json.loads(json.dumps(d['original_record']).replace(old,self.cfg['id']));r['source_url']=self.cfg['url']+'#page='+str(number);r['raw_ref']='raw/start.pdf'
  return d,r,{'id':self.cfg['id'],'url':self.cfg['url'],'raw_ref':'raw/start.pdf','expected_sha256':self.cfg['expected_sha256']}
 def test_exact_catalog_namespace_and_rawref_select_all_four(self):
  self.assertIn(self.cfg['url'],m.PROFILE['urls']);self.assertEqual(self.cfg['expected_sha256'],m.SOURCE_SHA256);self.assertEqual(self.cfg['expected_pages'],62);rows=[]
  for n in [2,3,6,46]:
   d,r,item=self.source(n);self.assertTrue(m.attach_retained_ir(r,d,item,m.SOURCE_SHA256));self.assertEqual(r['raw_ref'],'raw/start.pdf');self.assertEqual(r['document_id'],self.cfg['id']);self.assertEqual(r['canonical_structure_selection']['source_url'],self.cfg['url']+'#page='+str(n));rows.append(r)
  s=m.summary(rows);self.assertEqual((s['contents_entries'],s['source_words'],s['original_failed_detector_cells_retained']),(96,603,44));self.assertEqual(s['literal_leader_folio_spacing_discrepancies'],3)
 def test_unknown_alias_is_noop_without_native_access(self):
  d,r,item=self.source();item['url']=self.cfg['url'].replace('online.encodeplus.com','example.gov');before=copy.deepcopy(r)
  self.assertFalse(m.attach_record(r,object(),object(),item,m.SOURCE_SHA256));self.assertEqual(r,before)
 def test_known_route_wrong_record_source_hash_refuses_atomically(self):
  d,r,item=self.source();r['raw_sha256']='0'*64;before=copy.deepcopy(r)
  with self.assertRaises(ValueError):m.attach_retained_ir(r,d,item,m.SOURCE_SHA256)
  self.assertEqual(r,before)
 def test_known_route_changed_configured_source_refuses_atomically(self):
  d,r,item=self.source();item['expected_sha256']='0'*64;before=copy.deepcopy(r)
  with self.assertRaises(ValueError):m.attach_retained_ir(r,d,item,m.SOURCE_SHA256)
  self.assertEqual(r,before)
 def test_known_route_changed_native_body_refuses_atomically(self):
  d,r,item=self.source();d['native_text']+=' source drift';before=copy.deepcopy(r)
  with self.assertRaises(ValueError):m.attach_retained_ir(r,d,item,m.SOURCE_SHA256)
  self.assertEqual(r,before)
