import sys
sys.dont_write_bytecode=True
import pathlib,json,subprocess,unittest,hashlib
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H/'candidate'))
from collectors.encodeplus import retained_native as n
LEGACY=H/'legacy-compatibility/actual-retained-full172'
def equivalent(d):
 s=json.loads((d/'checkpoint.json').read_text());cfg=json.loads((d/'config.json').read_text());rs=[json.loads(l)for l in(d/'records.jsonl').read_text().split('\n')if l];receipt=json.loads((d/'raw/source.pdf.receipt.json').read_text());headers=n.validate_source((d/'raw/source.pdf').read_bytes(),receipt,cfg);assert n.summarize(rs,s['details'],cfg,headers)==json.loads((d/'coverage.json').read_text())
class Compatibility(unittest.TestCase):
 def test_legacy_current_published172_exactreport(self):equivalent(LEGACY)
 def test_legacy_published_captured_verifier(self):
  cmd=[sys.executable,'-B',str(LEGACY/'collector-source/collectors/encodeplus/retained_native.py'),'--verify',str(LEGACY)];p=subprocess.run(cmd,capture_output=True);self.assertEqual(p.returncode,0,p.stderr.decode());self.assertTrue(json.loads(p.stdout)['artifact_replay_verified'])
 def test_all_six_newreport_equivalence(self):
  for d in sorted((H/'full-native').iterdir()):
   if d.is_dir():
    with self.subTest(id=d.name):equivalent(d)
if __name__=='__main__':unittest.main()
