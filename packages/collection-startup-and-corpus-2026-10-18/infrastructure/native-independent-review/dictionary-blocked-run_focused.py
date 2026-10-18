import pathlib,sys,json,unittest,socket,subprocess,contextlib
from unittest.mock import patch
import pypdf,pdfplumber,pypdfium2
from pypdf.generic import EncodedStreamObject,DecodedStreamObject
from PIL import Image
P=pathlib.Path(sys.argv[1]).resolve();sys.path.insert(0,str(P/'candidate'))
from collectors.encodeplus import test_infrastructure_logical as tests
calls=[]
def deny(name):
 def f(*a,**k):calls.append(name);raise AssertionError('Review forbiddenAPI:'+name)
 return f
with contextlib.ExitStack()as stack:
 for obj,names in [(EncodedStreamObject,['get_data']),(DecodedStreamObject,['get_data']),(pdfplumber,['open']),(pypdfium2,['PdfDocument']),(Image,['open']),(socket,['socket']),(subprocess,['run','Popen'])]:
  for name in names:stack.enter_context(patch.object(obj,name,deny(name)))
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
print(json.dumps({'tests':result.testsRun,'passed':result.wasSuccessful(),'forbidden_calls':calls,'native_page_text_parse':False,'allowed_dictionary_only_generic_sixpage_control':True}))
raise SystemExit(0 if result.wasSuccessful()and not calls else 1)
