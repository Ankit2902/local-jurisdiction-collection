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
  if reader.is_encrypted:raise ValueError('Encrypted PDF is not qualified')
  count=len(reader.pages)
  if count<1:raise ValueError('PDF has no readable pages')
  for page in reader.pages:
   _=page.mediabox
   stream=page.get_contents()
   if stream is not None:stream.get_data()
 except Exception as exc:raise ValueError('Required PDF structure is unqualified: '+str(exc)) from exc
 return {'format':'PDF','qualification':'strict parser, readable page tree/content streams; semantics not assessed','pages':count,'bytes':len(data)}
