"""Stage original30 PDF bodies+real receipts with reviewed fetch_raw; no page text parse."""
import sys
sys.dont_write_bytecode=True
import json,hashlib,os,contextlib,traceback,io,time
from pathlib import Path
from unittest.mock import patch,PropertyMock
from discover import ROOT,transport
import collect
from pypdf import PdfReader
from pypdf._page import PageObject
from pdfminer.pdftypes import PDFStream
from PIL import Image
import pdfplumber,pypdfium2 as pdfium
CONFIG=ROOT/'configs/brla-udc-current-visible-documents.json';OUT=ROOT/'capture'
def save(n,v):collect.save(ROOT/n,v)
pre=json.loads((ROOT/'size-preflight.json').read_text())
assert pre['complete']and pre['selected']==30 and pre['unknown_lengths']==0 and pre['known_declared_bytes']<500_000_000
assert all(x['status']==200 and x['content_type'].split(';')[0].strip().lower()=='application/pdf'for x in pre['results'])
assert not OUT.exists(),'Capture output already exists; no automatic retry'
OUT.mkdir();c=collect.load(CONFIG);collect.save(OUT/'config.json',c)
status={'pid':os.getpid(),'stage':'opening','started_at':transport.now(),'image_calls':[],'source_byte_size_preflight':pre['known_declared_bytes'],'page_count_only_before_parse':True}
save('capture-status.json',status)
def no(*a,**kw):status['image_calls'].append('forbidden_image_API');save('capture-status.json',status);raise AssertionError('No image bytes/decode/render/OCR')
orig=PDFStream.get_data
def stream_guard(stream,*a,**kw):
 if getattr(stream.attrs.get('Subtype'),'name',None)=='Image'or('W'in stream.attrs and'H'in stream.attrs):return no()
 return orig(stream,*a,**kw)
try:
 with contextlib.ExitStack()as st:
  st.enter_context(patch.object(PDFStream,'get_data',stream_guard))
  st.enter_context(patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=no))
  for obj,names in [(pdfium.PdfPage,['render','get_objects']),(pdfium.PdfImage,['extract','get_bitmap','get_data']),(pdfplumber.page.Page,['to_image']),(Image,['open','frombytes'])]:
   for n in names:
    if hasattr(obj,n):st.enter_context(patch.object(obj,n,no))
  items,identity=collect.discover(OUT,c)
  expected=json.loads((ROOT/'brla-udc-inventory.json').read_text())['selected_visible_documents']
  assert [(i['url'],i['heading'])for i in items]==[(i['url'],i['label'])for i in expected],'Source inventory drift; no automatic adjustment'
  collect.save(OUT/'checkpoint.json',{'scripts':collect.runtime_scripts(),'stage':'capture-only','capture_complete':False,'pid':os.getpid()})
  docs=[];start=time.monotonic()
  for index,item in enumerate(items):
   status.update(stage='capture',next_document=index+1,total_documents=30);save('capture-status.json',status)
   data,meta,ref=collect.fetch_raw(OUT,'item:'+item['id'],item['url'],c,kind='pdf')
   assert not meta.get('policy_omitted_image')and data.startswith(b'%PDF-'),'Expected original native PDF; no substitution'
   pages=len(PdfReader(io.BytesIO(data),strict=True).pages)
   d={'ordinal':index,'id':item['id'],'label':item['heading'],'url':item['url'],'raw_ref':ref,'sha256':meta['sha256'],'bytes':len(data),'pages':pages}
   docs.append(d);assert sum(x['bytes']for x in docs)<=500_000_000,'Aggregate size exceeded authorized bound'
   print(json.dumps(d),flush=True)
  report={'stage':'capture_only_terminal','documents':docs,'document_count':30,'physical_pages':sum(x['pages']for x in docs),'original_bytes':sum(x['bytes']for x in docs),'capture_elapsed_seconds':time.monotonic()-start,'text_or_table_parse_performed':False,'page_count_method':'pypdf PdfReader.pages length only; no page content/images accessed','image_calls':status['image_calls'],'identity':identity,'whole_publication_qualified':False,'unlinked_widget_metadata':json.loads((ROOT/'brla-udc-inventory.json').read_text())['unlinked_widget_metadata']}
  save('native-capture-summary.json',report)
  collect.save(OUT/'checkpoint.json',{'scripts':collect.runtime_scripts(),'stage':'capture-only','capture_complete':True,'pid':os.getpid(),'finished_at':transport.now()})
  status.update(stage='capture_terminal_before_text_parse',finished_at=transport.now(),documents=30,pages=report['physical_pages'],bytes=report['original_bytes']);save('capture-status.json',status)
except BaseException as exc:
 status.update(stage='stopped',error=repr(exc),traceback=traceback.format_exc(),finished_at=transport.now());save('capture-status.json',status);raise
