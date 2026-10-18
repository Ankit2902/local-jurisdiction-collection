"""Explicit no-image API context for native text/metadata processing."""
import contextlib
from unittest.mock import patch,PropertyMock
@contextlib.contextmanager
def guard(calls):
 from pypdf._page import PageObject
 from pypdf.generic import EncodedStreamObject,DecodedStreamObject
 from pdfminer.pdftypes import PDFStream
 import pdfplumber,pypdfium2 as pdfium
 from PIL import Image
 def denied(*a,**kw):calls.append('blocked_image_api');raise AssertionError('Image bytes/pixels/render/OCR deliberately forbidden')
 original=PDFStream.get_data
 def stream(s,*a,**kw):
  attrs=s.attrs
  if getattr(attrs.get('Subtype'),'name',None)=='Image'or('W'in attrs and'H'in attrs)or('Width'in attrs and'Height'in attrs)or'ImageMask'in attrs:return denied()
  return original(s,*a,**kw)
 with contextlib.ExitStack()as stack:
  stack.enter_context(patch.object(PDFStream,'get_data',stream));stack.enter_context(patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=denied))
  for cls in [EncodedStreamObject,DecodedStreamObject]:
   old=cls.get_data
   def pg(s,*a,_old=old,**kw):
    if str(s.get('/Subtype'))=='/Image'or('/Width'in s and'/Height'in s)or'/ImageMask'in s:return denied()
    return _old(s,*a,**kw)
   stack.enter_context(patch.object(cls,'get_data',pg))
  for obj,names in [(pdfium.PdfPage,['render','get_objects']),(pdfium.PdfImage,['extract','get_bitmap','get_data']),(pdfplumber.page.Page,['to_image']),(Image,['open'])]:
   for n in names:
    if hasattr(obj,n):stack.enter_context(patch.object(obj,n,denied))
  yield
