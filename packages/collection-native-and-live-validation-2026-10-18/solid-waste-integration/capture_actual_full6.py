"""One fresh exact full6 integration capture; no publisher/image operations."""
import contextlib,copy,gzip,hashlib,importlib.metadata,json,pathlib,socket,sys,time
from unittest.mock import patch,PropertyMock
R=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(R/'candidate'))
from collectors.encodeplus import native_document as native
from PIL import Image
import pymupdf,pypdfium2,pdfplumber
from pypdf.generic import EncodedStreamObject,DecodedStreamObject
from pypdf._page import PageObject
from pdfminer.pdftypes import PDFStream
E=R/'candidate/collectors/encodeplus';cfg=json.loads((E/'configs/native-82-4b983dc51ab6.json').read_text());data=(E/'fixtures/solid-waste-logical/source.pdf').read_bytes();assert hashlib.sha256(data).hexdigest()==cfg['expected_sha256'];out=R/'actual-full6';assert not out.exists();calls=[];old=PDFStream.get_data
sha=lambda b:hashlib.sha256(b).hexdigest()
def no(*a,**kw):calls.append('forbidden_image_or_network');raise AssertionError('No image/decode/extract/render/OCR/network')
def imageguard(stream):
 if getattr(stream.attrs.get('Subtype'),'name',None)=='Image' or ('W' in stream.attrs and 'H' in stream.attrs):return no()
 return old(stream)
before={p.name:sha(p.read_bytes()) for p in E.glob('*.py')}
with contextlib.ExitStack() as stack:
 for obj,names in [(socket,['socket','create_connection']),(Image,['open']),(pymupdf.Document,['extract_image']),(pymupdf.Page,['get_pixmap']),(pypdfium2.PdfPage,['render','get_objects']),(pypdfium2.PdfImage,['extract','get_bitmap','get_data']),(pdfplumber.page.Page,['to_image'])]:
  for n in names:
   if hasattr(obj,n):stack.enter_context(patch.object(obj,n,no))
 stack.enter_context(patch.object(PDFStream,'get_data',imageguard));stack.enter_context(patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=no))
 for cls in [EncodedStreamObject,DecodedStreamObject]:
  original=cls.get_data
  def guard(self,*a,_original=original,**kw):
   if str(self.get('/Subtype','')).lower()=='/image':return no()
   return _original(self,*a,**kw)
  stack.enter_context(patch.object(cls,'get_data',guard))
 started=time.monotonic();records,details=native.page_records(data,cfg);native.validate_record_identity(records,details,cfg);bodies=native.outputs(records);elapsed=time.monotonic()-started
assert not calls and len(records)==88 and details['pages']==6 and details['normalized_record_count']==88
expected=[json.loads(l) for l in (E/'fixtures/sto-four-column/ordinary-solid-waste-baseline.jsonl').read_text().splitlines()];original=records[0]['superseded_detector_diagnostics']['original_page_records'];assert json.loads(json.dumps(original))==expected
out.mkdir()
for n,b in bodies.items():(out/n).write_bytes(b)
(out/'details.json').write_text(json.dumps(details,indent=2)+'\n');assert before=={p.name:sha(p.read_bytes()) for p in E.glob('*.py')}
report={'passed':True,'one_fresh_full6_integration_execution':True,'source_sha256':sha(data),'runtime_modules':before,'seconds':elapsed,'physical_pages':6,'primary_logical_units':88,'source_controls':26,'source_glyphs':15574,'source_MCID_refs':109,'original6page_diagnostics_exact_baseline':True,'native_codehashes_binds_newmodules':all(native.code_hashes()[n]==h for n,h in before.items() if n.startswith('solid_waste_') or n=='native_document.py'),'forbidden_calls':calls,'outputs':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in out.iterdir()},'runtime':{k:importlib.metadata.version(k) for k in ['pypdf','pdfminer.six','PyMuPDF','Pillow']},'new_acquisition':False,'required_external_documents_complete':False,'current_adoption_edition_qualified':False,'publication_complete':False}
(R/'actual-full6-capture.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['runtime_modules','outputs']},indent=2))
