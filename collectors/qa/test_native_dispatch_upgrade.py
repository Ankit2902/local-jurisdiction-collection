"""Actual newly qualified native dispatch and explicit owned-job revision migration."""
import copy,hashlib,json,sys,tempfile,unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from collectors.qa.test_ops_acceptance import ops
sys.path.insert(0,str(ops.ROOT/'collectors/registry'))
from catalog import load_catalog
from dispatch import command,bind_run,Unsupported
class NativeUpgrade(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);self.catalog=load_catalog();self.pub=next(p for p in self.catalog['publications'] if p['id']=='82-4b983dc51ab6');self.target=next(t for t in self.catalog['targets'] if t['id']=='82');self.cfg=json.loads((ops.ROOT/self.pub['adapter_config_path']).read_text());self.runtime=self.root/'runtime';self.runtime.mkdir();ops.save(self.runtime/'runtime.json',{'packages':[]});self.out=self.root/'out';self.calls=[];self.version='v1'
 def tearDown(self):self.t.cleanup()
 def context(self):
  def child(argv,**kwargs):
   self.calls.append(argv);self.out.mkdir(exist_ok=True);ops.save(self.out/'checkpoint.json',{'config':self.cfg,'native_export':{'status':'failed','reason':'Preserved original timeout'},'generation':0});ops.save(self.out/'coverage.json',{'native_document_complete':True,'source_page_traversal_complete':True,'publication_text_complete':False,'attachments_complete':False,'edition_complete':False});return SimpleNamespace(returncode=0)
  stack=ExitStack()
  for attr,value in [('STATE_ROOT',self.root/'durable'),('runtime_env',lambda *_:(Path('/fake/python'),Path('/fake/node'),{})),('registry_plan',lambda *_:{'publication_id':self.pub['id'],'staged_config':self.cfg}),('catalog_publication',lambda *_:self.pub),('doctor',lambda *a,**kw:{'runtime_ready':True,'ready':True,'issues':[]}),('code_binding',lambda *_:{'native_document.py':self.version}),('access_state',lambda *_:[])]:stack.enter_context(patch.object(ops,attr,value))
  stack.enter_context(patch.object(ops.subprocess,'run',side_effect=child));return stack
 def run_job(self,**kwargs):return ops.execute_job(self.runtime,'82',self.pub['id'],self.out,**kwargs)
 def test_seven_source_qualified_native_configs_dispatch_without_html_target_assumption(self):
  selected=[p for p in self.catalog['publications'] if p.get('adapter_mode')=='native_document'];self.assertEqual(len(selected),7)
  current=[p for p in selected if p['qualification_evidence']['kind']=='literal-current-publisher-anchor-and-pinned-original-native-file'];historical=[p for p in selected if p['qualification_evidence']['kind']=='historical-observed-native-receipt-full172-retained-current-parser'];self.assertEqual(len(current),6);self.assertEqual([p['id'] for p in historical],['82-8fbdce15716d'])
  for pub in selected:
   collect=command(pub,self.target,'/fresh',resume=True,upgrade_code=True);self.assertIn('collectors.encodeplus.native_document',collect['argv']);self.assertIn('--upgrade-code',collect['argv']);self.assertIn('--config',collect['argv']);self.assertIsNone(collect['staged_config'])
   verify=command(pub,self.target,'/fresh',verify=True);self.assertIn('--verify',verify['argv']);self.assertNotIn('collectors.encodeplus.verify',verify['argv'])
   with self.assertRaises(Unsupported):command(pub,self.target,'/fresh',upgrade_code=True)
   with self.assertRaises(Unsupported):command(pub,self.target,'/fresh',max_items=1)
 def test_native_readonly_binding_rejects_wrong_exact_config(self):
  self.out.mkdir();ops.save(self.out/'checkpoint.json',{'config':self.cfg});self.assertTrue(bind_run(self.pub,self.target,self.out));changed=copy.deepcopy(self.cfg);changed['expected_pages']+=1;ops.save(self.out/'checkpoint.json',{'config':changed})
  with self.assertRaises(Unsupported):bind_run(self.pub,self.target,self.out)
 def test_verified_native_capture_never_promotes_and_subsequent_run_is_readonly(self):
  with self.context():
   code,r=self.run_job();self.assertEqual(code,2);self.assertFalse(r['publication_accepted']);self.assertTrue(r['acceptance']['native_capture_verified']);self.assertFalse(ops.read(Path(r['job']))['complete']);self.calls=[]
   code,r=self.run_job();self.assertEqual(code,2);self.assertEqual(len(self.calls),1);self.assertEqual(self.calls[0][3],'verify')
 def test_changed_code_requires_explicit_upgrade_and_preserves_prior_job(self):
  with self.context():
   _,r=self.run_job();metadata=Path(r['job']);prior=metadata.read_bytes();self.version='v2';self.calls=[]
   with self.assertRaisesRegex(ops.OperationError,'automatic resume'):self.run_job()
   self.assertEqual(metadata.read_bytes(),prior);self.assertEqual(self.calls,[])
   code,r=self.run_job(upgrade_code=True);self.assertEqual(code,2);self.assertIn('--resume',self.calls[0]);self.assertIn('--upgrade-code',self.calls[0]);job=ops.read(metadata);self.assertEqual(len(job['code_upgrades']),1);h=hashlib.sha256(prior).hexdigest();self.assertEqual((metadata.parent/'job-history'/(h+'.json')).read_bytes(),prior);self.assertEqual(job['binding']['collector_sources']['native_document.py'],'v2');self.assertFalse(job['complete'])
 def test_unowned_or_changed_publication_cannot_be_adopted_by_upgrade(self):
  with self.context():
   with self.assertRaisesRegex(ops.OperationError,'existing matching launcher'):self.run_job(upgrade_code=True)
   self.assertEqual(self.calls,[]);self.assertFalse(self.out.exists());_,r=self.run_job();self.version='v2';self.cfg=dict(self.cfg,url='https://example.invalid/wrong.pdf');self.calls=[]
   with self.assertRaisesRegex(ops.OperationError,'automatic resume'):self.run_job(upgrade_code=True)
   self.assertEqual(self.calls,[])
 def test_upgrade_not_generic_family_bypass(self):
  self.pub=dict(self.pub,publisher='municode',adapter_mode='html')
  with self.context():
   with self.assertRaisesRegex(ops.OperationError,'only for an existing'):self.run_job(upgrade_code=True)
   self.assertEqual(self.calls,[])
if __name__=='__main__':unittest.main(verbosity=2)
