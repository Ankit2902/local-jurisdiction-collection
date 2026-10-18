import sys,pathlib,unittest,importlib.util,contextlib,socket,urllib.request,json
from unittest.mock import patch
sys.dont_write_bytecode=True
H=pathlib.Path(sys.argv[1]);name=sys.argv[2]
import pypdf,pdfplumber,pypdfium2
from PIL import Image
calls=[]
def denied(*a,**kw):calls.append('forbidden_native_image_network');raise AssertionError(calls[-1])
with contextlib.ExitStack()as stack:
 for obj,attr in [(pypdf,'PdfReader'),(pdfplumber,'open'),(pypdfium2,'PdfDocument'),(socket,'socket'),(socket,'create_connection'),(urllib.request,'urlopen'),(Image,'open'),(Image,'frombytes'),(Image,'fromarray'),(pdfplumber.page.Page,'to_image'),(pypdfium2.PdfPage,'render')]:stack.enter_context(patch.object(obj,attr,denied))
 spec=importlib.util.spec_from_file_location('review_tests',H/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 suite=unittest.defaultTestLoader.loadTestsFromModule(m)
 if name=='test_wrapper_compatibility':
  suite=unittest.TestSuite([m.Compatibility('test_legacy_current_published172_exactreport'),m.Compatibility('test_all_six_newreport_equivalence')])
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 assert not calls,'Forbidden operation attempted'
 print(json.dumps({'module':name,'tests':result.testsRun,'passed':result.wasSuccessful(),'native_constructor_image_network_calls':calls}))
 sys.exit(0 if result.wasSuccessful()else 3)
