"""Network-free serial runner source binding, interruption and truthful status tests."""
import sys
sys.dont_write_bytecode=True
import json,tempfile,unittest,types,os
from pathlib import Path
from unittest.mock import patch
import batch
class BatchTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.registry=self.root/'registry.json';self.out=self.root/'batch';self.gate=self.root/'gate';self.gate.mkdir();self.registry.write_text(json.dumps({'publications':[{'id':'a-primary','target_id':'a','publisher':'municode','runnable':True,'role':'primary','source_url':'https://library.municode.com/zz/a/codes/code','expected_identity':{'client_names':['A'],'state':'ZZ','publisher_client_id':1},'publisher_product_id':2}]}))
 def tearDown(self):self.tmp.cleanup()
 def invoke(self,*args,runner=None):
  argv=['batch.py','--registry',str(self.registry),'--out',str(self.out),*args]
  with patch.object(sys,'argv',argv),patch.object(batch,'check',return_value={'passed':True}),patch.object(batch.subprocess,'run',side_effect=runner or self.success),patch.dict(os.environ,{'MUNICODE_GATE_DIR':str(self.gate)}):return batch.main()
 def success(self,cmd,**kwargs):
  if 'collect.py' in str(cmd[2]):
   out=Path(cmd[cmd.index('--out')+1]);out.mkdir(parents=True,exist_ok=True);(out/'coverage.json').write_text(json.dumps({'publication_complete':True}))
  return types.SimpleNamespace(returncode=0,stdout='{}',stderr='')
 def test_serial_complete_and_resume_skip(self):
  self.assertEqual(self.invoke(),0);status=json.loads((self.out/'status.json').read_text());self.assertTrue(status['jobs']['a-primary']['full_publication_live_verified']);self.assertEqual(self.invoke('--resume',runner=lambda *a,**k:self.fail('Complete job rerun')),0)
 def test_source_binding_mismatch_refused(self):
  self.invoke();data=json.loads(self.registry.read_text());data['publications'][0]['publisher_product_id']=3;self.registry.write_text(json.dumps(data))
  with self.assertRaisesRegex(ValueError,'mismatch'):self.invoke('--resume')
 def test_access_stop_dispatches_nothing(self):
  (self.gate/'browser-stop.json').write_text('{}');self.assertEqual(self.invoke(runner=lambda *a,**k:self.fail('Request after access stop')),2);self.assertEqual(json.loads((self.out/'status.json').read_text())['phase'],'access_stopped')
 def test_running_interruption_resumes(self):
  with self.assertRaises(KeyboardInterrupt):self.invoke(runner=lambda *a,**k:(_ for _ in ()).throw(KeyboardInterrupt()))
  self.assertEqual(json.loads((self.out/'status.json').read_text())['jobs']['a-primary']['status'],'running');self.assertEqual(self.invoke('--resume'),0)
 def test_success_exit_without_complete_coverage_cannot_pass(self):
  def incomplete(cmd,**kw):
   r=self.success(cmd,**kw)
   if 'collect.py' in str(cmd[2]):(self.out/'runs/a-primary/coverage.json').write_text('{"publication_complete":false}')
   return r
  self.assertEqual(self.invoke(runner=incomplete),2);self.assertFalse(json.loads((self.out/'status.json').read_text())['jobs']['a-primary']['full_publication_live_verified'])
if __name__=='__main__':unittest.main(verbosity=2)
