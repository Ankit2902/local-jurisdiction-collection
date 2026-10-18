import runpy,sys,socket,base64,contextlib,json
from pathlib import Path
from unittest.mock import patch
import pdfplumber,pypdfium2
from PIL import Image
c=Path(sys.argv[1]);o=Path(sys.argv[2]);calls=[]
def no(*a,**kw):calls.append("forbidden");raise AssertionError("No native parse, network, image decode/render/extraction")
sys.path.insert(0,str(c));sys.argv=[str(c/'run_tests.py')]
with contextlib.ExitStack()as s:
 for obj,names in [(pdfplumber,['open']),(pypdfium2,['PdfDocument']),(pypdfium2.PdfPage,['render','get_objects']),(pypdfium2.PdfImage,['get_bitmap','get_data','extract']),(Image,['open']),(socket,['create_connection']),(base64,['b64decode'])]:
  for n in names:
   if hasattr(obj,n):s.enter_context(patch.object(obj,n,no))
 s.enter_context(patch.object(socket.socket,'connect',no))
 try:runpy.run_path(str(c/'run_tests.py'),run_name='__main__')
 except SystemExit as e:assert e.code==0,e.code
assert not calls
(o/'guarded-test-result.json').write_text(json.dumps({'passed':True,'forbidden_calls':calls,'new_native_parses':0,'network_requests':0,'image_decode_render_extract_OCR':False},indent=2)+'\n')
