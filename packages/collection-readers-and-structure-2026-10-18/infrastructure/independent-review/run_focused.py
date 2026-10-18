import pathlib,sys,json,unittest,socket,subprocess,contextlib
from unittest.mock import patch
import pypdf,pdfplumber,pypdfium2
from PIL import Image
P=pathlib.Path(sys.argv[1]).resolve();sys.path.insert(0,str(P/'candidate'))
from collectors.encodeplus import test_infrastructure_logical as a,test_infrastructure_nested_list as b
calls=[]
def deny(name):
 def f(*args,**kw):calls.append(name);raise AssertionError('Review forbiddenAPI:'+name)
 return f
with contextlib.ExitStack()as st:
 for ob,names in [(pypdf,['PdfReader']),(pdfplumber,['open']),(pypdfium2,['PdfDocument']),(Image,['open']),(socket,['socket']),(subprocess,['run','Popen'])]:
  for n in names:st.enter_context(patch.object(ob,n,deny(n)))
 suite=unittest.TestSuite()
 for mod in (a,b):
  for group in unittest.defaultTestLoader.loadTestsFromModule(mod):
   for t in group:
    if not t.id().endswith('test_ordinary_generic_profile_and_csv_are_unchanged'):suite.addTest(t)
 result=unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps({'tests':result.testsRun,'passed':result.wasSuccessful(),'forbidden_calls':calls,'native_parse':False,'excluded_generic_control':'Unchanged dictionary-open control covered by captured140suite'}))
raise SystemExit(0 if result.wasSuccessful()and not calls else 1)
