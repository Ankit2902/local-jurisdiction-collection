"""Forward publisher-tag/MCID PDF reconstruction. No rendering or image decoding.

The forward tree is authoritative for ownership, including page continuations whose
reverse ParentTree index some native text devices fail to associate with a tag.
Artifacts are excluded from body text ONLY when explicitly marked /Artifact.
"""
import collections,hashlib,io,json,math,os
from pathlib import Path
from pypdf import PdfReader
from pypdf.generic import IndirectObject
POLICY='literal-[IMAGE]-no-image-fetch-v1'
VERSION='publisher-forward-tags-mcid-v1'
def sha(data):return hashlib.sha256(data).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def deref(x):return x.get_object() if hasattr(x,'get_object') else x
def attributes(x):
 x=deref(x)
 if isinstance(x,list):return [a for v in x for a in attributes(v)]
 return [x] if isinstance(x,dict) else []
def safe(x):
 x=deref(x)
 if isinstance(x,dict):return {str(k):safe(v) for k,v in x.items()}
 if isinstance(x,list):return [safe(v) for v in x]
 if isinstance(x,str) and x.lstrip().lower().startswith('data:image/'):return '[IMAGE]'
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 return str(x)
def inventory(data):
 reader=PdfReader(io.BytesIO(data));catalog=reader.trailer['/Root'];root=deref(catalog.get('/StructTreeRoot'))
 if not isinstance(root,dict):return None
 pages={p.indirect_reference.idnum:i+1 for i,p in enumerate(reader.pages)};rolemap=deref(root.get('/RoleMap',{}));classmap=deref(root.get('/ClassMap',{}));nodes=[];references=[];unsupported=[]
 def page_num(x):
  ref=x if isinstance(x,IndirectObject) else getattr(x,'indirect_reference',None);return pages.get(ref.idnum) if ref else None
 def walk(value,parent_key=(),parent_id=None,inherited_page=None):
  value=deref(value);values=value if isinstance(value,list) else [value];out=[]
  for i,raw in enumerate(values):
   v=deref(raw);key=parent_key+(i,);sid='tag:'+'.'.join(map(str,key))
   if isinstance(v,int):
    ref={'source_id':sid,'page':inherited_page,'mcid':int(v),'owner_id':parent_id};references.append(ref);out.append(dict(ref,kind='content'));continue
   if not isinstance(v,dict):continue
   page=page_num(v.get('/Pg')) or inherited_page
   if '/MCID' in v:
    if '/Stm' in v:unsupported.append({'source_id':sid,'reason':'Tagged separate-stream namespace needs an explicit profile'})
    ref={'source_id':sid,'page':page,'mcid':int(v['/MCID']),'owner_id':parent_id};references.append(ref);out.append(dict(ref,kind='content'));continue
   if v.get('/Type')=='/OBJR':
    unsupported.append({'source_id':sid,'reason':'Annotation/object reference requires an explicit citation and document-asset profile'});out.append({'kind':'object-reference','source_id':sid,'page':page});continue
   raw_role=str(v.get('/S',''));role=str(rolemap.get(raw_role,raw_role));attrs=attributes(v.get('/A',[]));classes=deref(v.get('/C',[]));classes=classes if isinstance(classes,list) else [classes]
   standard=set('/Document /DocumentFragment /Part /Art /Sect /Div /BlockQuote /Caption /TOC /TOCI /Index /NonStruct /Private /P /H /H1 /H2 /H3 /H4 /H5 /H6 /L /LI /Lbl /LBody /Table /TR /TH /TD /THead /TBody /TFoot /Span /Quote /Note /Reference /BibEntry /Code /Link /Annot /Ruby /RB /RT /RP /Warichu /WT /WP /Figure /Formula /Form /Aside /Title /FENote /Sub /Em /Strong'.split())
   if role not in standard:unsupported.append({'source_id':sid,'reason':'Unknown/unmapped source structure role '+role})
   for name in classes:
    if isinstance(name,int):continue
    if str(name) not in classmap:unsupported.append({'source_id':sid,'reason':'Unresolved source attribute class '+str(name)})
    else:attrs+=attributes(classmap[str(name)])
   span={k[1:]:int(a[k]) for a in attrs for k in ['/RowSpan','/ColSpan'] if k in a};assert all(v>0 for v in span.values()),'Nonpositive source table span'
   actual=str(v.get('/ActualText','')) or None;alt=str(v.get('/Alt','')) or None
   redact=actual is not None and actual.lstrip().lower().startswith('data:image/')
   n={'source_id':sid,'index_path':list(key),'parent_id':parent_id,'page':page,'raw_role':raw_role,'role':role,'span':span,'source_attributes':[safe(a) for a in attrs],'actual_text':'[IMAGE]' if redact else actual,'alt_text_sha256':sha(alt.encode()) if alt else None}
   if redact:n['actual_text_sha256']=sha(actual.encode())
   nodes.append(n);n['children']=walk(v.get('/K'),key,sid,page);out.append({'kind':'element','source_id':sid})
  return out
 roots=walk(root.get('/K'));lookup={n['source_id']:n for n in nodes};counts=collections.Counter((r['page'],r['mcid']) for r in references);duplicates=[list(k) for k,v in counts.items() if v>1];unbound=[r for r in references if r['page'] is None]
 def figure(owner):
  n=lookup.get(owner)
  # Available separately tagged Caption/P/Span/label descendants are text,
  # even when their ancestor is a Figure. Only direct graphic refs are images.
  return n['source_id'] if n and n['role']=='/Figure' else None
 for r in references:r['image_owner_id']=figure(r['owner_id'])
 return {'schema_version':1,'pages':len(reader.pages),'nodes':nodes,'roots':roots,'references':references,'duplicate_references':duplicates,'unbound_references':unbound,'unsupported':unsupported,'tagged':bool(deref(catalog.get('/MarkInfo',{})).get('/Marked',False))}

