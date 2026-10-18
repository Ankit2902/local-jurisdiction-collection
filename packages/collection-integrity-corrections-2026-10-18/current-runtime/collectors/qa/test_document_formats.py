"""Concrete byte-format faults, not PDF legal-semantic or OCR validation."""
import importlib.util,io,sys,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'collectors/municode'))
spec=importlib.util.spec_from_file_location('qa_municode_document_model',ROOT/'collectors/municode/model.py');muni=importlib.util.module_from_spec(spec);spec.loader.exec_module(muni)
from collectors.ecode.media import qualify_asset
def qualified(family,data,extension,mime):
 url='https://example.invalid/appendix.'+extension
 if family=='municode':return muni.asset_qualification(url,data,{'content-type':mime})[0]=='acquired'
 try:qualify_asset(data,{'requested_url':url,'headers':{'content-type':mime}});return True
 except Exception:return False
class Tests(unittest.TestCase):
 def test_empty_and_truncated_pdf_never_qualified(self):
  for family in ['municode','ecode']:
   for data in [b'',b'%PDF-',b'%PDF-1.7\nnot a real PDF\n%%EOF']:
    with self.subTest(family=family,bytes=len(data)):self.assertFalse(qualified(family,data,'pdf','application/pdf'))
 def test_zip_crc_and_plain_text_baseline(self):
  b=io.BytesIO()
  with zipfile.ZipFile(b,'w',compression=zipfile.ZIP_STORED) as z:z.writestr('appendix.txt',b'Original appendix text')
  good=b.getvalue();bad=good.replace(b'Original appendix text',b'Corrupted appendix tex')
  for family in ['municode','ecode']:
   with self.subTest(family=family):self.assertTrue(qualified(family,good,'zip','application/zip'));self.assertFalse(qualified(family,bad,'zip','application/zip'));self.assertTrue(qualified(family,b'Operative appendix text','txt','text/plain'));self.assertFalse(qualified(family,b'','txt','text/plain'))
if __name__=='__main__':unittest.main(verbosity=2)
