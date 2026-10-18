"""Clark source-bound configuration dispatch tests; no publisher/native/image work.

Optional CLARK_PROOF_ROOT points to the relocated sealed full30 proof directory.
These tests exercise planning/dispatch and retained-proof identity, not a fresh
common family-verifier run. That all-page verification is sealed in the proof.
"""
import copy,hashlib,importlib.util,io,json,os,socket,subprocess,sys,tempfile,unittest,zipfile
from contextlib import redirect_stdout,redirect_stderr
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup
sys.path.insert(0,str(Path(__file__).resolve().parent))
from catalog import load_catalog
from dispatch import ROOT,Unsupported,qualified,command,bind_run
ID='96-7e8795b1baee';CONFIG='collectors/official/configs/clark-title30-current-associated-documents.json'
PROOF=Path(os.environ.get('CLARK_PROOF_ROOT',ROOT/'packages/collection-source-recovery-2026-10-18/clark/full30'))
def read(p):return json.loads(Path(p).read_text())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class Clark(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  global PROOF
  if not (PROOF/'run/checkpoint.json').is_file():
   # Source-only snapshots carry this audited documentary archive, not native PDFs.
   temp=tempfile.TemporaryDirectory();cls.addClassCleanup(temp.cleanup);PROOF=Path(temp.name)
   with zipfile.ZipFile(ROOT/'collectors/registry/clark-title30-source-evidence.zip')as z:
    cp=json.loads(z.read('full30/run/checkpoint.json'));names=['config.json','run/config.json','run/checkpoint.json','run/coverage.json','source-inventory.json','verify.stdout','run/'+cp['identity']['source_ref']]+['run/executed/'+n for n in cp['scripts']]
    for n in names:
     dest=PROOF/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read('full30/'+n))
  cls.cat=load_catalog();cls.pub=next(p for p in cls.cat['publications']if p['id']==ID);cls.target=next(t for t in cls.cat['targets']if t['id']=='96');cls.cfg=read(ROOT/CONFIG)
 def forbidden(self,*a,**kw):raise AssertionError('No network or family/native/image execution')
 def test_01_exact_tested_config_and_narrow_scope(self):
  self.assertEqual((ROOT/CONFIG).read_bytes(),(PROOF/'config.json').read_bytes());self.assertEqual(self.cfg['coverage_level'],'file_pages');self.assertEqual(self.cfg['mode'],'pdf_set');self.assertEqual(self.cfg['transport'],'http');self.assertEqual(self.cfg['document_transport'],'http');self.assertIn('9/17/2026',self.cfg['inventory_selector']);self.assertEqual(self.pub['validation_level'],'mapped_only');self.assertFalse(self.pub['full_live_verified']);self.assertTrue(self.pub['qualification_evidence']['full_file_pages_live_verified']);self.assertFalse(self.pub['qualification_evidence']['legal_semantic_coverage_complete']);self.assertFalse(self.pub['qualification_evidence']['jurisdiction_complete'])
 def test_02_current_inventory_not_legacy(self):
  s=read(PROOF/'run/checkpoint.json');html=(PROOF/'run'/s['identity']['source_ref']).read_bytes();soup=BeautifulSoup(html,'html.parser');self.assertEqual(len(soup.select(self.cfg['source_currency_selector'])),1);selected=soup.select(self.cfg['inventory_selector']);prior=read(PROOF/'source-inventory.json');self.assertEqual([(a['href'],a.get_text(' ',strip=True))for a in selected],[(a['url'],a['label'])for a in prior['current_documents']]);self.assertEqual(len(selected),30);self.assertEqual(len(prior['historical_documents_explicitly_outside_current_group']),66)
 def test_03_plan_and_configuration_identity(self):
  p=command(self.pub,self.target,'/fresh/clark',sys.executable);self.assertEqual(p['qualified_config_path'],CONFIG);self.assertIsNone(p['staged_config']);self.assertEqual(p['argv'],[sys.executable,'collectors/official/collect.py','--config',CONFIG,'--out','/fresh/clark']);self.assertFalse(p['jurisdiction_complete']);self.assertEqual(qualified(self.pub,self.target)['config'],self.cfg)
 def test_04_missing_or_wrong_source_configuration_refuses(self):
  for changes in [{'adapter_config_path':'collectors/official/configs/MISSING-clark.json'},{'source_url':'https://www.clarkcountynv.gov/NOT-THE-OBSERVED-PUBLICATION'}]:
   p=copy.deepcopy(self.pub);p.update(changes)
   with self.assertRaises(Unsupported):qualified(p,self.target)
 def test_05_retained_binding_no_reparse_and_mutations(self):
  with patch.object(socket,'socket',side_effect=self.forbidden):self.assertTrue(bind_run(self.pub,self.target,PROOF/'run'))
  for key,value in [('coverage_level','publication_text'),('jurisdiction','Another County'),('state','CA'),('source_url','https://www.clarkcountynv.gov/other'),('inventory_selector','main a[href]')]:
   c=copy.deepcopy(self.cfg);c[key]=value
   with tempfile.TemporaryDirectory()as td:
    (Path(td)/'config.json').write_text(json.dumps(c))
    with self.assertRaises(Unsupported):bind_run(self.pub,self.target,td)
 def cli(self,args,expected=0):
  m=module('clark_registry_cli',ROOT/'collectors/registry/collect.py');calls=[]
  def child(argv,**kw):calls.append((argv,kw));return subprocess.CompletedProcess(argv,0)
  out,err=io.StringIO(),io.StringIO()
  with patch.object(sys,'argv',['registry',*args]),patch.object(m.subprocess,'run',side_effect=child),patch.object(socket,'socket',side_effect=self.forbidden),redirect_stdout(out),redirect_stderr(err):
   try:m.main();code=0
   except SystemExit as e:code=e.code
  return code,calls,out.getvalue(),err.getvalue()
 def test_06_collect_dispatch_only_no_transport(self):
  with tempfile.TemporaryDirectory()as td:
   code,calls,_,_=self.cli(['collect','--target','96','--publication',ID,'--out',str(Path(td)/'NEW')]);self.assertEqual(code,0);self.assertEqual(len(calls),1);self.assertEqual(calls[0][0][1:4],['collectors/official/collect.py','--config',CONFIG]);self.assertEqual(calls[0][1]['cwd'],ROOT);self.assertFalse((Path(td)/'NEW').exists())
 def test_07_verify_dispatch_only_no_native_verifier(self):
  code,calls,_,_=self.cli(['verify','--target','96','--publication',ID,'--out',str(PROOF/'run')]);self.assertEqual(code,0);self.assertEqual(len(calls),1);self.assertEqual(calls[0][0],[sys.executable,'collectors/official/verify.py',str((PROOF/'run').resolve())])
 def test_08_wrong_target_and_nonempty_output_refuse_before_dispatch(self):
  code,calls,_,_=self.cli(['collect','--target','95','--publication',ID,'--out','/tmp/clark-should-not-exist']);self.assertEqual(code,2);self.assertEqual(calls,[])
  with tempfile.TemporaryDirectory()as td:
   (Path(td)/'kept').write_text('retained');code,calls,_,_=self.cli(['collect','--target','96','--publication',ID,'--out',td]);self.assertEqual(code,2);self.assertEqual(calls,[]);self.assertEqual((Path(td)/'kept').read_text(),'retained')
 def test_09_partial_and_resume_flags_remain_explicit(self):
  p=command(self.pub,self.target,'/fresh/clark',sys.executable,resume=True,max_items=1);self.assertEqual(p['argv'][-3:],['--resume','--max-items','1']);self.assertNotIn('--max-items',command(self.pub,self.target,'/fresh/clark',sys.executable)['argv'])
 def test_10_common_acceptance_preserves_semantic_gap(self):
  m=module('clark_ops',ROOT/'collectors/ops/launcher.py');before=digest(PROOF/'run/coverage.json')
  with patch.object(socket,'socket',side_effect=self.forbidden):a=m.publication_acceptance(self.pub,PROOF/'run')
  self.assertTrue(a['native_capture_verified']);self.assertTrue(a['required_nonimage_documents_complete']);self.assertFalse(a['publication_text_complete']);self.assertFalse(a['legal_structure_qualified']);self.assertFalse(a['publication_coverage_accepted']);self.assertFalse(a['jurisdiction_complete']);self.assertEqual(digest(PROOF/'run/coverage.json'),before)
 def test_11_exact_family_source_bridge_no_fresh_common_claim(self):
  cp=read(PROOF/'run/checkpoint.json');self.assertEqual(len(cp['scripts']),16)
  for name,sha in cp['scripts'].items():self.assertEqual(digest(ROOT/'collectors/official'/name),sha,name);self.assertEqual(digest(PROOF/'run/executed'/name),sha,name)
  v=read(PROOF/'verify.stdout');self.assertTrue(v['all_run_files_unchanged']);self.assertEqual(v['forbidden_calls'],[]);self.assertFalse(v['coverage']['legal_semantic_coverage_complete']);self.assertEqual(v['coverage']['image_placeholder_count'],229)
 def test_12_no_borrowed_publisher_identity_and_primary_unchanged(self):
  self.assertEqual(self.pub['expected_identity']['client_names'],['Clark County']);self.assertEqual(self.pub['expected_identity']['state'],'NV');self.assertNotIn('publisher_product_id',self.pub['expected_identity']);self.assertEqual(self.target['primary_publication']['publisher'],'municode');self.assertNotEqual(self.target['primary_publication']['id'],ID);self.assertTrue(self.target['primary_publication']['observed_access_advisories']);self.assertFalse(self.pub['observed_access_advisories']);self.assertFalse(self.pub['image_policy']['download_images']);self.assertEqual(self.pub['image_policy']['placeholder'],'[IMAGE]')
if __name__=='__main__':unittest.main(verbosity=2)
