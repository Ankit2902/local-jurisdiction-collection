"""Whole actual6-page source and corrupted real export tests. No network/images."""
import contextlib,csv,hashlib,io,json,pathlib,shutil,socket,tempfile,unittest
from unittest.mock import patch
import pymupdf
from PIL import Image
from pypdf.generic import EncodedStreamObject,DecodedStreamObject
import extract_logical,independent_audit
BASE=pathlib.Path(__file__).resolve().parents[1]
DATA=(BASE/'source.pdf').read_bytes()
CALLS=[]
def forbidden(*a,**kw):CALLS.append('forbidden');raise AssertionError('Network/image/pixel API forbidden')
@contextlib.contextmanager
def no_images_network():
 with contextlib.ExitStack() as stack:
  for obj,name in [(socket,'socket'),(socket,'create_connection'),(Image,'open'),(pymupdf.Document,'extract_image'),(pymupdf.Page,'get_pixmap')]:stack.enter_context(patch.object(obj,name,forbidden))
  for cls in [EncodedStreamObject,DecodedStreamObject]:
   original=cls.get_data
   def guard(self,*a,_original=original,**kw):
    if str(self.get('/Subtype','')).lower()=='/image':return forbidden()
    return _original(self,*a,**kw)
   stack.enter_context(patch.object(cls,'get_data',guard))
  yield

def rows(path):return [json.loads(s) for s in path.read_text().splitlines()]
def put(path,values):path.write_text(''.join(json.dumps(v,ensure_ascii=False,sort_keys=True)+'\n' for v in values))
class WholeSource(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.canonical=pathlib.Path(cls.tmp.name)/'canonical'
  with no_images_network():
   cls.result=extract_logical.write(DATA,cls.canonical);cls.audit=independent_audit.audit(DATA,cls.canonical)
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def corrupt(self,file,mutator,sync_csv=False):
  with tempfile.TemporaryDirectory() as td:
   target=pathlib.Path(td)/'copy';shutil.copytree(self.canonical,target)
   values=rows(target/file);mutator(values);put(target/file,values)
   if sync_csv:
    fields=['id','unit_type','parent_id','source_label','text','source_tag_id','source_pages','source_sha256']
    with (target/'logical-units.csv').open('w',newline='') as f:
     w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows({**r,'source_pages':json.dumps(r['source_pages'])} for r in values)
   with no_images_network(),self.assertRaises((AssertionError,KeyError,StopIteration)):independent_audit.audit(DATA,target)
 def test_01_actual_all_six_pages(self):
  self.assertTrue(self.audit['passed']);self.assertEqual(self.audit['logical_units'],88);self.assertEqual(self.audit['controls'],26);self.assertEqual(self.audit['content_refs'],109);self.assertEqual(self.audit['source_glyphs'],15574);self.assertTrue(self.audit['canonical_csv_agrees']);self.assertEqual(CALLS,[])
 def test_02_missing_middle_unit(self):self.corrupt('logical-units.jsonl',lambda v:v.pop(37),True)
 def test_03_duplicate_middle_unit(self):self.corrupt('logical-units.jsonl',lambda v:v.insert(37,v[36]),True)
 def test_04_crosspage_alpha_list_wrong_parent(self):
  def f(v):next(r for r in v if r['logical_key']=='7.36-1.B.2.a')['parent_id']='native-82-4b983dc51ab6::7.36-1.B.1'
  self.corrupt('logical-units.jsonl',f,True)
 def test_05_residential_commercial_scope_swap(self):
  def f(v):next(r for r in v if r['logical_key']=='7.36-3.B.Commercial.1')['parent_id']='native-82-4b983dc51ab6::7.36-3.B.Residential'
  self.corrupt('logical-units.jsonl',f,True)
 def test_06_split_crosspage_D(self):
  def f(v):r=next(r for r in v if r['logical_key']=='7.36-5.D');r['source_refs']=r['source_refs'][:1];r['source_pages']=[5]
  self.corrupt('logical-units.jsonl',f,True)
 def test_07_join_printed_hyphen(self):
  def f(v):r=next(r for r in v if r['logical_key']=='7.36-5.G');self.assertIn('rights-of-\nway.',r['text']);r['text']=r['text'].replace('rights-of-\nway.','rights-of-way.')
  self.corrupt('logical-units.jsonl',f,True)
 def test_08_footer_leaks_into_body(self):self.corrupt('logical-units.jsonl',lambda v:v[8].update(text=v[8]['text']+' 7/21/2011 7-21-11 AM Page 1'),True)
 def test_09_glyph_codepoint_corruption(self):self.corrupt('source-glyphs.jsonl',lambda v:v[900].update(text='X'))
 def test_10_original_CID_corruption(self):self.corrupt('source-glyphs.jsonl',lambda v:v[900].update(cid=v[900]['cid']+1))
 def test_11_original_position_corruption(self):
  def f(v):v[900]['matrix'][4]+=.5
  self.corrupt('source-glyphs.jsonl',f)
 def test_12_missing_word(self):self.corrupt('source-words.jsonl',lambda v:v.pop(150))
 def test_13_duplicate_word(self):self.corrupt('source-words.jsonl',lambda v:v.append(v[100]))
 def test_14_wrong_word_owner(self):self.corrupt('source-words.jsonl',lambda v:v[200].update(logical_owner_id='wrong'))
 def test_15_missing_Artifact_control(self):self.corrupt('source-controls.jsonl',lambda v:v.pop())
 def test_16_lost_original_linebreak(self):
  def f(v):r=next(r for r in v if r['logical_key']=='7.36-5.G');r['source_lines'][0]['raw_text']+='invented'
  self.corrupt('logical-units.jsonl',f,True)
 def test_17_csv_not_parallel_bad_export(self):
  with tempfile.TemporaryDirectory() as td:
   target=pathlib.Path(td)/'copy';shutil.copytree(self.canonical,target);p=target/'logical-units.csv';p.write_text(p.read_text().replace('behind the existing building line','behind an invented building line'))
   with no_images_network(),self.assertRaises(AssertionError):independent_audit.audit(DATA,target)
 def test_18_wrong_source_edition_rejected_before_interpretation(self):
  for changed in [DATA+b'\n',DATA[:100]+bytes([DATA[100]^1])+DATA[101:]]:
   self.assertNotEqual(hashlib.sha256(changed).hexdigest(),independent_audit.PIN)
   with no_images_network(),self.assertRaises(AssertionError):extract_logical.build(changed)
 def test_19_false_resolved_dependency_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   target=pathlib.Path(td)/'copy';shutil.copytree(self.canonical,target);p=target/'source-dependency-inventory.json';v=json.loads(p.read_text());v['textual_dependencies'][0]['resolved_in_this_packet']=True;p.write_text(json.dumps(v))
   with no_images_network(),self.assertRaises(AssertionError):independent_audit.audit(DATA,target)
 def test_20_reordered_legal_units(self):
  def f(v):v[27],v[28]=v[28],v[27]
  self.corrupt('logical-units.jsonl',f,True)
 def test_21_no_images_or_payloads_in_all_canonical_exports(self):
  self.assertEqual(CALLS,[])
  for p in self.canonical.iterdir():
   text=p.read_text().lower();self.assertNotIn('data:image',text);self.assertNotIn('base64,',text);self.assertNotIn('<img',text);self.assertNotIn('<svg',text)
  inv=self.result['dependency_inventory'];self.assertTrue(all(inv[k]==0 for k in ['embedded_files','annotations','inline_images','image_xobjects']));self.assertEqual(inv['table_disposition']['applicability'],'not-applicable')
if __name__=='__main__':unittest.main(verbosity=2)
