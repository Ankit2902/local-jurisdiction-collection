"""Pinned real-parser PDF byte/structure qualification; no image extraction or legal-semantic claim."""
import hashlib,io,logging,warnings
EXPECTED_PYPDF='6.21.1'
_CACHE={}
def runtime_check():
 try:import pypdf
 except ImportError:return False,'pypdf=='+EXPECTED_PYPDF+' required; install collectors/municode/requirements.txt'
 return (pypdf.__version__==EXPECTED_PYPDF,'pypdf=='+pypdf.__version__+'; expected '+EXPECTED_PYPDF)
class Capture(logging.Handler):
 def __init__(self):super().__init__(logging.WARNING);self.messages=[]
 def emit(self,record):self.messages.append(record.getMessage())
def qualify_pdf(body):
 key=hashlib.sha256(body).hexdigest()
 if key in _CACHE:return dict(_CACHE[key])
 ok,runtime=runtime_check()
 if not ok:return {'status':'unqualified','reason':runtime}
 if not body.startswith(b'%PDF-') or not body.rstrip().endswith(b'%%EOF'):return {'status':'failed','reason':'PDF header/trailer missing or truncated'}
 from pypdf import PdfReader
 from pypdf.generic import IndirectObject,StreamObject,DictionaryObject,ArrayObject,NullObject
 handler=Capture();logger=logging.getLogger('pypdf');logger.addHandler(handler)
 try:
  with warnings.catch_warnings(record=True) as ww:
   warnings.simplefilter('always');reader=PdfReader(io.BytesIO(body),strict=True)
   if reader.is_encrypted and not reader.decrypt(''):raise ValueError('Encrypted PDF requires unavailable password')
   root=reader.trailer['/Root']
   if root.get('/Type')!='/Catalog':raise ValueError('PDF catalog missing')
   objects={}
   for generation,entries in reader.xref.items():
    if generation==65535:continue
    for ident,offset in entries.items():
     if ident:objects[(ident,generation)]=reader.get_object(IndirectObject(ident,generation,reader))
   for ident in reader.xref_objStm:objects[(ident,0)]=reader.get_object(IndirectObject(ident,0,reader))
   seen=set();nonimage_streams=0;image_streams=0
   def walk(obj):
    nonlocal nonimage_streams,image_streams
    if isinstance(obj,IndirectObject):
     key=(obj.idnum,obj.generation)
     if key in seen:return
     seen.add(key);resolved=reader.get_object(obj)
     if resolved is None:raise ValueError('Unresolved PDF indirect object '+str(key))
     walk(resolved);return
    if isinstance(obj,StreamObject):
     if obj.get('/Subtype')=='/Image':image_streams+=1 # Image contents are deliberately not decoded/extracted.
     else:obj.get_data();nonimage_streams+=1
    if isinstance(obj,DictionaryObject):
     for value in obj.values():walk(value)
    elif isinstance(obj,ArrayObject):
     for value in obj:walk(value)
   for key,obj in objects.items():
    if key not in seen:seen.add(key);walk(obj)
   pages=list(reader.pages)
   if not pages:raise ValueError('PDF has no physical pages')
   operators=0
   for page in pages:
    if page.get('/Type')!='/Page':raise ValueError('Invalid page-tree leaf')
    box=page.mediabox
    if len(box)!=4:raise ValueError('Malformed page media box')
    contents=page.get_contents()
    if contents is not None:operators+=len(contents.operations)
   notes=[str(w.message) for w in ww]+handler.messages
   if notes:raise ValueError('Strict PDF parser reported integrity warning: '+notes[0])
   result={'status':'acquired','reason':'pypdf '+EXPECTED_PYPDF+' strict catalog/xref/object/page/content integrity passed; images not extracted; no legal-semantic assertion','parser':'pypdf','parser_version':EXPECTED_PYPDF,'physical_pages':len(pages),'resolved_indirect_objects':len(objects),'decoded_nonimage_streams':nonimage_streams,'image_streams_not_decoded':image_streams,'page_content_operators':operators,'image_extraction':False}
 except Exception as e:result={'status':'failed','reason':'Strict pypdf integrity failure: '+type(e).__name__+': '+str(e)}
 finally:logger.removeHandler(handler)
 _CACHE[key]=result
 return dict(result)
