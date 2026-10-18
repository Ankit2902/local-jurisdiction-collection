import contextlib,io,json,pathlib,shutil,socket,tempfile,unittest
from unittest.mock import patch
from PIL import Image
from pypdf.generic import EncodedStreamObject,DecodedStreamObject
import verify,acquire_county
CALLS=[]
def forbidden(*a,**k):CALLS.append('forbidden');raise AssertionError('Network/image API not permitted')
@contextlib.contextmanager
def guards():
 with contextlib.ExitStack() as s:
  for obj,key in [(socket,'socket'),(socket,'create_connection'),(Image,'open')]:s.enter_context(patch.object(obj,key,forbidden))
  for cls in [EncodedStreamObject,DecodedStreamObject]:
   old=cls.get_data
   def guard(self,*a,_old=old,**k):
    if str(self.get('/Subtype','')).lower()=='/image':return forbidden()
    return _old(self,*a,**k)
   s.enter_context(patch.object(cls,'get_data',guard))
  yield
class ProofTests(unittest.TestCase):
 def test_1_real_source_offline(self):
  with guards():r=verify.verify()
  self.assertTrue(r['passed']);self.assertEqual(CALLS,[])
 def corrupt(self,path,mutator):
  with tempfile.TemporaryDirectory() as td:
   b=pathlib.Path(td)/'proof';shutil.copytree(verify.BASE,b,ignore=shutil.ignore_patterns('__pycache__','MANIFEST.json'));p=b/path
   value=json.loads(p.read_text());mutator(value);p.write_text(json.dumps(value))
   with patch.object(verify,'BASE',b),guards(),self.assertRaises(AssertionError):verify.verify()
 def test_2_do_not_waive_historical_edition(self):self.corrupt('retained-chapter-binding/proof.json',lambda x:x.update(reusable_as_2011_edition_equivalent=True))
 def test_3_do_not_waive_county_semantics(self):self.corrupt('county-acquisition.json',lambda x:x.update(all_semantic_text_tables_reading_order_qualified=True))
 def test_4_wrong_county_file(self):self.corrupt('county-acquisition.json',lambda x:x.update(source_sha256='wrong'))
 def test_5_missing_chapter_middle_owner(self):self.corrupt('retained-chapter-binding/proof.json',lambda x:x['source_dom_order'].pop(10))
 def test_6_wrong_native_reference(self):self.corrupt('retained-chapter-binding/proof.json',lambda x:x.update(same_native_sha256='wrong'))
 def test_7_failed_HTTP_cannot_qualify(self):self.corrupt('raw/county-code.pdf.receipt.json',lambda x:x.update(status=403))
 def test_8_acquisition_refuses_existing_capture_before_network(self):
  with patch.object(acquire_county.transport,'fetch',forbidden),patch.object(acquire_county.transport,'reserve',forbidden),self.assertRaises(AssertionError):acquire_county.main()
  self.assertEqual(CALLS,[])
if __name__=='__main__':unittest.main(verbosity=2)
