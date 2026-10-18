"""PDF glyph/MCID/font/position ledger. No image stream decoding or rendering."""
import io
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager,PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdftypes import resolve1

def extract(data):
 class Device(PDFPageAggregator):
  def begin_page(self,*a):
   super().begin_page(*a);self.stack=[];self.mcid=None;self.artifact=False;self.rows=[];self.tag_events=[];self.paths=0
  def begin_tag(self,tag,props=None):
   self.stack.append((self.mcid,self.artifact));props=resolve1(props);name=tag.name
   if name=='Artifact':self.mcid=None;self.artifact=True
   elif isinstance(props,dict) and 'MCID' in props:self.mcid=int(resolve1(props['MCID']))
   self.tag_events.append({'event':'begin','tag':name,'mcid':self.mcid,'artifact':self.artifact,'glyph_ordinal':len(self.rows),'property_keys':sorted(props) if isinstance(props,dict) else []})
  def end_tag(self):
   self.tag_events.append({'event':'end','mcid':self.mcid,'artifact':self.artifact,'glyph_ordinal':len(self.rows)});self.mcid,self.artifact=self.stack.pop() if self.stack else (None,False)
  def render_char(self,matrix,font,fontsize,scaling,rise,cid,ncs,graphicstate):
   advance=super().render_char(matrix,font,fontsize,scaling,rise,cid,ncs,graphicstate);c=self.cur_item._objs[-1];self.rows.append({'ordinal':len(self.rows),'text':c.get_text(),'font':c.fontname,'font_size':c.size,'font_source_size':fontsize,'cid':cid,'matrix':list(matrix),'bbox':list(c.bbox),'advance':advance,'source_mcid':self.mcid,'source_artifact':self.artifact});return advance
  def render_image(self,*a,**kw):raise AssertionError('Unexpected source image: profile excludes images; image bytes are never decoded')
  def paint_path(self,*a,**kw):self.paths+=1
 class Interpreter(PDFPageInterpreter):
  def do_BDC(self,tag,props):
   if hasattr(props,'name'):
    named=resolve1(self.resources.get('Properties',{}));assert isinstance(named,dict) and props.name in named;props=resolve1(named[props.name])
   return super().do_BDC(tag,props)
 doc=PDFDocument(PDFParser(io.BytesIO(data)));manager=PDFResourceManager();device=Device(manager,laparams=None);interpreter=Interpreter(manager,device);pages=[]
 for number,page in enumerate(PDFPage.create_pages(doc),1):
  interpreter.process_page(page)
  for row in device.rows:row.update(page=number,glyph_id=f'p{number}:g{row["ordinal"]:05d}')
  pages.append({'page':number,'mediabox':list(page.mediabox),'glyphs':device.rows,'tag_events':device.tag_events,'path_paint_operators':device.paths,'image_decode_calls':0})
 return pages
