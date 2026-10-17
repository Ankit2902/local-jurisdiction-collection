"""Native glyph and image-placement metadata only; never decode or render images."""
import hashlib,json,io
import pymupdf
def page_evidence(page):
 m=pymupdf.mupdf
 class Device(m.FzDevice2):
  def __init__(self):
   super().__init__();self.fz_enable_device_hints(m.FZ_DONT_DECODE_IMAGES);self.use_virtual_fill_text();self.use_virtual_stroke_text();self.use_virtual_ignore_text();self.use_virtual_fill_image();self.use_virtual_fill_image_mask();self.use_virtual_clip_image_mask();self.glyphs=[];self.images=[];self.seen={}
  def record(self,text,mode,ctm):
   span=text.head;items=[]
   while span:
    wrapped=m.FzTextSpan(span)
    for i in range(span.len):
     c=wrapped.items(i);x=ctm.a*c.x+ctm.c*c.y+ctm.e;y=ctm.b*c.x+ctm.d*c.y+ctm.f;items.append({'unicode':c.ucs,'text':chr(c.ucs) if c.ucs>=0 else None,'x':round(x,5),'y':round(y,5)})
    span=span.next
   key=json.dumps(items,sort_keys=True)
   if key in self.seen and self.seen[key]!=mode:return
   self.seen[key]=mode;self.glyphs.extend(items)
  def fill_text(self,ctx,text,ctm,*args):self.record(text,'fill',ctm)
  def stroke_text(self,ctx,text,ctm,*args):self.record(text,'stroke',ctm)
  def ignore_text(self,ctx,text,ctm,*args):self.record(text,'ignore',ctm)
  def image(self,ctm,kind):
   matrix=m.FzMatrix(ctm);box=m.fz_transform_rect(m.FzRect(0,0,1,1),matrix)
   self.images.append({'ordinal':len(self.images),'kind':kind,'bbox':[round(getattr(box,k),5) for k in ['x0','y0','x1','y1']],'placeholder':'[IMAGE]'})
  def fill_image(self,ctx,image,ctm,*args):self.image(ctm,'image')
  def fill_image_mask(self,ctx,image,ctm,*args):self.image(ctm,'image-mask')
  def clip_image_mask(self,ctx,image,ctm,*args):self.image(ctm,'image-mask-clip')
 device=Device();m.fz_run_page(page.this,device,m.FzMatrix(),m.FzCookie())
 text=''.join(g['text'] or '' for g in device.glyphs)
 return {'engine':'MuPDF '+pymupdf.VersionBind+' native device FZ_DONT_DECODE_IMAGES','glyph_count':len(device.glyphs),'unmapped_glyph_count':sum(g['text'] is None for g in device.glyphs),'glyph_text':text,'glyph_text_sha256':hashlib.sha256(text.encode()).hexdigest(),'glyphs':device.glyphs,'coordinate_basis':'MuPDF transformed page coordinates, top origin','image_placements':device.images,'image_binary_extraction_count':0,'image_decode_enabled':False}

def image_placements(data):
 """Read image draw operators and CTMs without accessing image stream data.

 MuPDF's DONT_DECODE_IMAGES deliberately skips image callbacks, so absence of
 those callbacks is never used as evidence that a source page has no images.
 """
 from pdfminer.pdfparser import PDFParser
 from pdfminer.pdfdocument import PDFDocument
 from pdfminer.pdfpage import PDFPage
 from pdfminer.pdfinterp import PDFResourceManager,PDFPageInterpreter
 from pdfminer.pdfdevice import PDFDevice
 from pdfminer.utils import apply_matrix_pt
 class Images(PDFDevice):
  def begin_page(self,page,ctm):self.rows=[]
  def render_image(self,name,stream):
   points=[apply_matrix_pt(self.ctm,p) for p in [(0,0),(0,1),(1,0),(1,1)]]
   box=[min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]
   self.rows.append({'ordinal':len(self.rows),'source_object_name':str(name) if not str(name).isdigit() else 'inline-image','source_xobject_id':getattr(stream,'objid',None),'bbox':list(map(lambda x:round(x,5),box)),'coordinate_basis':'PDFminer transformed page coordinates, bottom origin','placeholder':'[IMAGE]'})
 class Interpreter(PDFPageInterpreter):
  def do_Do(self,name):
   try:return super().do_Do(name)
   finally:self.device.set_ctm(self.ctm)
 doc=PDFDocument(PDFParser(io.BytesIO(data)));manager=PDFResourceManager();device=Images(manager);interpreter=Interpreter(manager,device);result=[]
 for page in PDFPage.create_pages(doc):interpreter.process_page(page);result.append(device.rows)
 return result
