#!/usr/bin/env python3
"""Independent original PDF -> tagged output audit, no pdf_tags/model imports.

Raw tree/MCID glyphs are independently read with PDFminer. A separate MuPDF
native text device checks page Unicode coverage, including unstructured legal
continuations; empty native structure paths are never assumed to be artifacts.
"""
import argparse,collections,hashlib,io,json,sys,unicodedata,re
from pathlib import Path
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdftypes import resolve1,PDFObjRef
from pdfminer.pdfinterp import PDFResourceManager,PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.utils import decode_text

def expected_image_metadata(value):
 """Remove every bounded base64 image URI; ambiguous mixed values cannot qualify."""
 cursor=0;pieces=[];found=False
 while True:
  start=value.lower().find('data:image/',cursor)
  if start<0:
   return (''.join(pieces)+value[cursor:],'bounded-quoted-image-URI',None) if found else (value,None,None)
  if start>0 and value[start-1] in ['"',"'"]:
   close=value.find(value[start-1],start)
   if close>=0 and re.fullmatch(r'data:image/[a-z0-9.+-]+;base64,[A-Za-z0-9+/=\s]*',value[start:close],re.I):
    pieces.extend([value[cursor:start],'[IMAGE]']);cursor=close;found=True;continue
  if start==0 and re.fullmatch(r'data:image/[a-z0-9.+-]+;base64,[A-Za-z0-9+/=\s]*',value,re.I):return '[IMAGE]','image-only-metadata',None
  return '[IMAGE]','ambiguous-mixed-text-image-payload',''.join(pieces)+value[cursor:start]
def norm(text):return ''.join(unicodedata.normalize('NFC',text).split())
def digest(data):return hashlib.sha256(data).hexdigest()
def native_variant_metadata(m,span,c,ctm,path):
 # span.font is borrowed: constructing an owning FzFont wrapper would drop the
 # live native font after the callback. The raw read-only accessor owns nothing.
 return {'unicode':chr(c.ucs),'font_name':m.ll_fz_font_name(span.font),'gid':c.gid,'x':ctm.a*c.x+ctm.c*c.y+ctm.e,'y':ctm.b*c.x+ctm.d*c.y+ctm.f,'structure_path':path[:]}
def role(v):return '/'+v.name if hasattr(v,'name') else str(v or '')
def attrs(v):
 v=resolve1(v)
 if isinstance(v,list):return [a for x in v for a in attrs(x)]
 return [v] if isinstance(v,dict) else []
