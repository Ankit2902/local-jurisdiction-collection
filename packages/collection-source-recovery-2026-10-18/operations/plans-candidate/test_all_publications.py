"""Actual isolated CLI planning; network/native/API and execution tripwires enabled."""
import sys
sys.dont_write_bytecode=True
import hashlib,importlib.util,json,os,subprocess,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE/'candidate'
spec=importlib.util.spec_from_file_location('snapshot_catalog',ROOT/'collectors/registry/catalog.py');CAT=importlib.util.module_from_spec(spec);spec.loader.exec_module(CAT)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
GUARD='''import sys,os,json,socket,builtins,subprocess
from pathlib import Path
log=Path(os.environ['PLAN_GUARD_LOG'])
def deny(name):
 with log.open('a') as f:f.write(json.dumps({'forbidden':name,'argv':sys.argv})+'\\n')
 raise AssertionError('Forbidden planning operation '+name)
socket.socket.connect=lambda *a,**k:deny('socket.connect')
socket.create_connection=lambda *a,**k:deny('socket.create_connection')
original=builtins.__import__
def checked_import(name,*a,**k):
 if name.split('.')[0] in ('PIL','playwright','pdfplumber','pypdfium2','fitz','pypdf','mcp','codex'):return deny('native_or_app_import:'+name)
 return original(name,*a,**k)
builtins.__import__=checked_import
popen=subprocess.Popen.__init__
def checked_popen(self,args,*a,**k):
 parts=[str(x) for x in args]
 indexes=[i for i,x in enumerate(parts) if x.endswith('/collectors/registry/collect.py')]
 if not(len(indexes)==1 and parts[indexes[0]+1:indexes[0]+2]==['plan']):return deny('unexpected_child:'+str(parts))
 return popen(self,args,*a,**k)
subprocess.Popen.__init__=checked_popen
'''
class AllPublicationPlanTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=CAT.load_catalog();cls.target={t['id']:t for t in cls.catalog['targets']};cls.pub={p['id']:p for p in cls.catalog['publications']}
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.work=Path(self.tmp.name);self.guard=self.work/'guard';self.guard.mkdir();(self.guard/'sitecustomize.py').write_text(GUARD);self.log=self.work/'guard-events.jsonl'
  self.before={p.relative_to(ROOT).as_posix():sha(p) for p in ROOT.rglob('*') if p.is_file()}
 def tearDown(self):
  self.assertFalse(self.log.exists(),self.log.read_text() if self.log.exists() else '')
  self.assertEqual(self.before,{p.relative_to(ROOT).as_posix():sha(p) for p in ROOT.rglob('*') if p.is_file()})
  self.assertFalse((ROOT/'.collection-runtime').exists());self.assertFalse(list(ROOT.rglob('*.pyc')))
 def run_cli(self,args,direct=False):
  command=[sys.executable,'-B',str(ROOT/('collectors/registry/collect.py' if direct else 'collect.py'))]+args
  return subprocess.run(command,cwd=self.work,env=dict(os.environ,PYTHONPATH=str(self.guard),PYTHONDONTWRITEBYTECODE='1',PLAN_GUARD_LOG=str(self.log),HOME=str(self.work/'fresh-home')),capture_output=True)
 def result(self,args,direct=False):
  r=self.run_cli(args,direct);self.assertEqual(r.returncode,0,r.stderr.decode());return json.loads(r.stdout)
 def test_legacy_all_primary_behavior_preserved(self):
  d=self.result(['plan','--all']);self.assertEqual(d['targets'],130);self.assertEqual(len(d['plans']),130)
  self.assertEqual({p['publication_id'] for p in d['plans']},{t['primary_publication_id'] for t in self.target.values()});self.assertNotIn('publication_count',d)
 def test_all_known_publications_discoverable(self):
  d=self.result(['plan','--all-publications']);self.assertEqual(d['targets'],130);self.assertEqual(d['publication_count'],225);self.assertEqual(d['runnable_config_count'],195)
  self.assertEqual({p['publication_id'] for p in d['plans']},set(self.pub));self.assertEqual(len(d['plans']),len({p['publication_id'] for p in d['plans']}));self.assertEqual(sum(bool(p['observed_access_advisories']) for p in d['plans']),154)
  for p in d['plans']:
   source=self.pub[p['publication_id']];self.assertEqual(p['publication_role'],source['role']);self.assertEqual(p['source_url'],source['source_url']);self.assertEqual(p['publication_title'],source['title']);self.assertEqual(p['target_id'],source['target_id']);self.assertIs(p['jurisdiction_complete'],False)
 def test_unknown_publication_configs_retained_with_actual_reasons(self):
  d=self.result(['plan','--all-publications']);unknown=[p for p in d['plans'] if not p['runnable']];self.assertEqual(len(unknown),30)
  for p in unknown:self.assertTrue(p['unsupported_reason']);self.assertTrue(p['publication_title']);self.assertTrue(p['source_url']);self.assertNotIn('argv',p)
 def test_direct_registry_same_plan_scope(self):
  a=self.result(['plan','--all-publications']);b=self.result(['plan','--all-publications'],True);self.assertEqual(a,b)
 def test_target_filter_includes_its_own_secondary_publications(self):
  d=self.result(['plan','--target','82','--all-publications']);ids={p['id'] for p in self.pub.values() if p['target_id']=='82'}
  self.assertEqual({p['publication_id'] for p in d['plans']},ids);self.assertEqual(d['publication_count'],len(ids));self.assertEqual(d['targets'],1)
 def test_cohort_filters_retain_full_matching_inventory(self):
  for cohort in ['original','expansion']:
   d=self.result(['plan','--all-publications','--cohort',cohort]);actual=CAT.load_catalog(cohort)
   self.assertEqual({p['publication_id'] for p in d['plans']},{p['id'] for p in actual['publications']});self.assertEqual(d['targets'],len(actual['targets']))
 def test_collect_verify_status_cannot_use_enumeration_flag(self):
  for action in ['collect','verify','status']:
   out=self.work/(action+'-not-created');r=self.run_cli([action,'--all-publications','--target','82','--out',str(out)],True)
   self.assertEqual(r.returncode,2);self.assertIn(b'only for plan',r.stderr);self.assertFalse(out.exists())
  for action in ['run','verify']:
   out=self.work/(action+'-root-not-created');r=self.run_cli([action,'--all-publications','--target','82','--out',str(out)])
   self.assertEqual(r.returncode,2);self.assertFalse(out.exists())
 def test_ambiguous_selectors_refuse_without_execution(self):
  for selector in [['--all'],['--publication','82-primary']]:
   r=self.run_cli(['plan','--all-publications']+selector);self.assertEqual(r.returncode,2);self.assertIn(b'selectors cannot be combined',r.stderr)
if __name__=='__main__':unittest.main()
