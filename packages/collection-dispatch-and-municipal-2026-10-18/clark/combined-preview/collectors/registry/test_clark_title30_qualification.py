"""Finite source archive/receipt/config/scope faults; no native/image/network work."""
import copy,hashlib,json,sys,tempfile,unittest,zipfile,socket
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
from catalog import load_catalog
from dispatch import ROOT
from clark_title30_qualification import audit,ID,KIND,BUNDLE,MANIFEST,PATH
import followup_qualification
HERE=ROOT/'collectors/registry'
def read(p):return json.loads(p.read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
class Qualification(unittest.TestCase):
 def setUp(self):self.cat=load_catalog()
 def forbidden(self,*a,**kw):raise AssertionError('No native/image/network work')
 def stage(self,root):
  here=Path(root)/'collectors/registry';here.mkdir(parents=True);cfg=Path(root)/PATH;cfg.parent.mkdir(parents=True)
  cfg.write_bytes((ROOT/PATH).read_bytes())
  for n in [BUNDLE,MANIFEST,'followup-qualified-configs.json']:(here/n).write_bytes((HERE/n).read_bytes())
  return here
 def mutate_archive(self,here,member,fn):
  with zipfile.ZipFile(here/BUNDLE)as z:raw={n:z.read(n)for n in z.namelist()}
  raw[member]=fn(raw[member])
  with zipfile.ZipFile(here/BUNDLE,'w',zipfile.ZIP_DEFLATED)as z:
   for n,b in raw.items():z.writestr(n,b)
  m=read(here/MANIFEST);m['archive_sha256']=sha((here/BUNDLE).read_bytes());m['files']=[{'member':n,'bytes':len(b),'sha256':sha(b)}for n,b in raw.items()];(here/MANIFEST).write_text(json.dumps(m))
  q=read(here/'followup-qualified-configs.json');q['publications'][ID]['qualification_evidence']['source_archive_sha256']=m['archive_sha256'];(here/'followup-qualified-configs.json').write_text(json.dumps(q))
 def test_actual_portable_archive_passes_without_packages(self):
  with tempfile.TemporaryDirectory()as td,patch.object(socket,'socket',side_effect=self.forbidden):self.assertEqual(audit(self.stage(td),self.cat),[])
 def test_corrupt_archive_refuses(self):
  with tempfile.TemporaryDirectory()as td:
   h=self.stage(td);(h/BUNDLE).write_bytes((h/BUNDLE).read_bytes()+b'corrupt');self.assertTrue(audit(h,self.cat))
 def test_source_html_mutation_refuses_even_repacked_manifest(self):
  with tempfile.TemporaryDirectory()as td:
   h=self.stage(td)
   with zipfile.ZipFile(h/BUNDLE)as z:cp=json.loads(z.read('full30/run/checkpoint.json'))
   n='full30/run/'+cp['identity']['source_ref'];self.mutate_archive(h,n,lambda b:b.replace(b'Title 30 - Effective 9/17/2026',b'Historic unrelated book'))
   self.assertTrue(audit(h,self.cat))
 def test_native_closing_receipt_mutation_refuses(self):
  with tempfile.TemporaryDirectory()as td:
   h=self.stage(td)
   with zipfile.ZipFile(h/BUNDLE)as z:cp=json.loads(z.read('full30/run/checkpoint.json'))
   n='full30/run/'+cp['item_consistency'][0]['raw_ref'].removesuffix('.bin')+'.receipt.json'
   def change(b):x=json.loads(b);x['sha256']='0'*64;return json.dumps(x).encode()
   self.mutate_archive(h,n,change);self.assertTrue(audit(h,self.cat))
 def test_selector_and_scope_config_mutations_refuse(self):
  for key,value in [('inventory_selector','main a[href]'),('source_url','https://www.clarkcountynv.gov/other'),('coverage_level','publication_text'),('jurisdiction','Other County')]:
   with tempfile.TemporaryDirectory()as td:
    h=self.stage(td);f=Path(td)/PATH;c=read(f);c[key]=value;f.write_text(json.dumps(c));self.assertTrue(audit(h,self.cat),key)
 def test_owner_and_qualification_promotion_refuse(self):
  for key,value in [('target_id','95'),('validation_level','full_file_pages_live_verified'),('full_live_verified',True)]:
   c=copy.deepcopy(self.cat);next(p for p in c['publications']if p['id']==ID)[key]=value;self.assertTrue(audit(HERE,c),key)
 def test_router_arbitrary_extra_and_unknown_proof_kinds_refuse(self):
  original=Path.read_text;baseline=read(HERE/'followup-qualified-configs.json')
  for kind in ['not-a-qualified-proof',None,'historical-observed-native-receipt-full172-retained-current-parser','literal-current-publisher-anchor-and-pinned-original-native-file',KIND]:
   q=copy.deepcopy(baseline);q['publications']['fake-extra']={'qualification_evidence':{'kind':kind}}
   def patched(path,*a,**kw):return json.dumps(q)if path==HERE/'followup-qualified-configs.json'else original(path,*a,**kw)
   with patch.object(Path,'read_text',patched),patch.object(socket,'socket',side_effect=self.forbidden):errors=followup_qualification.audit(HERE,self.cat)
   self.assertTrue(errors,kind)
if __name__=='__main__':unittest.main(verbosity=2)
