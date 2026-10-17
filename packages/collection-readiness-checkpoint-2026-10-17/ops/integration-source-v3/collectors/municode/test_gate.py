"""Network-free gate tests use only isolated temporary gate state."""
import sys,os,json,tempfile,subprocess,unittest
from pathlib import Path
class GateTests(unittest.TestCase):
 def test_external_stop_is_host_bound_and_publisher_stop_is_global(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'state.json').write_text(json.dumps({'family_stop':{'reason':'preserved direct stop'},'browser_workflow_authorized':True}));env={**os.environ,'MUNICODE_GATE_DIR':td}
   def run(*args):return subprocess.run([sys.executable,str(Path(__file__).with_name('gate_cli.py')),*args],env=env,capture_output=True,text=True)
   self.assertEqual(run('stop-external','https://external.example.test/file.pdf','HTTP403').returncode,0);self.assertFalse((root/'browser-stop.json').exists());self.assertNotEqual(run('reserve','https://external.example.test/other.pdf').returncode,0);self.assertEqual(run('reserve','https://library.municode.com/api/test').returncode,0)
   self.assertEqual(run('stop-browser','https://library.municode.com/api/test','HTTP403').returncode,0);self.assertNotEqual(run('reserve','https://library.municode.com/api/test').returncode,0);self.assertEqual(json.loads((root/'state.json').read_text())['family_stop']['reason'],'preserved direct stop')
 def test_429_persists_stop_and_minimum_cooldown(self):
  import time
  with tempfile.TemporaryDirectory() as td:
   env={**os.environ,'MUNICODE_GATE_DIR':td};start=time.time();r=subprocess.run([sys.executable,str(Path(__file__).with_name('gate_cli.py')),'cooldown','1'],env=env,capture_output=True,text=True);self.assertEqual(r.returncode,0);state=json.loads((Path(td)/'state.json').read_text());self.assertGreaterEqual(state['actual_rate_limit_until'],start+300);self.assertTrue((Path(td)/'browser-stop.json').exists())
if __name__=='__main__':unittest.main(verbosity=2)
