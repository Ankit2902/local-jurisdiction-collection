"""Network-free preflight compatibility regressions; acceptance is not a live browser proof."""
import sys
sys.dont_write_bytecode=True
import unittest
from unittest.mock import patch
import runtime

class RuntimeTests(unittest.TestCase):
 def setUp(self):self.advisory=patch.object(runtime,'advisory_state',return_value={'blocked':False});self.advisory.start()
 def tearDown(self):self.advisory.stop()
 def probe(self,node,playwright):
  with patch.object(runtime.subprocess,'check_output',side_effect=[node+'\n',playwright+'\n']) as calls:
   result=runtime.check();self.assertEqual(result['network_requests'],0);return result,calls.call_count
 def test_supported_npm_version(self):
  result,calls=self.probe('v24.19.0','1.62.1');self.assertTrue(result['passed']);self.assertEqual(calls,2)
 def test_supported_official_python_core_version(self):
  result,calls=self.probe('v24.21.0','1.64.0');self.assertTrue(result['passed']);self.assertEqual(calls,2)
 def test_unqualified_version_refused(self):
  result,calls=self.probe('v24.21.0','1.65.0');self.assertFalse(result['passed']);self.assertEqual(calls,2)
 def test_exact_bundled_official_core_build(self):
  result,calls=self.probe('v24.21.0','1.64.0-beta-1791568591000');self.assertTrue(result['passed']);self.assertEqual(calls,2)
 def test_other_beta_build_refused(self):
  result,calls=self.probe('v24.21.0','1.64.0-beta-other');self.assertFalse(result['passed']);self.assertEqual(calls,2)
 def test_ancient_system_node_refused_before_module_load(self):
  result,calls=self.probe('v8.17.0','1.64.0');self.assertFalse(result['passed']);self.assertEqual(calls,1)
 def test_missing_runtime_refused(self):
  with patch.object(runtime.subprocess,'check_output',side_effect=FileNotFoundError('node missing')):
   self.assertFalse(runtime.check()['passed'])

if __name__=='__main__':unittest.main(verbosity=2)
