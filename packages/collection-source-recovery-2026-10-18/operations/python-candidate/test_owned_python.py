"""Controlled installer/doctor version faults; no pip, browser or network execution."""
import sys
sys.dont_write_bytecode=True
import contextlib,importlib.util,io,json,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent

def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
C=module(HERE/'candidate/collectors/ops/launcher.py','candidate_launcher')
B=module(HERE/'baseline/launcher.py','baseline_launcher')
B.HERE=C.HERE
class OwnedPythonTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.runtime=Path(self.temp.name)/'owned'
  self.py=self.runtime/'venv/bin/python';self.py.parent.mkdir(parents=True);self.py.write_text('existing owned interpreter sentinel\n')
  self.node=self.runtime/'driver/node';self.node.parent.mkdir();self.node.write_text('controlled driver sentinel\n')
  package=self.node.parent/'package/package.json';package.parent.mkdir();package.write_text('{"version":"1.64.0"}')
  self.bootstrap=[3,12,1];self.actual=[3,12,14];self.commands=[];self.installs=[]
  self.packages=[{'name':line.split('==')[0],'version':line.split('==')[1]} for line in (C.HERE/'requirements.txt').read_text().splitlines() if line and not line.startswith('#')]
  self.receipt={'owner':C.MARKER,'setup_complete':True,'python_version':self.actual.copy(),'requirements_sha256':C.sha(C.HERE/'requirements.txt'),'packages':self.packages,'browser_driver_sha256':{'driver':'controlled'},'shim_sha256':{'shim':'controlled'}}
  C.save(self.runtime/'runtime.json',self.receipt)
 def captured(self,argv,**kw):
  argv=[str(x) for x in argv];self.commands.append(argv)
  if len(argv)>2 and argv[1]=='-c' and 'version_info' in argv[2]:return json.dumps(self.bootstrap if argv[0]=='bootstrap-python' else self.actual)
  if argv[1:]==['-m','pip','check']:return 'No broken requirements found.\n'
  if argv[1:]==['-m','pip','list','--format=json']:return json.dumps(self.packages)
  if argv[0]==str(self.node) and argv[1]=='--version':return 'v24.19.0\n'
  if argv[0]==str(self.node) and argv[1].endswith('browser_check.cjs'):return '{"passed":true,"headed":true,"publisher_requests":0}'
  raise AssertionError('Unexpected subprocess '+str(argv))
 def install(self,argv,**kw):self.installs.append([str(x) for x in argv]);return subprocess.CompletedProcess(argv,0)
 @contextlib.contextmanager
 def controls(self,m):
  with contextlib.ExitStack() as st:
   st.enter_context(patch.object(m,'captured',side_effect=self.captured))
   st.enter_context(patch.object(m,'runtime_env',return_value=(self.py,self.node,{})))
   st.enter_context(patch.object(m,'driver_hashes',return_value={'driver':'controlled'}))
   st.enter_context(patch.object(m,'shim_hashes',return_value={'shim':'controlled'}))
   st.enter_context(patch.object(m.subprocess,'run',side_effect=self.install))
   st.enter_context(contextlib.redirect_stdout(io.StringIO()))
   yield
 def test_baseline_setup_reproduces_bootstrap_mislabel(self):
  self.actual=[3,11,9]
  with self.controls(B):r=B.setup(self.runtime,'bootstrap-python')
  self.assertEqual(r['python_version'],[3,12,1]);self.assertTrue(r['setup_complete']);self.assertTrue(self.installs)
 def test_setup_rejects_actual_owned_wrong_major_minor_before_pip(self):
  self.actual=[3,11,9];before=self.py.read_bytes()
  with self.controls(C),self.assertRaisesRegex(C.OperationError,'Owned runtime Python is not 3.12'):C.setup(self.runtime,'bootstrap-python')
  self.assertEqual(self.installs,[]);self.assertEqual(self.py.read_bytes(),before)
  self.assertFalse(C.read(self.runtime/'runtime.json')['setup_complete'])
 def test_setup_records_owned_not_bootstrap_patch_version(self):
  with self.controls(C):r=C.setup(self.runtime,'bootstrap-python')
  self.assertEqual(r['python_version'],[3,12,14]);self.assertEqual(r['setup_python_version'],[3,12,1]);self.assertTrue(r['setup_complete'])
 def test_baseline_doctor_reproduces_unchecked_wrong_owned_version(self):
  self.actual=[3,11,9]
  with self.controls(B):r=B.doctor(self.runtime)
  self.assertTrue(r['runtime_ready']);self.assertTrue(r['ready']);self.assertFalse(any('version_info' in str(a) for a in self.commands))
 def test_doctor_rejects_wrong_owned_version(self):
  self.actual=[3,11,9]
  with self.controls(C):r=C.doctor(self.runtime)
  self.assertFalse(r['runtime_ready']);self.assertFalse(r['ready']);self.assertTrue(any('not 3.12' in s for s in r['issues']))
 def test_current_valid_receipt_without_new_optional_bootstrap_field_works(self):
  self.assertNotIn('setup_python_version',self.receipt)
  with self.controls(C):r=C.doctor(self.runtime)
  self.assertTrue(r['runtime_ready']);self.assertTrue(r['ready'])
 def test_doctor_rejects_owned_patch_version_drift_from_receipt(self):
  self.actual=[3,12,15]
  with self.controls(C):r=C.doctor(self.runtime)
  self.assertFalse(r['runtime_ready']);self.assertTrue(any('differs from the setup receipt' in s for s in r['issues']))
 def test_invalid_interpreter_version_shape_refuses(self):
  for value in [None,{},[3,12],[3,True,1],[3,12,'14']]:
   with self.subTest(value=value),patch.object(C,'captured',return_value=json.dumps(value)),self.assertRaisesRegex(C.OperationError,'valid version triplet'):C.interpreter_version(self.py)
if __name__=='__main__':unittest.main()
