"""Nonimage document format checks. No image rendering/extraction or member files saved."""
import io,json,zipfile
from urllib.parse import urlsplit
from .common import QualificationError

def qualify_asset(raw,a):
 u=a['requested_url'];ctype=a.get('headers',{}).get('content-type','').lower();path=urlsplit(u).path.lower()
 if not raw or not raw.strip():raise QualificationError('Empty required attachment')
 if 'html' in ctype or raw.lstrip()[:40].lower().startswith((b'<!doctype html',b'<html')):raise QualificationError('Required binary attachment returned HTML')
 if 'application/pdf' in ctype or path.endswith('.pdf') or raw.lstrip().startswith(b'%PDF-'):
  if not raw.lstrip().startswith(b'%PDF-') or b'%%EOF' not in raw[-1024:]:raise QualificationError('Missing PDF signature/closing EOF')
  try:
   from pypdf import PdfReader
   reader=PdfReader(io.BytesIO(raw),strict=True)
   if reader.is_encrypted:raise QualificationError('Encrypted attachment is unqualified')
   pages=len(reader.pages)
   if pages<1:raise QualificationError('PDF has no pages')
  except Exception as e:raise QualificationError('Unqualified PDF: '+str(e)) from e
  return {'format':'pdf','pages':pages,'strict_parse':True,'image_objects_extracted':False}
 if path.endswith(('.zip','.docx','.xlsx','.pptx')) or raw.startswith(b'PK') or any(t in ctype for t in ['application/zip','officedocument']):
  try:
   with zipfile.ZipFile(io.BytesIO(raw)) as archive:
    infos=archive.infolist()
    if not infos:raise QualificationError('Empty archive')
    if any(i.flag_bits&1 for i in infos):raise QualificationError('Encrypted archive')
    bad=archive.testzip()
    if bad:raise QualificationError('ZIP CRC failure '+bad)
    members={i.filename for i in infos}
    for ext,main in [('.docx','word/document.xml'),('.xlsx','xl/workbook.xml'),('.pptx','ppt/presentation.xml')]:
     if path.endswith(ext) and main not in members:raise QualificationError('Office main document missing '+main)
  except Exception as e:raise QualificationError('Unqualified ZIP/Office archive: '+str(e)) from e
  return {'format':'zip_or_office','members':len(infos),'crc_checked':True,'member_files_saved':False}
 if any(ctype.startswith(t) for t in ['text/plain','text/csv','text/css','text/xml','application/xml','application/json']):
  try:text=raw.decode('utf-8-sig')
  except UnicodeDecodeError as e:raise QualificationError('Unsupported attachment text encoding') from e
  if not text.strip() or '\x00' in text:raise QualificationError('Empty/binary text attachment')
  if 'json' in ctype:
   try:json.loads(text)
   except ValueError as e:raise QualificationError('Invalid JSON attachment') from e
  if 'xml' in ctype:
   try:__import__('xml.etree.ElementTree',fromlist=['fromstring']).fromstring(text)
   except Exception as e:raise QualificationError('Invalid XML attachment') from e
  return {'format':'text','media_type':ctype,'encoding':'utf-8-sig'}
 raise QualificationError('Unsupported/unqualified nonimage attachment media '+ctype)
