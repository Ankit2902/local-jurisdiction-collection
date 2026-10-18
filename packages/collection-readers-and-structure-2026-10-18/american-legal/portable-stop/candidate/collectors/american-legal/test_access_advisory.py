"""Portable known-stop refusal: no acquisition, images, gate reset or state writes."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,os,shutil,subprocess,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
class AccessAdvisoryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.shipped=self.root/'standalone';self.shipped.mkdir()
  for name in ['gate.py','access-advisory.json']:shutil.copy2(HERE/name,self.shipped/name)
  self.state=self.root/'custom-gate'
 def reserve(self):
  return subprocess.run([sys.executable,'-B',str(self.shipped/'gate.py'),'reserve','https://codelibrary.amlegal.com/codes/fixture/latest/overview'],env=dict(os.environ,AMLEGAL_GATE_DIR=str(self.state),HOME=str(self.root/'fresh-home'),PYTHONDONTWRITEBYTECODE='1'),capture_output=True)
 def test_fresh_custom_gate_refuses_before_mkdir(self):
  r=self.reserve();self.assertNotEqual(r.returncode,0);self.assertIn(b'portable workflow access stop',r.stderr);self.assertFalse(self.state.exists())
 def test_empty_custom_gate_stays_empty(self):
  self.state.mkdir();r=self.reserve();self.assertNotEqual(r.returncode,0);self.assertEqual(list(self.state.iterdir()),[])
 def test_existing_stop_state_request_bytes_preserved(self):
  self.state.mkdir();a=json.loads((HERE/'access-advisory.json').read_text())['advisories'][0]
  (self.state/'browser-stop.json').write_text(json.dumps(a['observed_stop']))
  (self.state/'state.json').write_text('{"last_start":1}')
  (self.state/'requests.jsonl').write_text('original request ledger\n')
  before={p.name:p.read_bytes() for p in self.state.iterdir()};r=self.reserve();self.assertNotEqual(r.returncode,0)
  self.assertEqual(before,{p.name:p.read_bytes() for p in self.state.iterdir()})
 def test_missing_advisory_still_refuses(self):
  (self.shipped/'access-advisory.json').unlink();r=self.reserve();self.assertNotEqual(r.returncode,0);self.assertIn(b'missing or invalid',r.stderr);self.assertFalse(self.state.exists())
 def test_altered_advisory_never_releases_known_stop(self):
  data=json.loads((self.shipped/'access-advisory.json').read_text());data['advisories'][0].update(operator_review_required=False,automatic_retry=True)
  (self.shipped/'access-advisory.json').write_text(json.dumps(data));r=self.reserve();self.assertNotEqual(r.returncode,0);self.assertFalse(self.state.exists())
 def test_no_reset_cli(self):
  r=subprocess.run([sys.executable,'-B',str(self.shipped/'gate.py'),'reserve','https://example.test','--reset'],env=dict(os.environ,AMLEGAL_GATE_DIR=str(self.state)),capture_output=True)
  self.assertEqual(r.returncode,2);self.assertFalse(self.state.exists())
if __name__=='__main__':unittest.main()
