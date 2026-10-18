"""Read-only standard official verifier, no network/images/rendering; stdout JSON receipt."""
import pathlib,sys,contextlib,socket,json,time,hashlib
from unittest.mock import patch,PropertyMock
OUT=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(OUT/'runtime'))
import verify,collect,pdfplumber,pypdfium2 as pdfium
from pypdf._page import PageObject
from pdfminer.pdftypes import PDFStream
from PIL import Image
calls=[]
def forbidden(*a,**k):calls.append('network_image_render_api');raise AssertionError('Offline noimage verifier forbids API')
orig=PDFStream.get_data
def guard(stream,*a,**k):
 if getattr(stream.attrs.get('Subtype'),'name',None)=='Image' or ('W' in stream.attrs and 'H' in stream.attrs):return forbidden()
 return orig(stream,*a,**k)
def files():return {str(p.relative_to(OUT/'run')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (OUT/'run').rglob('*') if p.is_file()}
before=files();started=collect.transport.now()
with contextlib.ExitStack() as stack:
 stack.enter_context(patch.object(PDFStream,'get_data',guard));stack.enter_context(patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=forbidden))
 for obj,names in [(socket,['socket','create_connection']),(pdfium.PdfPage,['render','get_objects']),(pdfium.PdfImage,['extract','get_bitmap','get_data']),(pdfplumber.page.Page,['to_image']),(Image,['open'])]:
  for name in names:
   if hasattr(obj,name):stack.enter_context(patch.object(obj,name,forbidden))
 r=verify.verify(OUT/'run')
 after=files();assert before==after,'Offline verifier mutated run';print(json.dumps({'run_file_count':len(before),'all_run_files_unchanged':before==after,'run_manifest_sha256':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),'started_at':started,'finished_at':collect.transport.now(),'forbidden_calls':calls,'coverage':collect.brief(r),'pdf_text_table_qa':r.get('pdf_text_table_qa')},indent=2))
 raise SystemExit(0 if r['requested_coverage_complete'] else 3)
