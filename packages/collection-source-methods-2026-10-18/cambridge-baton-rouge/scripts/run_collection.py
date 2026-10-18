"""Actual unchanged standardcollector using successful capture-only raw import.
Fresh discovery and later page/all30 native responses; all-page parsing is guarded.
"""
import sys
sys.dont_write_bytecode=True
import contextlib,json,traceback
from pathlib import Path
from unittest.mock import patch,PropertyMock
from discover import ROOT,transport
import collect,pdfplumber,pypdfium2 as pdfium
from pypdf._page import PageObject
from pdfminer.pdftypes import PDFStream
from PIL import Image
c=ROOT/'configs/brla-udc-current-visible-documents.json'
assert json.loads((ROOT/'native-capture-summary.json').read_text())['document_count']==30
status={'stage':'standard_collection','started_at':transport.now(),'image_calls':[],'native_original_source':'capture/; source-bound real receipts; no prior normalizer completion claimed'}
def save():collect.save(ROOT/'collection-status.json',status)
def no(*a,**kw):status['image_calls'].append('forbidden_image_API');save();raise AssertionError('Image pixels/decode/render/extract/OCR forbidden')
orig=PDFStream.get_data
def sg(s,*a,**kw):
 if getattr(s.attrs.get('Subtype'),'name',None)=='Image'or('W'in s.attrs and'H'in s.attrs):return no()
 return orig(s,*a,**kw)
save()
try:
 with contextlib.ExitStack()as st:
  st.enter_context(patch.object(PDFStream,'get_data',sg));st.enter_context(patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=no))
  for obj,names in [(pdfium.PdfPage,['render','get_objects']),(pdfium.PdfImage,['extract','get_bitmap','get_data']),(pdfplumber.page.Page,['to_image']),(Image,['open','frombytes'])]:
   for n in names:
    if hasattr(obj,n):st.enter_context(patch.object(obj,n,no))
  code=collect.collect(c,ROOT/'run',from_cache=ROOT/'capture')
  status.update(stage='standard_collection_terminal',exit_code=code,finished_at=transport.now());save();raise SystemExit(code)
except SystemExit:raise
except BaseException as e:
 status.update(stage='stopped',error=repr(e),traceback=traceback.format_exc(),finished_at=transport.now());save();raise
