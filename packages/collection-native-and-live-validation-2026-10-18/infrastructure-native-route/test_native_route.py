import ast,copy,gzip,hashlib,json,pathlib,unittest
from collectors.encodeplus import infrastructure_contents as m
BASE=pathlib.Path(__file__).resolve().parent
class NativeRoute(unittest.TestCase):
 def test_only_literal_observed_url_added(self):
  old=ast.literal_eval(ast.parse((BASE/'baseline-profile.py').read_text()).body[1].value)
  cfg=json.loads((BASE/'native-config.json').read_text());new=m.PROFILE
  self.assertEqual(new['urls'],old['urls']+[cfg['url']])
  self.assertEqual({k:v for k,v in new.items()if k!='urls'},{k:v for k,v in old.items()if k!='urls'})
  for name in ['start','end']:
   receipt=json.loads((BASE/f'{name}.pdf.receipt.json').read_text());self.assertEqual(receipt['url'],cfg['url']);self.assertEqual(receipt['sha256'],cfg['expected_sha256']);self.assertEqual(receipt['http_status'],200);self.assertFalse(receipt['challenge'])
 def test_exact_registered_url_and_namespace_select_all_four(self):
  cfg=json.loads((BASE/'native-config.json').read_text());ir=json.loads(gzip.decompress((BASE/'fixtures/infrastructure-four-region/selected-ir.json.gz').read_bytes()));out=[]
  for d in ir:
   oldid=d['original_record']['document_id'];r=json.loads(json.dumps(d['original_record']).replace(oldid,cfg['id']));r['source_url']=cfg['url']+'#page='+str(r['physical_page']);r['raw_ref']='raw/start.pdf'
   item={'id':cfg['id'],'url':cfg['url'],'raw_ref':'raw/start.pdf','expected_sha256':cfg['expected_sha256']}
   self.assertTrue(m.attach_retained_ir(r,d,item,cfg['expected_sha256']));self.assertEqual(r['canonical_structure_selection']['source_url'],r['source_url']);self.assertEqual(r['document_id'],cfg['id']);out.append(r)
  q=m.summary(out);self.assertTrue(q['finite_source_structure_complete']);self.assertEqual(q['contents_entries'],96);self.assertEqual(q['source_words'],603);self.assertEqual(q['original_failed_detector_cells_retained'],44);self.assertEqual(q['literal_leader_folio_spacing_discrepancies'],3)
 def test_unobserved_host_with_same_uuid_remains_noop(self):
  cfg=json.loads((BASE/'native-config.json').read_text());r={'physical_page':2};item={'url':cfg['url'].replace('online.encodeplus.com','example.gov')};self.assertFalse(m.attach_record(r,object(),object(),item,cfg['expected_sha256']));self.assertEqual(r,{'physical_page':2})
