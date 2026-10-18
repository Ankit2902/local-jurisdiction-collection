import pathlib,sys,json,unittest,socket,subprocess,contextlib
from unittest.mock import patch
import pypdf,pdfplumber,pypdfium2
from PIL import Image
P=pathlib.Path(sys.argv[1]).resolve();sys.path.insert(0,str(P/'candidate'))
from collectors.encodeplus import test_infrastructure_logical as tests
calls=[]
def deny(name):
 def f(*a,**k):calls.append(name);raise AssertionError('Review forbiddenAPI:'+name)
 return f
with contextlib.ExitStack()as stack:
 for obj,names in [(pypdf.PdfReader,['__init__']),(pdfplumber,['open']),(pypdfium2,['PdfDocument']),(Image,['open']),(socket,['socket']),(subprocess,['run','Popen'])]:
  for name in names:stack.enter_context(patch.object(obj,name,deny(name)))
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(tests.InfrastructurePrintedWorkflow)
 suite=unittest.TestSuite(t for t in suite if not t.id().endswith('test_ordinary_generic_profile_and_csv_are_unchanged'))
 result=unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps({'tests':result.testsRun,'passed':result.wasSuccessful(),'forbidden_calls':calls,'native_parse':False,'excluded_generic_dictionary_control':'Captured final family suite covers this unchanged generic control; review intentionally forbids opening any PDF'}))
raise SystemExit(0 if result.wasSuccessful()and not calls else 1)
