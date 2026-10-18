"""Run existing launcher acceptance/dependency tests against isolated candidate functions."""
import importlib.util,sys,unittest
from pathlib import Path
root=Path(__file__).resolve().parent
repo=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/github/local-jurisdiction-collection')
sys.path[:0]=[str(repo/'collectors/qa'),str(repo)]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
ops=load('isolated_required_pdf_ops',root/'launcher-candidate.py');ops.ROOT=repo;ops.HERE=repo/'collectors/ops'
acceptance=load('test_ops_acceptance',repo/'collectors/qa/test_ops_acceptance.py');acceptance.ops=ops
sys.modules['collectors.qa.test_ops_acceptance']=acceptance
loader=unittest.TestLoader();suite=unittest.TestSuite([loader.loadTestsFromModule(acceptance)])
for name in ('test_ops_dependencies','test_native_dispatch_upgrade'):
 suite.addTests(loader.loadTestsFromModule(load(name,repo/'collectors/qa'/(name+'.py'))))
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
