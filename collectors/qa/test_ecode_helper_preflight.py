import sys
sys.dont_write_bytecode=True
import importlib.util,tempfile,unittest,argparse
from pathlib import Path
from unittest.mock import patch
B=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--input',required=True,type=Path);ap.add_argument('--helper',required=True,type=Path);args,rest=ap.parse_known_args();sys.argv=[sys.argv[0]]+rest
spec=importlib.util.spec_from_file_location('helper',args.helper.resolve());helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
class Preflight(unittest.TestCase):
 def test_installed_unified_runtime_qualifies_dependencies(self):helper.verification_dependencies()
 def missing(self,module,distribution,exception=False):
  root=args.input.resolve();original=importlib.util.find_spec
  def find(name,*a,**k):
   if name==module:
    if exception:raise ModuleNotFoundError(name)
    return None
   return original(name,*a,**k)
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'never-created';argv=['helper','--input',str(root),'--collector-root',str(root/'executed-source'),'--publication-id','albany-acquired','--out',str(out)]
   with patch.object(sys,'argv',argv),patch.object(importlib.util,'find_spec',side_effect=find),patch.object(helper.importlib,'import_module',side_effect=AssertionError('Must not load selected engine')) as engine:
    with self.assertRaisesRegex(ValueError,'Missing read-only source-verification dependencies: '+distribution):helper.main()
    self.assertFalse(out.exists());engine.assert_not_called()
 def test_missing_Pillow_fails_before_output_or_verifier_import(self):self.missing('PIL.Image','Pillow')
 def test_nested_PIL_ModuleNotFound_fails_before_output(self):self.missing('PIL.Image','Pillow',True)
 def test_missing_BS4_fails_before_output(self):self.missing('bs4','beautifulsoup4')
 def test_missing_requests_fails_before_output(self):self.missing('requests','requests')
 def test_missing_pypdf_fails_before_output(self):self.missing('pypdf','pypdf')
if __name__=='__main__':unittest.main()
