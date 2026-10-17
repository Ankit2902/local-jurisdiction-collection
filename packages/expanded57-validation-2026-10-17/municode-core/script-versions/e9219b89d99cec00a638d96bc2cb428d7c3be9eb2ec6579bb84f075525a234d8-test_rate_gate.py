"""Network-free tests of shared 429 cooldown and pre-request refusal; not live source validation."""
import io,json,os,subprocess,sys,tempfile,time,unittest,urllib.error
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
from municode_shared import fetch,Cooldown
ROOT=Path(__file__).resolve().parent
class GateTests(unittest.TestCase):
 def test_429_retry_after_persisted_and_no_second_request(self):
  with tempfile.TemporaryDirectory() as t:
   gate=Path(t)/'gate';calls=[]
   class Opener:
    def open(self,req,timeout=0):
     calls.append(req.full_url);raise urllib.error.HTTPError(req.full_url,429,'Too Many Requests',{'retry-after':'1000'},io.BytesIO(b'rate limited'))
   with patch.dict(os.environ,{'MUNICODE_GATE_DIR':str(gate)}),patch('urllib.request.build_opener',return_value=Opener()):
    start=time.time()
    with self.assertRaises(RuntimeError):fetch('https://library.municode.com/api/test-no-network',Path(t)/'response.bin')
    state=json.loads((gate/'state.json').read_text());self.assertGreaterEqual(state['cooldown_until'],start+1000)
    with self.assertRaises(Cooldown):fetch('https://library.municode.com/api/test-no-network-2',Path(t)/'response2.bin')
    self.assertEqual(len(calls),1);self.assertFalse((Path(t)/'response2.bin').exists());self.assertEqual(json.loads((Path(t)/'response.bin.receipt.json').read_text())['http_status'],429)
 def test_browser_cli_refuses_existing_cooldown(self):
  with tempfile.TemporaryDirectory() as t:
   Path(t,'state.json').write_text(json.dumps({'cooldown_until':time.time()+300}))
   r=subprocess.run([sys.executable,str(ROOT/'gate_cli.py'),'reserve','https://library.municode.com/no-network'],env={**os.environ,'MUNICODE_GATE_DIR':t},capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0);self.assertIn('cooldown',r.stderr.lower());self.assertFalse(Path(t,'requests.jsonl').exists())
if __name__=='__main__':unittest.main(verbosity=2)
