"""Three source pages: font/CID/operator text metadata, no text substitution or image work."""
import collections,hashlib,io,json,pathlib,sys,time
P=pathlib.Path(__file__).resolve().parents[3];R=P/'github/local-jurisdiction-collection';sys.path.insert(0,str(R))
from collectors.encodeplus import retained_native
from pdfminer.pdfinterp import PDFResourceManager,PDFPageInterpreter
from pdfminer.pdfdevice import PDFTextDevice
from pdfminer.pdfpage import PDFPage
from pypdf import PdfReader
S=R/'packages/collection-dispatch-and-municipal-2026-10-18/upoc-2024/actual-retained-full172';O=pathlib.Path(__file__).resolve().parent;sha=lambda x:hashlib.sha256(x).hexdigest();data=(S/'raw/source.pdf').read_bytes()
assert sha(data)=='877c6e874d4de7873d22dd51443fd5c42169445ad2955db3836841a105a57102'
assert sha((R/'collectors/encodeplus/retained_native.py').read_bytes())=='f7ef2d7ec3e12454c13be9fcb099c93f806b0a3ed451501bfc84f8707bb04bf3'
report={'source_sha256':sha(data),'pages':[],'selected_pages':[7,9,12]};t=time.monotonic()
class Manager(PDFResourceManager):
 def get_font(self,objid,spec):
  f=super().get_font(objid,spec);f.source_pdf_objid=objid;return f
class Device(PDFTextDevice):
 def __init__(self,m):super().__init__(m);self.glyphs=[];self.tags=[]
 def render_char(self,matrix,font,fontsize,scaling,rise,cid,ncs,graphicstate):
  try:unicode=font.to_unichr(cid)
  except Exception:unicode=None
  self.glyphs.append({'font_object':font.source_pdf_objid,'fontname':font.fontname,'cid':cid,'unicode':unicode,'text_matrix':list(matrix),'font_size':fontsize,'advance':font.char_width(cid)*fontsize*scaling});return font.char_width(cid)*fontsize*scaling
 def render_image(self,*a,**k):raise AssertionError('Selected cached pages have no image objects; refuse unexpected image')
 def begin_tag(self,tag,props=None):self.tags.append({'tag':str(tag),'props':{str(k):repr(v) for k,v in (props or {}).items()}})
with retained_native.guards() as calls:
 pr=PdfReader(io.BytesIO(data),strict=True);root=pr.trailer['/Root'];report['catalog_keys']=list(root);report['marked_info']=str(root.get('/MarkInfo'));report['StructTreeRoot_present']='/StructTreeRoot'in root
 for index,page in enumerate(PDFPage.get_pages(io.BytesIO(data),pagenos={n-1 for n in report['selected_pages']},check_extractable=True)):
  m=Manager();d=Device(m);PDFPageInterpreter(m,d).process_page(page);fontcounts=collections.Counter(str(g['font_object']) for g in d.glyphs);cidmap={f:sorted({g['cid'] for g in d.glyphs if str(g['font_object'])==f}) for f in fontcounts};physical=report['selected_pages'][index]
  report['pages'].append({'physical_page':physical,'source_glyphs':len(d.glyphs),'font_counts':dict(fontcounts),'font_CIDs':cidmap,'marked_content_tags':d.tags,'glyphs':d.glyphs})
 report['forbidden_calls']=calls[:]
assert not calls;report['seconds']=time.monotonic()-t;report['executed_source_sha256']=sha(pathlib.Path(__file__).read_bytes());(O/'bounded-used-code-probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='pages'}|{'pages':[{k:v for k,v in x.items() if k!='glyphs'} for x in report['pages']]},indent=2))
