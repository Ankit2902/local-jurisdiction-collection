"""Capture exact22 observed Clerk native PDFs then metadata-only page counts.

No all-page text parsing, image resources, pixels/render/OCR, retries or bypass.
"""
from pathlib import Path
import sys,json,hashlib,shutil,io,os,contextlib,time,traceback
from unittest.mock import patch,PropertyMock
P=Path(__file__).resolve().parent;R=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/github/local-jurisdiction-collection');sys.path.insert(0,str(R/'collectors/official'));import collect as current
scripts=current.runtime_scripts()
for name in scripts:shutil.copyfile(R/'collectors/official'/name,P/'runtime'/name)
for name in ['requirements.txt']:
 if(R/'collectors/official'/name).exists():shutil.copyfile(R/'collectors/official'/name,P/'runtime'/name)
# Use the immutable source snapshot in this new process, not production modules.
for name in ['collect','model','transport','post_transport','spokane_bulk']:sys.modules.pop(name,None)
sys.path.insert(0,str(P/'runtime'));import collect
from bs4 import BeautifulSoup
from pypdf import PdfReader
from pypdf._page import PageObject
from pypdf.generic import EncodedStreamObject,DecodedStreamObject
import pdfplumber,pypdfium2 as pdfium
from pdfminer.pdftypes import PDFStream
from PIL import Image
inventory=json.loads((P/'clark-uncodified-inventory.json').read_text());heads=json.loads((P/'size-summary.json').read_text());assert heads['complete']and heads['declared_total_bytes']<500_000_000
c={'schema':1,'id':'96-clark-clerk-uncodified-ordinances','jurisdiction':'Clark County','state':'NV','publication':'Uncodified ordinances listed by the Clark County Clerk, 5388–5409','source_url':inventory['source_url'],'mode':'pdf_set','transport':'http','document_transport':'http','inventory_selector':inventory['inventory_anchor_selector'],'include_url_regex':r'^https://weddings[.]vegas/wp-content/uploads/2026/(?:08|09)/ORD-[0-9]+[.]pdf$','source_currency_selector':'main .rightsection > .table.bordered.bid','source_identity_tokens':['ordinances that have been codified through Ordinance No. 5387','The following table is a list of code amendments that have not yet been codified.'],'coverage_level':'file_pages','pdf_normalization':'coordinate-v1','source_currency_scope':'Complete published ordinance table text including title/adopted/effective cells, not a claim that its dates are county-wide currency.','scope_warning':'Only 22 source-listed uncodified native ordinances. Separate required codified county code is 96-primary/Municode and remains stopped/unacquired here. Not Title30, all county law, all uncodified changes or an amendment application/edition opinion. No separate image requests or pixels/render/OCR; native originals may contain intrinsic images.'}
collect.save(P/'ordinance-config.json',c);capture=P/'capture';capture.mkdir(exist_ok=True);status={'pid':os.getpid(),'started_at':collect.transport.now(),'stage':'source-refresh','image_api_calls':[],'all_page_text_parse_performed':False};collect.save(P/'capture-status.json',status)
def forbidden(*a,**kw):status['image_api_calls'].append('forbidden_image');raise AssertionError('No image APIs/pixels/render allowed')
orig=PDFStream.get_data
def stream_guard(stream,*a,**kw):
 if getattr(stream.attrs.get('Subtype'),'name',None)=='Image'or('W'in stream.attrs and'H'in stream.attrs)or('Width'in stream.attrs and'Height'in stream.attrs):return forbidden()
 return orig(stream,*a,**kw)
started=time.monotonic()
try:
 with contextlib.ExitStack()as stack:
  stack.enter_context(patch.object(PDFStream,'get_data',stream_guard));stack.enter_context(patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=forbidden))
  for cls in [EncodedStreamObject,DecodedStreamObject]:
   old=cls.get_data
   def pg(stream,*a,_old=old,**kw):
    if str(stream.get('/Subtype'))=='/Image'or('/Width'in stream and'/Height'in stream)or stream.get('/ImageMask')is True:return forbidden()
    return _old(stream,*a,**kw)
   stack.enter_context(patch.object(cls,'get_data',pg))
  for obj,names in [(pdfium.PdfPage,['render','get_objects']),(pdfium.PdfImage,['extract','get_bitmap','get_data']),(pdfplumber.page.Page,['to_image']),(Image,['open'])]:
   for n in names:
    if hasattr(obj,n):stack.enter_context(patch.object(obj,n,forbidden))
  items,identity=collect.discover(capture,c);assert[(i['url'],i['heading'])for i in items]==[(i['url'],i['ordinance'])for i in inventory['uncodified_ordinances']],'Source inventory changed; no adjustment/retry'
  original=BeautifulSoup((P/'clark-county-code.html').read_bytes(),'html.parser');assert identity['source_currency']==collect.model.clean(original.select_one(c['source_currency_selector']).get_text(' ',strip=True)),'Source table titles/dates changed'
  collect.save(capture/'config.json',c);collect.save(capture/'inventory.json',items);collect.save(capture/'checkpoint.json',{'scripts':scripts,'stage':'capture-only','capture_complete':False,'identity':identity,'all_page_text_parse_performed':False})
  expected={i['url']:i['bytes']for i in heads['documents_inventory']};counts=[]
  for ordinal,item in enumerate(items,1):
   status.update(stage='native-capture-and-pagecount',next_document=ordinal,total_documents=22);collect.save(P/'capture-status.json',status)
   data,receipt,ref=collect.fetch_raw(capture,'item:'+item['id'],item['url'],c,kind='pdf');assert data.startswith(b'%PDF-')and not receipt.get('policy_omitted_image'),'Native PDF source required; no image/GET fallback';assert len(data)==expected[item['url']],'Native size changed since observed HEAD inventory'
   reader=PdfReader(io.BytesIO(data),strict=True);count=len(reader.pages);assert count>0;counts.append({'ordinance':item['heading'],'url':item['url'],'raw_ref':ref,'sha256':receipt['sha256'],'bytes':len(data),'physical_pages':count,'encrypted':reader.is_encrypted,'qualification':'Original capture and strict PDF page-tree count only; no text/table/image interpretation.'})
   collect.save(P/'capture-page-counts.json',{'documents':counts,'pages_counted':sum(x['physical_pages']for x in counts),'body_bytes':sum(x['bytes']for x in counts),'all_page_text_parse_performed':False});print(json.dumps(counts[-1]),flush=True)
  collect.save(capture/'checkpoint.json',{'scripts':scripts,'stage':'capture-only','capture_complete':True,'identity':identity,'all_page_text_parse_performed':False,'finished_at':collect.transport.now()});status.update(stage='capture-and-pagecount-terminal',finished_at=collect.transport.now(),elapsed_seconds=round(time.monotonic()-started,3),document_count=22,physical_page_count=sum(x['physical_pages']for x in counts),native_bytes=sum(x['bytes']for x in counts));collect.save(P/'capture-status.json',status)
except Exception as e:
 status.update(stage='stopped',error=repr(e),traceback=traceback.format_exc(),finished_at=collect.transport.now());collect.save(P/'capture-status.json',status);raise
