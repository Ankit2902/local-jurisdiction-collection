"""Fresh-checkout refusal tests; no publisher/browser/image operations."""
import sys
sys.dont_write_bytecode=True
import ast,hashlib,importlib.util,json,os,shutil,subprocess,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
FAMILY=HERE/'candidate/collectors/american-legal'
CENTRAL=HERE/'candidate/collectors/registry/access-advisories.json'
BASELINE=HERE/'baseline/access-advisories.json'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class PortableStopTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.tmp=Path(self.temp.name)
  self.family=self.tmp/'shipped/collectors/american-legal';self.family.mkdir(parents=True)
  for p in FAMILY.iterdir():shutil.copy2(p,self.family/p.name)
  self.gate=self.tmp/'fresh-home/custom-gate'
 def reserve(self,gate=None):
  return subprocess.run([sys.executable,'-B',str(self.family/'gate.py'),'reserve','https://codelibrary.amlegal.com/codes/fixture/latest/overview'],env=dict(os.environ,AMLEGAL_GATE_DIR=str(gate or self.gate),HOME=str(self.tmp/'fresh-home'),PYTHONDONTWRITEBYTECODE='1'),capture_output=True)
 def test_absent_custom_gate_refuses_before_creation(self):
  r=self.reserve();self.assertNotEqual(r.returncode,0);self.assertIn(b'portable workflow access stop',r.stderr);self.assertFalse(self.gate.exists())
 def test_empty_gate_no_state_lock_or_request(self):
  self.gate.mkdir(parents=True);r=self.reserve();self.assertNotEqual(r.returncode,0);self.assertEqual(list(self.gate.iterdir()),[])
 def test_existing_stop_and_state_exactly_preserved(self):
  self.gate.mkdir(parents=True)
  shutil.copy2(HERE/'evidence/browser-stop.json',self.gate/'browser-stop.json')
  (self.gate/'state.json').write_text('{"last_start":1}')
  (self.gate/'requests.jsonl').write_text('historical\n')
  before={p.name:sha(p) for p in self.gate.iterdir()};r=self.reserve();self.assertNotEqual(r.returncode,0)
  self.assertEqual(before,{p.name:sha(p) for p in self.gate.iterdir()})
 def test_missing_bundled_advisory_does_not_release_stop(self):
  (self.family/'access-advisory.json').unlink();r=self.reserve();self.assertNotEqual(r.returncode,0);self.assertIn(b'missing or invalid',r.stderr);self.assertFalse(self.gate.exists())
 def test_malformed_bundled_advisory_does_not_release_stop(self):
  (self.family/'access-advisory.json').write_text('broken');r=self.reserve();self.assertNotEqual(r.returncode,0);self.assertFalse(self.gate.exists())
 def test_changed_witness_and_false_flags_do_not_release_stop(self):
  d=load(self.family/'access-advisory.json');a=d['advisories'][0];a['source_sha256']='0'*64;a['operator_review_required']=False;a['automatic_retry']=True
  (self.family/'access-advisory.json').write_text(json.dumps(d));r=self.reserve();self.assertNotEqual(r.returncode,0);self.assertIn(b'missing or invalid',r.stderr);self.assertFalse(self.gate.exists())
 def test_no_reset_or_bypass_cli(self):
  r=subprocess.run([sys.executable,'-B',str(self.family/'gate.py'),'reserve','https://example.test','--reset'],env=dict(os.environ,AMLEGAL_GATE_DIR=str(self.gate)),capture_output=True)
  self.assertEqual(r.returncode,2);self.assertFalse(self.gate.exists())
 def test_exact_original_stop_and_raw_failure_preserved(self):
  a=load(FAMILY/'access-advisory.json')['advisories'][0]
  self.assertEqual(a['observed_stop'],load(HERE/'evidence/browser-stop.json'))
  self.assertEqual(a['source_sha256'],sha(HERE/'evidence/browser-stop.json'))
  self.assertEqual(a['raw_refusal_witness']['sha256'],sha(HERE/'evidence/failure-response.json'))
  failure=load(HERE/'evidence/failure-response.json');event=json.loads(failure['error'])['access_stop']
  self.assertEqual(event['status'],403);self.assertEqual(event['headers']['cf-mitigated'],'challenge');self.assertEqual(failure['op'],'head')
  self.assertEqual(event['body_snippet_bytes'],0)
 def test_existing_registry_entries_byte_value_unchanged(self):
  old=load(BASELINE);new=load(CENTRAL)
  self.assertEqual(new['schema_version'],old['schema_version']);self.assertEqual(new['status_note'],old['status_note'])
  self.assertEqual(new['advisories'][:-1],old['advisories'])
  self.assertEqual(new['advisories'][-1],load(FAMILY/'access-advisory.json')['advisories'][0])
 def test_no_network_or_image_imports_in_gate(self):
  tree=ast.parse((FAMILY/'gate.py').read_text());names=[]
  for n in ast.walk(tree):
   if isinstance(n,ast.Import):names.extend(x.name for x in n.names)
   elif isinstance(n,ast.ImportFrom):names.append(n.module)
  self.assertFalse(any(n.split('.')[0] in ['socket','requests','urllib','PIL','fitz','pypdfium2','playwright'] for n in names if n))
if __name__=='__main__':unittest.main()
