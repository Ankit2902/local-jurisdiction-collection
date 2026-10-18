"""Standard family reconcile under network/pixel tripwires and immutable source/run maps."""
import sys
sys.dont_write_bytecode=True
import json,hashlib,socket,contextlib,traceback
from pathlib import Path
from unittest.mock import patch,PropertyMock
from discover import ROOT
import collect,pdfplumber,pypdfium2 as pdfium
from pypdf._page import PageObject
from pdfminer.pdftypes import PDFStream
from PIL import Image
run=ROOT/'run'
def hashes(p):return {f.relative_to(p).as_posix():hashlib.sha256(f.read_bytes()).hexdigest()for f in p.rglob('*')if f.is_file()}
before=hashes(run);sources=hashes(ROOT/'runtime');forbidden=[]
def no(*a,**kw):forbidden.append('network_or_image_API');raise AssertionError('Readonly verification forbids network/image/decode/render/OCR')
orig=PDFStream.get_data
def sg(s,*a,**kw):
 if getattr(s.attrs.get('Subtype'),'name',None)=='Image'or('W'in s.attrs and'H'in s.attrs):return no()
 return orig(s,*a,**kw)
with contextlib.ExitStack()as st:
 st.enter_context(patch.object(socket,'socket',no));st.enter_context(patch.object(PDFStream,'get_data',sg));st.enter_context(patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=no))
 for obj,names in [(pdfium.PdfPage,['render','get_objects']),(pdfium.PdfImage,['extract','get_bitmap','get_data']),(pdfplumber.page.Page,['to_image']),(Image,['open','frombytes'])]:
  for n in names:
   if hasattr(obj,n):st.enter_context(patch.object(obj,n,no))
 report=collect.reconcile(run)
assert before==hashes(run)and sources==hashes(ROOT/'runtime'),'Source/evidence changed during readonlyverify'
result={'run_files_sha256_before':before,'run_files_sha256_after':hashes(run),'collector_source_sha256_before':sources,'collector_source_sha256_after':hashes(ROOT/'runtime'),'evidence_read_only':True,'publisher_requests':0,'forbidden_calls':forbidden,'coverage':report,'verification_scope':'Standardfamilyreconcile selected thirtyvisible officialnativePDF file_pages; no commonlauncher or legal/jurisdiction upgrade'}
collect.save(ROOT/'family-readonly-verification.json',result)
print(json.dumps({'requested_coverage_complete':report['requested_coverage_complete'],'run_files':len(before),'sources':len(sources),'forbidden_calls':forbidden,'evidence_read_only':True},indent=2))
raise SystemExit(0 if report['requested_coverage_complete']else 3)
