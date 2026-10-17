"""No-network tripwires for documented direct entrypoints and missing/altered stop state."""
import sys
sys.dont_write_bytecode=True
import json,os,runpy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import collect,batch,runtime
from access_state import advisory_state,HERE
class AccessTests(unittest.TestCase):
 def test_missing_and_mismatched_advisories_do_not_release_stop(self):
  with tempfile.TemporaryDirectory() as tmp:
   missing=Path(tmp)/'missing.json';self.assertTrue(advisory_state(missing,missing)['blocked']);bad=Path(tmp)/'bad.json';bad.write_text('{"schema_version":1,"advisories":[]}');r=advisory_state(bad,missing);self.assertTrue(r['blocked']);self.assertTrue(r['advisory_errors'])
 def test_relocated_family_fallback_is_portable(self):
  with tempfile.TemporaryDirectory() as tmp:
   local=Path(tmp)/'access-advisory.json';local.write_bytes((HERE/'access-advisory.json').read_bytes());r=advisory_state(local,Path(tmp)/'no-registry.json');self.assertTrue(r['blocked']);self.assertEqual(len(r['advisories']),1);self.assertFalse(r['advisory_errors'])
 def test_direct_entrypoints_stop_before_browser_or_subprocess(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);gate=root/'fresh-gate';gate.mkdir();tripwire=lambda *a,**k:self.fail('Transport/subprocess must not run after known access stop')
   with patch.dict(os.environ,{'MUNICODE_GATE_DIR':str(gate)}),patch.object(collect,'Browser',side_effect=tripwire),patch.object(runtime.subprocess,'check_output',side_effect=tripwire),patch.object(batch.subprocess,'run',side_effect=tripwire):
    with patch.object(sys,'argv',['collect.py','--url','https://library.municode.com/zz/fixture/codes/test','--state','ZZ','--client-name','Fixture','--out',str(root/'collect')]):self.assertEqual(collect.main(),2)
    with patch.object(sys,'argv',['batch.py','--registry',str(root/'missing-registry.json'),'--out',str(root/'batch')]):
     with self.assertRaisesRegex(ValueError,'Publisher access stopped'):batch.main()
    with patch.object(sys,'argv',['export.py','--reference-run',str(root/'missing-reference'),'--product-id','17','--out',str(root/'export')]):
     with self.assertRaisesRegex(SystemExit,'Publisher access stopped'):runpy.run_path(str(HERE/'export.py'),run_name='__main__')
   self.assertEqual(list(gate.iterdir()),[]);self.assertFalse((root/'collect').exists());self.assertFalse((root/'batch').exists());self.assertFalse((root/'export').exists())
 def test_offline_dependency_check_not_blocked_by_access_advisory(self):self.assertTrue(runtime.check(live=False)['passed'])
if __name__=='__main__':unittest.main(verbosity=2)
