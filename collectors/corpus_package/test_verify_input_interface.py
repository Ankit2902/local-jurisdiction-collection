"""Bounded proof-report selection and verifier entrypoint controls."""
import json,tempfile,unittest,subprocess,sys,os
from pathlib import Path
from common import *
import package
from test_package import fixture
class Interface(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name).resolve();self.root,self.proof,self.family=fixture(self.base)
  d=load(self.proof);d.update(family_verification_path=self.family.name,family_verification_sha256=file_hash(self.family));self.proof.write_bytes(encoded(d))
 def tearDown(self):self.tmp.cleanup()
 def test_optional_proof_relative_json_report(self):
  r=package.run(self.root,self.proof,None,self.base/'out','originals-flagstaff-html-v1');self.assertTrue(r['package_verified']);self.assertFalse(r['complete'])
 def test_explicit_report_remains_supported(self):
  p=load(self.proof);p['family_verification_path']='../unsafe.json';self.proof.write_bytes(encoded(p));self.assertTrue(package.run(self.root,self.proof,self.family,self.base/'out','originals-flagstaff-html-v1')['package_verified'])
 def test_bad_default_paths_missing_reports_and_symlinks_refuse(self):
  original=load(self.proof);link=self.base/'symlink.json';link.symlink_to(self.family)
  for name in ['', '../family.json',str(self.family),'folder\\family.json','./family.json','missing.json','symlink.json']:
   with self.subTest(name=name):
    p=dict(original,family_verification_path=name);self.proof.write_bytes(encoded(p))
    with self.assertRaises((ValueError,FileNotFoundError)):package.run(self.root,self.proof,None,self.base/'out','originals-flagstaff-html-v1')
    self.assertFalse((self.base/'out').exists())
 def test_non_json_and_hash_mismatched_reports_refuse(self):
  original=load(self.proof)
  for content in [b'not JSON',b'{"wrong":"family"}\n']:
   self.family.write_bytes(content)
   with self.assertRaises((ValueError,json.JSONDecodeError)):package.run(self.root,self.proof,None,self.base/'out','originals-flagstaff-html-v1')
   self.assertFalse((self.base/'out').exists())
 def test_publication_id_unsafe_slug_refuses_before_writes(self):
  for value in ['../book','book/path','book\\path','with space','', 'a'*129]:
   out=self.base/'proof-out'
   r=subprocess.run([sys.executable,str(Path(__file__).with_name('verify_input.py')),'--reader','municode-html-publication-v1','--input',str(self.root),'--collector-root',str(self.base),'--publication-id',value,'--out',str(out)],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0);self.assertIn('safe caller-assigned stable slug',r.stderr);self.assertFalse(out.exists())
 def test_native_document_entrypoint_refuses_before_verifier_import(self):
  source=self.base/'collector';source.mkdir();(source/'verify.py').write_text('raise AssertionError("must not import")')
  inp=self.base/'native';inp.mkdir();(inp/'checkpoint.json').write_bytes(encoded({'phase':'finished','config':{'base':'https://source.test/regs/example/','mode':'native_document'}}))
  r=subprocess.run([sys.executable,str(Path(__file__).with_name('verify_input.py')),'--reader','encodeplus-html-publication-v1','--input',str(inp),'--collector-root',str(source),'--publication-id','native','--out',str(self.base/'proof-out')],capture_output=True,text=True)
  self.assertNotEqual(r.returncode,0);self.assertIn('native/page modes refuse',r.stderr);self.assertFalse((self.base/'proof-out').exists());self.assertFalse((source/'__pycache__').exists())
 def test_ordinary_python_no_bytecode_on_controlled_standard_verifier(self):
  source=self.base/'collector';source.mkdir();(source/'verify.py').write_text('def verify(root):\n return {"status":"synthetic control only"}\n')
  inp=self.base/'html';inp.mkdir();(inp/'checkpoint.json').write_bytes(encoded({'phase':'finished','config':{'base':'https://source.test/regs/example/'}}))
  r=subprocess.run([sys.executable,str(Path(__file__).with_name('verify_input.py')),'--reader','encodeplus-html-publication-v1','--input',str(inp),'--collector-root',str(source),'--publication-id','synthetic','--out',str(self.base/'proof-out')],capture_output=True,text=True)
  self.assertEqual(r.returncode,0,r.stderr);p=load(self.base/'proof-out/read-only-proof.json');self.assertEqual(p['collector_sources_before'],p['collector_sources_after']);self.assertEqual(p['verification']['runtime_before'],p['verification']['runtime_after']);self.assertFalse((source/'__pycache__').exists());self.assertEqual(p['family_verification_path'],'family-verification.json')
if __name__=='__main__':unittest.main()
