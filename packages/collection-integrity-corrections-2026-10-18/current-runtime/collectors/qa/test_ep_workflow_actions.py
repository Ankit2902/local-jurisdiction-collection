"""Explicit supported enCodePlus actions through the real shared job state machine."""
import json,tempfile,unittest
from pathlib import Path
from collectors.qa import test_native_dispatch_upgrade as native_case
ops=native_case.ops;command=native_case.command;Unsupported=native_case.Unsupported
class EPWorkflowActions(unittest.TestCase):
 def setUp(self):
  self.f=native_case.NativeUpgrade();self.f.setUp();self.f.pub=ops.catalog_publication('67-primary');self.f.cfg={'base':'https://online.encodeplus.com/regs/lincoln-ne/','identity':'Lincoln NE Municipal Code','jurisdiction':'Lincoln NE','scope':'Municipal code'}
 def tearDown(self):self.f.tearDown()
 def test_exact_html_dispatch_requires_explicit_resume_retry_and_same_options(self):
  pub=self.f.pub;target=next(t for t in self.f.catalog['targets'] if t['id']=='67');p=command(pub,target,'/fresh',resume=True,upgrade_code=True,native_export=True,retry_native_export=True);self.assertTrue(all(x in p['argv'] for x in ['--resume','--upgrade-code','--native-export','--retry-native-export']))
  for kwargs in [{'retry_native_export':True},{'resume':True,'retry_native_export':True},{'native_export':True,'verify':True}]:
   with self.assertRaises(Unsupported):command(pub,target,'/fresh',**kwargs)
  wrong=ops.catalog_publication('60-primary')
  with self.assertRaises(Unsupported):command(wrong,target,'/fresh',native_export=True)
 def test_finished_bound_native_options_reused_without_retry_but_explicit_retry_collects(self):
  with self.f.context():
   _,first=self.f.run_job(native_export=True);job=ops.read(Path(first['job']));self.assertTrue(job['binding']['collection_options']['native_export']);self.assertIn('--native-export',self.f.calls[0]);self.f.calls=[]
   self.f.run_job();self.assertEqual(len(self.f.calls),1);self.assertEqual(self.f.calls[0][3],'verify');self.f.calls=[]
   _,result=self.f.run_job(native_export=True,retry_native_export=True);self.assertEqual(self.f.calls[0][3],'collect');self.assertIn('--resume',self.f.calls[0]);self.assertIn('--retry-native-export',self.f.calls[0]);attempt=ops.read(Path(result['job']))['attempts'][-1];self.assertEqual(attempt['prior_native_export']['status'],'failed');self.assertTrue(attempt['requested_actions']['retry_native_export']);self.assertEqual(len(attempt['prior_family_checkpoint_sha256']),64)
 def test_retry_does_not_change_original_request_options_or_adopt_unowned_output(self):
  with self.f.context():
   with self.assertRaisesRegex(ops.OperationError,'existing matching launcher'):self.f.run_job(native_export=True,retry_native_export=True)
   self.f.run_job();self.f.calls=[]
   with self.assertRaisesRegex(ops.OperationError,'originally created'):self.f.run_job(native_export=True,retry_native_export=True)
   self.assertEqual(self.f.calls,[])
 def test_html_revision_upgrade_preserves_bound_options_and_requires_explicit_action(self):
  with self.f.context():
   self.f.run_job(native_export=True);self.f.version='v2';self.f.calls=[]
   with self.assertRaisesRegex(ops.OperationError,'automatic resume'):self.f.run_job()
   _,r=self.f.run_job(upgrade_code=True);self.assertIn('--upgrade-code',self.f.calls[0]);self.assertIn('--native-export',self.f.calls[0]);self.assertNotIn('--retry-native-export',self.f.calls[0]);j=ops.read(Path(r['job']));self.assertEqual(len(j['code_upgrades']),1);self.assertTrue(j['binding']['collection_options']['native_export'])
 def test_known_stop_blocks_explicit_retry_before_any_child_request(self):
  from unittest.mock import patch
  with self.f.context():
   self.f.run_job(native_export=True);self.f.calls=[]
   with patch.object(ops,'doctor',return_value={'runtime_ready':True,'ready':False,'issues':['Existing access stop'],'access_stops':[{'reason':'403'}]}):
    code,r=self.f.run_job(native_export=True,retry_native_export=True)
   self.assertEqual(code,3);self.assertEqual(r['status'],'blocked_preflight');self.assertEqual(self.f.calls,[])
if __name__=='__main__':unittest.main(verbosity=2)