def _save(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_name(path.name+'.'+str(os.getpid())+'.tmp');temp.write_bytes(canonical(value)+b'\n');os.replace(temp,path)
def _page_reader(data,source_inventory,cache_dir=None,interrupt_after=None):
 from pdfminer.pdfparser import PDFParser
 from pdfminer.pdfdocument import PDFDocument
 from pdfminer.pdfpage import PDFPage
 from pdfminer.pdfinterp import PDFResourceManager,PDFPageInterpreter
 from pdfminer.converter import PDFPageAggregator
 from pdfminer.layout import LTChar,LTContainer
 from pdfminer.pdftypes import resolve1
 from pdfminer.utils import decode_text
 source_hash=sha(data);module_hash=sha(Path(__file__).read_bytes());invhash=sha(canonical(source_inventory));byref={(r['page'],r['mcid']):r for r in source_inventory['references']};directory=Path(cache_dir) if cache_dir else None
 if directory:
  expected={'source_sha256':source_hash,'inventory_sha256':invhash,'parser_sha256':module_hash,'image_policy':POLICY}
  header=directory/'binding.json'
  if header.exists():assert json.loads(header.read_text())==expected,'PDF page cache source/parser/policy binding differs'
  else:_save(header,expected)
 class Device(PDFPageAggregator):
  def begin_page(self,*a):
   super().begin_page(*a);self.stack=[];self.mcid=None;self.artifact=False;self.meta=[];self.active_meta=[];self.encountered=[]
  def begin_tag(self,tag,props=None):
   self.stack.append((self.mcid,self.artifact,self.active_meta[:]))
   props=resolve1(props)
   if tag.name=='Artifact':self.mcid=None;self.artifact=True
   elif isinstance(props,dict) and 'MCID' in props:self.mcid=int(resolve1(props['MCID']));self.encountered.append(self.mcid)
   if isinstance(props,dict) and 'ActualText' in props:
    raw=resolve1(props['ActualText']);text=decode_text(raw) if isinstance(raw,bytes) else str(raw);item={'mcid':self.mcid,'artifact':self.artifact,'replacement':text,'shown_glyph_text':''};self.meta.append(item);self.active_meta.append(len(self.meta)-1)
  def end_tag(self):self.mcid,self.artifact,self.active_meta=self.stack.pop() if self.stack else (None,False,[])
  def render_char(self,*a,**kw):
   advance=super().render_char(*a,**kw);c=self.cur_item._objs[-1];c.source_mcid=self.mcid;c.source_artifact=self.artifact
   for index in self.active_meta:self.meta[index]['shown_glyph_text']+=c.get_text()
   return advance
  def render_image(self,*a,**kw):pass
  def paint_path(self,*a,**kw):pass
 class Interpreter(PDFPageInterpreter):
  def do_BDC(self,tag,props):
   if hasattr(props,'name'):
    named=resolve1(self.resources.get('Properties',{}));assert isinstance(named,dict) and props.name in named,'Unresolved named marked-content property';props=resolve1(named[props.name])
   return super().do_BDC(tag,props)
 def chars(obj):
  if isinstance(obj,LTChar):yield obj
  elif isinstance(obj,LTContainer):
   for child in obj:yield from chars(child)
 def shaped(cs):
  # Preserve original Unicode separately. Geometry only supplies otherwise absent word/line separators.
  out=[];previous=None;inferences=[]
  for c in cs:
   value=c.get_text()
   if previous is not None and out and not out[-1].endswith(tuple(' \t\n\r')) and value and not value[0].isspace():
    dx=c.x0-previous.x1;dy=abs(c.matrix[5]-previous.matrix[5]);size=max(c.size,previous.size,1)
    if dy>size*.5:out.append('\n');inferences.append('line')
    elif dx>size*.2:out.append(' ');inferences.append('word')
   out.append(value);previous=c
  return ''.join(out),inferences
 doc=PDFDocument(PDFParser(io.BytesIO(data)));manager=PDFResourceManager();device=Device(manager,laparams=None);interpreter=Interpreter(manager,device);records=[];new_pages=0
 for page_number,page in enumerate(PDFPage.create_pages(doc),1):
  path=directory/('page-%04d.json'%page_number) if directory else None
  if path and path.exists():
   packet=json.loads(path.read_text());assert packet['source_sha256']==source_hash and packet['page']==page_number and packet['payload_sha256']==sha(canonical(packet['payload'])),'Corrupt PDF page checkpoint';records.append(packet['payload']);continue
  interpreter.process_page(page);groups=collections.defaultdict(list);artifact=[];unbound=[]
  for c in chars(device.get_result()):
   if c.source_artifact:artifact.append(c)
   elif c.source_mcid is None:unbound.append(c)
   else:groups[c.source_mcid].append(c)
  blocks=[];unknown=[]
  for mcid,cs in sorted(groups.items()):
   ref=byref.get((page_number,mcid));glyph=''.join(c.get_text() for c in cs);text,inferences=shaped(cs)
   if ref is None:unknown.append({'mcid':mcid,'glyph_sha256':sha(glyph.encode()),'character_count':len(glyph)})
   image=ref.get('image_owner_id') if ref else None
   blocks.append({'block_id':'page:%s:mcid:%s'%(page_number,mcid),'page':page_number,'mcid':mcid,'owner_id':ref['owner_id'] if ref else None,'image_owner_id':image,'glyph_text':glyph,'text':text,'content_classification':'available-source-Figure-label-text' if image else 'source-text','original_glyph_sha256':sha(glyph.encode()),'original_glyph_characters':len(glyph),'separator_inferences':inferences,'first_bbox':list(cs[0].bbox),'last_bbox':list(cs[-1].bbox)})
  metadata=[]
  for span in device.meta:
   ref=byref.get((page_number,span['mcid']));image=ref.get('image_owner_id') if ref else None;value=span['replacement'];shown=span['shown_glyph_text']
   if value.lstrip().lower().startswith('data:image/'):
    span=dict(span,replacement='[IMAGE]',shown_glyph_text='[IMAGE]',replacement_sha256=sha(value.encode()),shown_glyph_sha256=sha(shown.encode()))
   metadata.append(dict(span,page=page_number,owner_id=ref['owner_id'] if ref else None,image_owner_id=image))
  payload={'page':page_number,'blocks':blocks,'artifact_text':''.join(c.get_text() for c in artifact),'unbound_nonartifact_text':''.join(c.get_text() for c in unbound),'unknown_mcids':unknown,'inline_actual_text':metadata,'encountered_mcids':sorted(set(device.encountered)),'image_binary_extraction_count':0}
  if path:_save(path,{'source_sha256':source_hash,'page':page_number,'payload_sha256':sha(canonical(payload)),'payload':payload})
  records.append(payload);new_pages+=1
  if interrupt_after is not None and new_pages>=interrupt_after:raise KeyboardInterrupt('Injected PDF page checkpoint interruption')
 return records

def parse(data,cache_dir=None,interrupt_after=None):
 inv=inventory(data)
 if inv is None:return None
 assert inv['tagged'],'Structure tree is not marked as tagged source'
 pages=_page_reader(data,inv,cache_dir,interrupt_after);nodes={n['source_id']:n for n in inv['nodes']};blocks={b['block_id']:b for p in pages for b in p['blocks']};byref={(b['page'],b['mcid']):b for b in blocks.values()};used=[];sequence=[];figures=[]
 def refs_for(n):
  result=[]
  for c in n['children']:
   if c['kind']=='element':result+=refs_for(nodes[c['source_id']])
   elif c['kind']=='content':result.append((c['page'],c['mcid']))
  return result
 def render(n,emit=False):
  if n['role']=='/Figure':
   parts=[];marked=False
   if not any(c['kind']=='content' for c in n['children']):
    parts.append('[IMAGE]');marked=True
    if emit:sequence.append({'kind':'image','source_id':n['source_id'],'text':'[IMAGE]'})
   for child in n['children']:
    if child['kind']=='content':
     if not marked:
      parts.append('[IMAGE]');marked=True
      if emit:sequence.append({'kind':'image','source_id':n['source_id'],'text':'[IMAGE]'})
     if emit:used.append((child['page'],child['mcid']))
    elif child['kind']=='element':parts.append(render(nodes[child['source_id']],emit))
   if not marked:
    parts.insert(0,'[IMAGE]')
    if emit:sequence.append({'kind':'image','source_id':n['source_id'],'text':'[IMAGE]'})
   if emit:figures.append(n['source_id'])
   return '\n'.join(p for p in parts if p)
  parts=[];last_block=False
  for child in n['children']:
   if child['kind']=='content':
    ref=(child['page'],child['mcid']);block=byref.get(ref)
    if emit:used.append(ref);sequence.append({'kind':'text','source_id':child['source_id'],'block_id':block['block_id'] if block else None,'page':child['page'],'mcid':child['mcid'],'empty_source_text':not bool(block)})
    value=block['text'] if block else '';is_block=False
   elif child['kind']=='element':
    element=nodes[child['source_id']];value=render(element,emit);is_block=element['role'] not in ['/Span','/Quote','/Reference','/Link','/Lbl']
   else:continue
   if value:
    if parts and (is_block or last_block) and not parts[-1].endswith((' ','\n','\t')) and not value.startswith((' ','\n','\t')):parts.append('\n')
    parts.append(value);last_block=is_block
  return ''.join(parts)
 logical=[]
 for root in inv['roots']:
  if root['kind']=='element':logical.append(render(nodes[root['source_id']],True))
 labels=[]
 for index,ref in enumerate(inv['references']):
  block=byref.get((ref['page'],ref['mcid']))
  if ref.get('image_owner_id') and block:labels.append({'figure_source_id':ref['image_owner_id'],'source_reference_id':ref['source_id'],'source_order_index':index,'page':ref['page'],'mcid':ref['mcid'],'block_id':block['block_id'],'available_text':block['text'],'original_glyph_text':block['glyph_text'],'original_glyph_sha256':block['original_glyph_sha256'],'original_glyph_characters':block['original_glyph_characters'],'basis':'Available publisher vector/source glyph labels; not image transcription or OCR'})
 tables=[]
 def descend(n,wanted):
  for c in n['children']:
   if c['kind']!='element':continue
   child=nodes[c['source_id']]
   if child['role'] in wanted:yield child
   elif child['role']!='/Table':yield from descend(child,wanted)
 for n in inv['nodes']:
  if n['role']=='/Table':
   rows=[]
   for row in descend(n,{'/TR'}):rows.append([{'source_id':c['source_id'],'tag':c['role'][1:].lower(),'text':render(c),'rowspan':c['span'].get('RowSpan',1),'colspan':c['span'].get('ColSpan',1),'source_content_refs':[{'page':p,'mcid':m} for p,m in refs_for(c)]} for c in descend(row,{'/TH','/TD'})])
   parent=nodes.get(n['parent_id'])
   while parent and parent['role']!='/Table':parent=nodes.get(parent['parent_id'])
   tables.append({'source_id':n['source_id'],'parent_table_id':parent['source_id'] if parent else None,'rows':rows})
 expected=[(r['page'],r['mcid']) for r in inv['references']];actual=collections.Counter(used);assert not(set(actual)-set(expected)),'Uninventoried logical text source ref';assert set(actual)==set(expected) and all(v==1 for v in actual.values()),'Missing/duplicated source-owned logical body'
 encountered={(p['page'],mcid) for p in pages for mcid in p['encountered_mcids']};missing_content_refs=sorted(set(expected)-encountered)
 unknown=[{'page':p['page'],**m} for p in pages for m in p['unknown_mcids']];unbound=[p['page'] for p in pages if p['unbound_nonartifact_text'].strip()];supported=not inv['duplicate_references'] and not inv['unbound_references'] and not inv['unsupported'] and not unknown and not unbound and not missing_content_refs
 qualification={'source_structure_supported':supported,'source_text_qualified':supported,'source_tables_qualified':supported,'source_reading_order_qualified':supported,'legal_provision_segmentation_qualified':False,'source_node_count':len(nodes),'source_reference_count':len(expected),'unique_owned_reference_count':len(actual),'source_table_count':len(tables),'source_table_rows':sum(len(t['rows']) for t in tables),'source_table_cells':sum(len(row) for t in tables for row in t['rows']),'source_figure_placeholders':len(figures),'duplicate_source_references':inv['duplicate_references'],'unbound_source_references':inv['unbound_references'],'unsupported_source':inv['unsupported'],'missing_source_content_refs':[{'page':p,'mcid':m} for p,m in missing_content_refs],'unknown_marked_text':unknown,'unbound_nonartifact_pages':unbound,'actual_text_variant_count':sum(len(p['inline_actual_text']) for p in pages)+sum(n['actual_text'] is not None for n in inv['nodes']),'image_binary_extraction_count':0,'basis':'Forward publisher StructTreeRoot K/page/MCID order, source table roles/spans, explicit Artifact disposition. Visible Unicode and literal source ActualText retained separately; no inferred legal provision segmentation.'}
 qualification['available_figure_text_blocks']=len(labels);qualification['available_figure_text_characters']=sum(b['original_glyph_characters'] for b in labels)
 return {'schema_version':1,'parser_version':VERSION,'image_policy':POLICY,'source_sha256':sha(data),'source_inventory':inv,'pages':pages,'logical_sequence':sequence,'logical_text':'\n'.join(logical),'logical_text_is_derived_view':True,'available_figure_text':labels,'available_figure_text_is_derived_view':True,'tables':tables,'table_text_is_derived_view':True,'qualification':qualification}


def main():
 import argparse,sys,datetime,shutil,platform,importlib.metadata
 parser=argparse.ArgumentParser();parser.add_argument('--pdf',type=Path);parser.add_argument('--out',required=True,type=Path);parser.add_argument('--source-url',default='retained-native-pdf');parser.add_argument('--owner-id',default='publication-pdf');parser.add_argument('--resume',action='store_true');parser.add_argument('--verify',action='store_true');a=parser.parse_args()
 if a.verify:
  source=json.loads((a.out/'source.json').read_text());data=(a.out/'source.pdf').read_bytes();assert sha(data)==source['sha256'],'Corrupt source PDF';actual=parse(data);assert actual is not None;assert json.loads((a.out/'tagged-document.json').read_text())==actual,'Normalized tagged PDF output differs from original source recomputation';print(json.dumps(actual['qualification'],indent=2));return
 if a.resume:
  source=json.loads((a.out/'source.json').read_text());data=(a.out/'source.pdf').read_bytes();assert sha(data)==source['sha256'],'Corrupt source PDF'
 else:
  assert a.pdf and not a.out.exists(),'Fresh --pdf and --out required';data=a.pdf.read_bytes();a.out.mkdir(parents=True);(a.out/'source.pdf').write_bytes(data);_save(a.out/'source.json',{'sha256':sha(data),'bytes':len(data),'source_url':a.source_url,'owner_id':a.owner_id,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'parser_sha256':sha(Path(__file__).read_bytes()),'runtime':{'python':sys.version,'platform':platform.platform(),'packages':{name:importlib.metadata.version(name) for name in ['pypdf','pdfminer.six','PyMuPDF']}},'kind':'Offline parser qualification, not a new publisher acquisition'});shutil.copy2(__file__,a.out/'executed-pdf_tags.py')
 document=parse(data,a.out/'page-cache');assert document is not None,'No publisher structure tree; untagged PDF remains unqualified';_save(a.out/'tagged-document.json',document);(a.out/'logical-text.txt').write_text(document['logical_text']);_save(a.out/'qualification.json',document['qualification']);print(json.dumps(document['qualification'],indent=2));sys.exit(0 if document['qualification']['source_structure_supported'] else 2)
if __name__=='__main__':main()