def audit(data,normalized):
 doc=PDFDocument(PDFParser(io.BytesIO(data)));sourcepages=list(PDFPage.create_pages(doc));pageids={p.pageid:i+1 for i,p in enumerate(sourcepages)};tree=resolve1(doc.catalog['StructTreeRoot']);roles=resolve1(tree.get('RoleMap',{}));classes=resolve1(tree.get('ClassMap',{}));nodes={};references=[];roots=[];errors=[]
 if digest(data)!=normalized['source_sha256']:errors.append({'error':'Original source hash differs'})
 def walk(value,key=(),parent=None,pg=None):
  value=resolve1(value);values=value if isinstance(value,list) else [value];out=[]
  for i,raw in enumerate(values):
   v=resolve1(raw);path=key+(i,);sid='tag:'+'.'.join(map(str,path))
   if isinstance(v,int):references.append((pg,v,parent));out.append(('content',pg,v));continue
   if not isinstance(v,dict):continue
   ref=v.get('Pg');page=pageids.get(ref.objid) if isinstance(ref,PDFObjRef) else None;page=page or pg
   if 'MCID' in v:references.append((page,int(v['MCID']),parent));out.append(('content',page,int(v['MCID'])));continue
   if role(v.get('Type'))=='/OBJR':continue
   rawrole=role(v.get('S'));mapped=roles.get(rawrole[1:]);r=role(mapped) if mapped is not None else rawrole;attributes=attrs(v.get('A',[]));cs=resolve1(v.get('C',[]));cs=cs if isinstance(cs,list) else [cs]
   for c in cs:
    if hasattr(c,'name'):attributes+=attrs(classes.get(c.name,[]))
   spans={k:int(a[k]) for a in attributes for k in ['RowSpan','ColSpan'] if k in a};actual=resolve1(v.get('ActualText'));actual=decode_text(actual) if isinstance(actual,bytes) else actual
   n={'source_id':sid,'parent_id':parent,'page':page,'role':r,'raw_role':rawrole,'span':spans,'actual_text':actual or None}
   if n['actual_text'] is not None:
    replacement,mode,prefix=expected_image_metadata(n['actual_text'])
    if mode:n.update(actual_text_sha256=digest(n['actual_text'].encode()),actual_text=replacement,actual_text_redaction_mode=mode)
    if mode=='ambiguous-mixed-text-image-payload':n['actual_text_available_prefix']=prefix
   nodes[sid]=n;n['children']=walk(v.get('K'),path,sid,page);out.append(('element',sid))
  return out
 roots=walk(tree.get('K'));refmap={(p,m):owner for p,m,owner in references};source_counts=collections.Counter((p,m) for p,m,owner in references)
 if any(v!=1 for v in source_counts.values()):errors.append({'error':'Duplicate original source MCID'})
 def image_owner(owner):
  n=nodes.get(owner)
  return n['source_id'] if n and n['role']=='/Figure' else None
 class RawDevice(PDFPageAggregator):
  def begin_page(self,*a):super().begin_page(*a);self.stack=[];self.current=None;self.artifact=False;self.groups=collections.defaultdict(list);self.artifacts=[];self.unbound=[];self.meta=[];self.active=[];self.encountered=set();self.encoded_glyphs=[]
  def begin_tag(self,tag,properties=None):
   self.stack.append((self.current,self.artifact,self.active[:]));properties=resolve1(properties)
   if tag.name=='Artifact':self.current=None;self.artifact=True
   elif isinstance(properties,dict) and 'MCID' in properties:self.current=int(resolve1(properties['MCID']));self.encountered.add(self.current)
   if isinstance(properties,dict) and 'ActualText' in properties:
    raw=resolve1(properties['ActualText']);replacement=decode_text(raw) if isinstance(raw,bytes) else str(raw);self.meta.append({'mcid':self.current,'artifact':self.artifact,'replacement':replacement,'shown_glyph_text':''});self.active.append(len(self.meta)-1)
  def end_tag(self):self.current,self.artifact,self.active=self.stack.pop() if self.stack else (None,False,[])
  def render_char(self,*a,**kw):
   advance=super().render_char(*a,**kw);value=self.cur_item._objs[-1].get_text()
   if len(value)>1:
    matrix,font,_,_,_,cid=a[:6];name=font.fontname.decode() if isinstance(font.fontname,bytes) else str(font.fontname);self.encoded_glyphs.append({'font_name':name,'source_cid':cid,'decoded_unicode':value,'mcid':self.current,'matrix':list(matrix)})
   if self.artifact:self.artifacts.append(value)
   elif self.current is None:self.unbound.append(value)
   else:self.groups[self.current].append(value)
   for index in self.active:self.meta[index]['shown_glyph_text']+=value
   return advance
  def render_image(self,*a,**kw):pass
  def paint_path(self,*a,**kw):pass
 class Interpreter(PDFPageInterpreter):
  def do_BDC(self,tag,properties):
   if hasattr(properties,'name'):properties=resolve1(resolve1(self.resources.get('Properties',{}))[properties.name])
   return super().do_BDC(tag,properties)
 manager=PDFResourceManager();device=RawDevice(manager,laparams=None);interpreter=Interpreter(manager,device);glyphs={};pagefacts=[]
 for pno,page in enumerate(sourcepages,1):
  interpreter.process_page(page);glyphs.update({(pno,k):''.join(v) for k,v in device.groups.items()});pagefacts.append({'page':pno,'artifact_text':''.join(device.artifacts),'unbound':''.join(device.unbound),'inline_actual_text':device.meta[:],'encountered':set(device.encountered),'encoded_glyphs':device.encoded_glyphs[:]})
 actualnodes={n['source_id']:n for n in normalized['source_inventory']['nodes']}
 if len(actualnodes)!=len(normalized['source_inventory']['nodes']):errors.append({'error':'Duplicate normalized source-node identity'})
 if set(actualnodes)!=set(nodes):errors.append({'error':'Normalized source-node identity set differs'})
 for sid,n in nodes.items():
  other=actualnodes.get(sid)
  if other is None:continue
  children=[('element',c['source_id']) if c['kind']=='element' else ('content',c['page'],c['mcid']) for c in other['children'] if c['kind'] in ['element','content']]
  if n['children']!=children:errors.append({'error':'Original K/MCID child ordering differs','source_id':sid})
  if any(n[k]!=other[k] for k in ['parent_id','page','role','raw_role','span','actual_text']):errors.append({'error':'Original node role/page/parent/span/ActualText mismatch','source_id':sid})
  if any(n.get(k)!=other.get(k) for k in ['actual_text_sha256','actual_text_redaction_mode','actual_text_available_prefix']):errors.append({'error':'Image-policy source ActualText hash differs','source_id':sid})
 actualpages={p['page']:p for p in normalized['pages']};actualblocks={(b['page'],b['mcid']):b for p in normalized['pages'] for b in p['blocks']}
 if len(actualpages)!=len(sourcepages) or len(actualpages)!=len(normalized['pages']):errors.append({'error':'Physical source page omitted/duplicated'})
 if len(actualblocks)!=sum(len(p['blocks']) for p in normalized['pages']):errors.append({'error':'Duplicate normalized marked-text body identity'})
 for key,text in glyphs.items():
  block=actualblocks.get(key);owner=refmap.get(key);image=image_owner(owner)
  if not block or block['owner_id']!=owner or block['original_glyph_sha256']!=digest(text.encode()) or block['glyph_text']!=text:errors.append({'error':'Original MCID text/owner/image disposition mismatch','page':key[0],'mcid':key[1]})
 if set(actualblocks)!=set(glyphs):errors.append({'error':'Extra/omitted normalized marked-text blocks'})
 for fact in pagefacts:
  other=actualpages.get(fact['page'],{})
  if other.get('artifact_text')!=fact['artifact_text'] or other.get('unbound_nonartifact_text')!=fact['unbound']:errors.append({'error':'Original explicit Artifact/unbound text disposition mismatch','page':fact['page']})
  metas=[]
  for item in fact['inline_actual_text']:
   owner=refmap.get((fact['page'],item['mcid']));image=image_owner(owner);item=dict(item,page=fact['page'],owner_id=owner,image_owner_id=image)
   replacement=item['replacement'];redacted,mode,prefix=expected_image_metadata(replacement)
   if mode:
    shown=item['shown_glyph_text'];item.update(replacement=redacted,shown_glyph_text='[IMAGE]' if 'data:image/' in shown.lower() else shown,replacement_sha256=digest(replacement.encode()),shown_glyph_sha256=digest(shown.encode()),replacement_redaction_mode=mode)
    if mode=='ambiguous-mixed-text-image-payload':item['replacement_available_prefix']=prefix
   metas.append(item)
  if other.get('inline_actual_text')!=metas:errors.append({'error':'Original inline ActualText variants differ','page':fact['page']})
 ambiguous=any(n.get('actual_text_redaction_mode')=='ambiguous-mixed-text-image-payload' for n in nodes.values()) or any(expected_image_metadata(m['replacement'])[1]=='ambiguous-mixed-text-image-payload' for p in pagefacts for m in p['inline_actual_text'])
 if ambiguous and any(normalized['qualification'].get(k) for k in ['source_text_qualified','source_structure_supported','source_tables_qualified','source_reading_order_qualified']):errors.append({'error':'Ambiguous mixed ActualText/image payload cannot qualify complete source interpretation'})
 expectedlabels=[]
 for index,(page,mcid,owner) in enumerate(references):
  if image_owner(owner) and (page,mcid) in glyphs:expectedlabels.append((owner,index,page,mcid,glyphs[(page,mcid)],digest(glyphs[(page,mcid)].encode())))
 actual_labels=[(b['figure_source_id'],b['source_order_index'],b['page'],b['mcid'],b['original_glyph_text'],b['original_glyph_sha256']) for b in normalized.get('available_figure_text',[])]
 if expectedlabels!=actual_labels:errors.append({'error':'Original available Figure glyph label ledger or source order differs'})
 def text(n):
  if n['role']=='/Figure':
   children=[];marked=False
   for child in n['children']:
    if child[0]=='element':children.append(text(nodes[child[1]]))
    elif not marked:children.append('[IMAGE]');marked=True
   return ('' if marked else '[IMAGE]')+''.join(children)
  out=[]
  for c in n['children']:
   if c[0]=='element':out.append(text(nodes[c[1]]))
   else:out.append(glyphs.get((c[1],c[2]),''))
  return ''.join(out)
 expectedlogical=''.join(text(nodes[c[1]]) for c in roots if c[0]=='element')
 if norm(expectedlogical)!=norm(normalized['logical_text']):errors.append({'error':'Whole-book original forward K/MCID logical text order differs'})
 def descendants(n,wanted):
  for child in n['children']:
   if child[0]!='element':continue
   value=nodes[child[1]]
   if value['role'] in wanted:yield value
   elif value['role']!='/Table':yield from descendants(value,wanted)
 tables={t['source_id']:t for t in normalized['tables']};source_tables=[n for n in nodes.values() if n['role']=='/Table'];cells=0
 if len(tables)!=len(normalized['tables']):errors.append({'error':'Duplicate normalized table identity'})
 if set(tables)!={t['source_id'] for t in source_tables}:errors.append({'error':'Original table inventory differs'})
 for table in source_tables:
  expected=[]
  for row in descendants(table,{'/TR'}):
   expected.append([{'source_id':c['source_id'],'tag':c['role'][1:].lower(),'text':norm(text(c)),'rowspan':c['span'].get('RowSpan',1),'colspan':c['span'].get('ColSpan',1)} for c in descendants(row,{'/TH','/TD'})]);cells+=len(expected[-1])
  actual=[[{k:(norm(c[k]) if k=='text' else c[k]) for k in ['source_id','tag','text','rowspan','colspan']} for c in row] for row in tables.get(table['source_id'],{}).get('rows',[])]
  if expected!=actual:errors.append({'error':'Original table cell text/order/tag/span differs','source_id':table['source_id']})
 native_reports=[]
 import pymupdf
 from pypdf import PdfReader
 reader=PdfReader(io.BytesIO(data))
 def explicit_encoding(page_number,font_name,cid):
  evidence={};seen=set()
  def walk(resources,path):
   resources=resources.get_object() if hasattr(resources,'get_object') else resources or {};fonts=resources.get('/Font',{});fonts=fonts.get_object() if hasattr(fonts,'get_object') else fonts
   for name,ref in fonts.items():
    font=ref.get_object()
    if str(font.get('/BaseFont','')).lstrip('/')!=font_name or font.get('/ToUnicode') or font.get('/Subtype')!='/Type1':continue
    enc=font.get('/Encoding');enc=enc.get_object() if hasattr(enc,'get_object') else enc
    if not isinstance(enc,dict):continue
    code=None
    for token in enc.get('/Differences',[]):
     if isinstance(token,int):code=int(token)
     elif code is not None:
      if code==cid and str(token)=='/f_f':evidence[getattr(ref,'idnum',str(name))]={'font_object_id':getattr(ref,'idnum',None),'resource_path':path+'/'+str(name),'font_name':font_name,'font_subtype':'/Type1','source_cid':cid,'source_glyph_name':'/f_f','original_encoding_differences':list(map(str,enc.get('/Differences',[]))),'ToUnicode_present':False,'source_unicode':'ff','basis':'Explicit source Encoding Differences CID -> /f_f; component glyph names f + f, independently reader-decoded as ff'}
      code+=1
   objects=resources.get('/XObject',{});objects=objects.get_object() if hasattr(objects,'get_object') else objects
   for name,ref in objects.items():
    key=getattr(ref,'idnum',id(ref))
    if key in seen:continue
    seen.add(key);obj=ref.get_object()
    if obj.get('/Subtype')=='/Form':walk(obj.get('/Resources',resources),path+'/'+str(name))
  walk(reader.pages[page_number-1].get('/Resources'),'page:'+str(page_number))
  return next(iter(evidence.values())) if len(evidence)==1 else None
 m=pymupdf.mupdf
 class NativeDevice(m.FzDevice2):
  def __init__(self):
   super().__init__();self.use_virtual_begin_structure();self.use_virtual_end_structure();self.use_virtual_fill_text();self.use_virtual_stroke_text();self.use_virtual_ignore_text();self.fz_enable_device_hints(m.FZ_DONT_DECODE_IMAGES);self.path=[];self.characters=[];self.seen={};self.ligatures=[]
  def begin_structure(self,ctx,standard,raw,index):self.path.append(raw)
  def end_structure(self,ctx):
   if self.path:self.path.pop()
  def record(self,raw,mode,ctm):
   span=raw.head;chars=[];positions=[]
   while span:
    wrapped=m.FzTextSpan(span)
    for i in range(span.len):
     c=wrapped.items(i)
     if c.ucs>=0:
      chars.append(chr(c.ucs));positions.append((c.x,c.y))
      if c.ucs==0xfb00:self.ligatures.append(native_variant_metadata(m,span,c,ctm,self.path))
    span=span.next
   value=''.join(chars);key=(value,tuple(positions),tuple(self.path))
   if key in self.seen and self.seen[key]!=mode:return
   self.seen[key]=mode;self.characters.append(value)
  def fill_text(self,ctx,text,ctm,*args):self.record(text,'fill',ctm)
  def stroke_text(self,ctx,text,ctm,*args):self.record(text,'stroke',ctm)
  def ignore_text(self,ctx,text,ctm,*args):self.record(text,'ignore',ctm)
 native=pymupdf.open(stream=data,filetype='pdf')
 for pno,page in enumerate(native,1):
  device=NativeDevice();m.fz_run_page(page.this,device,m.FzMatrix(),m.FzCookie());source=''.join(t for (p,mcid),t in glyphs.items() if p==pno);source+=pagefacts[pno-1]['artifact_text']+pagefacts[pno-1]['unbound'];expected_chars=collections.Counter(norm(source));observed_chars=collections.Counter(norm(''.join(device.characters)));strict_missing=expected_chars-observed_chars;strict_extra=observed_chars-expected_chars;adjusted=observed_chars.copy();variants=[];used_source=set()
  for native_glyph in device.ligatures:
   matches=[(i,g) for i,g in enumerate(pagefacts[pno-1]['encoded_glyphs']) if i not in used_source and g['decoded_unicode']=='ff' and g['font_name']==native_glyph['font_name'] and abs(g['matrix'][4]-native_glyph['x'])<.02 and abs(page.rect.height-g['matrix'][5]-native_glyph['y'])<.02]
   if len(matches)!=1:continue
   index,source_glyph=matches[0];binding=explicit_encoding(pno,source_glyph['font_name'],source_glyph['source_cid'])
   if binding is None:continue
   used_source.add(index);adjusted[native_glyph['unicode']]-=1;adjusted.update('ff');variants.append({'source_sha256':digest(data),'page':pno,'source_owner_id':refmap.get((pno,source_glyph['mcid'])),'source_mcid':source_glyph['mcid'],'reader_font_CID_and_position':source_glyph,'original_font_encoding':binding,'native_glyph':native_glyph,'resolved_by_source_encoding':True,'strict_raw_unicode_equal':False,'normalization_applied':'None; one explicit font/CID/glyph-position bound ff ligature interpretation retained as both literal codepoint sequences'})
  missing=expected_chars-adjusted;extra=adjusted-expected_chars;ok=not missing and not extra;native_reports.append({'page':pno,'passed':ok,'source_characters':sum(expected_chars.values()),'native_characters':sum(observed_chars.values()),'strict_raw_unicode_equal':not strict_missing and not strict_extra,'strict_missing':dict(strict_missing),'strict_extra':dict(strict_extra),'source_encoding_variants':variants,'resolved_by_source_encoding':bool(variants) and ok,'missing':dict(missing),'extra':dict(extra)})
  if not ok:errors.append({'error':'Independent native Unicode page multiset differs','page':pno})
 native.close()
 return {'schema_version':1,'scope':'Independent original raw PDF tree/MCID glyph/Artifact/ActualText/whole logical order, available Figure labels and source table-cell audit; no pdf_tags or model imports','source_sha256':digest(data),'independent_native_pages_passed':sum(p['passed'] for p in native_reports),'native_pages_strict_raw_unicode_equal':sum(p['strict_raw_unicode_equal'] for p in native_reports),'source_encoding_resolved_native_variants':sum(len(p['source_encoding_variants']) for p in native_reports),'native_page_checks':native_reports,'source_pages':len(sourcepages),'source_nodes':len(nodes),'source_mcid_references':len(references),'source_tables':len(source_tables),'source_table_cells':cells,'source_available_Figure_label_blocks':len(expectedlabels),'source_available_Figure_label_characters':sum(len(v[4]) for v in expectedlabels),'source_nonimage_body_characters':len(norm(expectedlogical.replace('[IMAGE]',''))),'failures':errors,'passed':not errors}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('run',type=Path);parser.add_argument('--owner');args=parser.parse_args()
 if (args.run/'tagged-document.json').exists():data=(args.run/'source.pdf').read_bytes();normalized=json.loads((args.run/'tagged-document.json').read_text())
 else:
  pages=[json.loads(v) for v in (args.run/'pdf-pages.jsonl').read_bytes().splitlines()];owners={p['owner_id'] for p in pages if 'tagged_document' in p}
  owner=args.owner or (next(iter(owners)) if len(owners)==1 else None);assert owner in owners,'Choose one observed tagged PDF owner explicitly';rows=[p for p in pages if p['owner_id']==owner];normalized=dict(next(p['tagged_document'] for p in rows if 'tagged_document' in p),pages=[p['tagged_page'] for p in rows]);url=rows[0]['source_url'];requests=json.loads((args.run/'requests.json').read_text());entry=requests['binary:'+url];data=(args.run/entry['file']).read_bytes();assert digest(data)==entry['sha256'],'Corrupt original PDF'
 result=audit(data,normalized);print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':sys.exit(main())
