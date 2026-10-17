"""Required nonimage byte/document integrity only; no semantic-completeness claims."""
import io
from urllib.parse import urlsplit

def qualify_document(data,url,content_type=''):
 if not data:raise ValueError('Required document is empty')
 mime=content_type.split(';',1)[0].strip().lower()
 if 'html' in mime or data.lstrip().lower().startswith((b'<!doctype html',b'<html')):
  raise ValueError('Required document is an unresolved HTML landing page')
 pdf=urlsplit(url).path.lower().endswith('.pdf') or mime=='application/pdf' or data.startswith(b'%PDF')
 if not pdf:return {'format':'non-PDF binary','qualification':'nonempty bytes only; document semantics unqualified','bytes':len(data)}
 if not data.startswith(b'%PDF-') or b'%%EOF' not in data[-1024:]:raise ValueError('Required PDF has missing/invalid header or EOF')
 from pypdf import PdfReader
 try:
  reader=PdfReader(io.BytesIO(data),strict=True)
  encrypted=bool(reader.is_encrypted)
  encryption_descriptor={}
  if encrypted:
   descriptor=reader.trailer.get('/Encrypt');descriptor=descriptor.get_object() if descriptor is not None else None
   if descriptor is not None:encryption_descriptor={str(k):str(descriptor[k]) for k in ['/Filter','/V','/R','/Length','/P','/EncryptMetadata'] if k in descriptor}
  count=len(reader.pages)
  if count<1:raise ValueError('PDF has no readable pages')
  for page in reader.pages:
   _=page.mediabox
   stream=page.get_contents()
   if stream is not None:stream.get_data()
   if encrypted:page.extract_text()
  if encrypted:
   # Ordinary reader defaults only: public empty-user permission encryption may open.
   # No supplied/guessed passwords, permission changes, or rewritten native bytes.
   import pypdfium2 as pdfium
   independent=pdfium.PdfDocument(data)
   try:
    if len(independent)!=count:raise ValueError('Independent public reader page count differs')
    for i in range(count):
     page=independent[i]
     try:
      textpage=page.get_textpage()
      try:textpage.get_text_range()
      finally:textpage.close()
     finally:page.close()
   finally:independent.close()
 except Exception as exc:raise ValueError('Required PDF structure is unqualified: '+str(exc)) from exc
 result={'format':'PDF','qualification':'strict parser, readable page tree/content streams; semantics not assessed','pages':count,'bytes':len(data)}
 if encrypted:result['public_open_encryption']={'encrypted':True,'descriptor':encryption_descriptor,'credentials_supplied':False,'ordinary_strict_all_page_text_and_stream_access':True,'ordinary_pdfium_all_page_text_access':True,'independent_page_count':count,'protection_or_permissions_changed':False,'native_bytes_rewritten':False,'scope':'Byte/document integrity only; no text agreement, table, edition or semantic qualification'}
 return result
