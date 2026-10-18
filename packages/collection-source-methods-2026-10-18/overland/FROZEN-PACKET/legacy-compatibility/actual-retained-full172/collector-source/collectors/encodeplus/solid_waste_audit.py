#!/usr/bin/env python3
"""Original PDF -> logical export audit. Imports no extraction/profile/tag parser code."""
import argparse,collections,csv,functools,hashlib,io,json,pathlib,re,sys
from pypdf import PdfReader
from pypdf.generic import IndirectObject,ContentStream
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager,PDFPageInterpreter
from pdfminer.pdfdevice import PDFTextDevice
from pdfminer.layout import LTChar
from pdfminer.pdftypes import resolve1
import pymupdf
from . import solid_waste_native as pdf_native
PIN='1af70bb8170cf2701cfb9e7ede2b274bf848309ca6fcaa3b7a7eeba9cd426c39';PUB='native-82-4b983dc51ab6';POLICY='literal-[IMAGE]-no-image-fetch-v1'
def sha(b):return hashlib.sha256(b).hexdigest()
def uid(key):return PUB+'::'+key

def original_tree(data):
 reader=PdfReader(io.BytesIO(data));assert len(reader.pages)==6;pageids={p.indirect_reference.idnum:i+1 for i,p in enumerate(reader.pages)};nodes=[];refs=[]
 for p in reader.pages:assert not p['/Resources'].get('/XObject')
 def page_of(value,inherited):
  if '/Pg' not in value:return inherited
  ref=value.raw_get('/Pg');return pageids[ref.idnum if isinstance(ref,IndirectObject) else ref.indirect_reference.idnum]
 def children(value):
  value=value.get_object() if hasattr(value,'get_object') else value;return value if isinstance(value,list) else [value]
 def visit(value,path,parent=None,page=None,owner=None):
  value=value.get_object() if hasattr(value,'get_object') else value
  if isinstance(value,int):assert page is not None and owner is not None;refs.append({'page':page,'mcid':value,'owner':owner});return
  assert isinstance(value,dict);page=page_of(value,page)
  if '/MCID' in value and '/S' not in value:refs.append({'page':page,'mcid':int(value['/MCID']),'owner':owner});return
  role=str(value['/S']);sid='tag:'+'.'.join(map(str,path));nodes.append({'id':sid,'role':role,'parent':parent,'order':len(nodes)})
  for index,child in enumerate(children(value['/K'])):visit(child,[*path,index],sid,page,sid)
 for index,value in enumerate(children(reader.root_object['/StructTreeRoot']['/K'])):visit(value,[index])
 assert len(nodes)==191 and len(refs)==109 and len({(r['page'],r['mcid']) for r in refs})==109
 return nodes,refs

@functools.lru_cache(maxsize=1)
def original_glyphs(data):
 assert sha(data)==PIN,'Source SHA mismatch; original profile unqualified'
 class Device(PDFTextDevice):
  def begin_page(self,page,ctm):self.stack=[];self.mcid=None;self.artifact=False;self.rows=[]
  def begin_tag(self,tag,props=None):
   self.stack.append((self.mcid,self.artifact));props=resolve1(props)
   if tag.name=='Artifact':self.artifact=True;self.mcid=None
   elif isinstance(props,dict) and 'MCID' in props:self.mcid=int(resolve1(props['MCID']))
  def end_tag(self):self.mcid,self.artifact=self.stack.pop()
  def render_char(self,matrix,font,fontsize,scaling,rise,cid,ncs,graphicstate):
   assert not font.is_vertical();value=font.to_unichr(cid);c=LTChar(matrix,font,fontsize,scaling,rise,value,font.char_width(cid),font.char_disp(cid),ncs,graphicstate);self.rows.append({'text':value,'cid':cid,'font':c.fontname,'font_size':c.size,'matrix':list(matrix),'bbox':list(c.bbox),'source_mcid':self.mcid,'source_artifact':self.artifact});return c.adv
  def render_image(self,*args):raise AssertionError('Image interpreter path forbidden')
 class Interpreter(PDFPageInterpreter):
  def do_BDC(self,tag,props):
   if hasattr(props,'name'):props=resolve1(resolve1(self.resources['Properties'])[props.name])
   return super().do_BDC(tag,props)
 manager=PDFResourceManager();device=Device(manager);interpreter=Interpreter(manager,device);doc=PDFDocument(PDFParser(io.BytesIO(data)));pages=[]
 for number,page in enumerate(PDFPage.create_pages(doc),1):
  interpreter.process_page(page)
  for i,g in enumerate(device.rows):g.update(page=number,ordinal=i,glyph_id=f'p{number}:g{i:05d}')
  pages.append(device.rows)
 native=[];pdf=pymupdf.open(stream=data,filetype='pdf');max_dx=0;max_ref_dx=0
 for rows,page in zip(pages,pdf):
  witness=pdf_native.page_evidence(page);assert witness['glyph_count']==len(rows) and witness['glyph_text']==''.join(g['text'] for g in rows),'Independent native glyph stream mismatch';seen=set()
  for g,n in zip(rows,witness['glyphs']):
   dx=abs(g['matrix'][4]-n['x']);max_dx=max(max_dx,dx)
   if not g['source_artifact'] and g['source_mcid'] not in seen:seen.add(g['source_mcid']);max_ref_dx=max(max_ref_dx,dx);assert dx<.001 and abs((792-g['matrix'][5])-n['y'])<.001,'Independent source content-anchor position differs'
  native.append({'glyphs':len(rows),'glyph_text_sha256':witness['glyph_text_sha256']})
 assert sum(len(p) for p in pages)==15574
 return pages,{'engine':'MuPDF native text device FZ_DONT_DECODE_IMAGES','pages':native,'full_glyph_sequence_including_whitespace_equal':True,'max_internal_glyph_advance_x_difference_points':max_dx,'max_content_ref_anchor_x_difference_points':max_ref_dx,'all109content_ref_anchors_agree_within001pt':True,'geometry_claim':'Internal glyph advances retain both reader values; no all-glyph coordinate equality claim.'}

def expected_text(gs):
 out=[];previous=None
 for g in gs:
  t=g['text']
  if previous and out and not out[-1][-1:].isspace() and t and not t[0].isspace():
   size=max(g['font_size'],previous['font_size']);newline=g['page']!=previous['page'] or abs(g['matrix'][5]-previous['matrix'][5])>size/2
   if newline:out.append('\n')
   elif g['bbox'][0]-previous['bbox'][2]>size/5:out.append(' ')
  out.append(t);previous=g
 return ''.join(out).strip()

def derive_hierarchy(ordered):
 """Different source-label/indent state machine; no profile/static parent map import."""
 result=[];section=cap=number=category=alpha_parent=None
 for sid,gs in ordered:
  text=expected_text(gs);x=next(g['bbox'][0] for g in gs if not g['text'].isspace());section_match=re.match(r'^(7\.36-[1-5])\s',text);marker=re.match(r'^([A-I]|[0-9]+|[a-k])\.\s',text);label=None
  if section_match:
   section=section_match.group(1);key=section;parent='document';kind='section';label=section;cap=number=category=alpha_parent=None;assert abs(x-90)<.2
  elif not result:assert text.startswith('Regulations for the Collection and Storage of Solid');key='document';parent=None;kind='document-title'
  elif section is None:
   if text=='2011':key='document.year';kind='front-matter'
   else:assert text.startswith('Pursuant to O.P.M.C. Chapter 7.36,');key='document.preamble';kind='preamble'
   parent='document'
  elif text in ['Residential Customers','Commercial Customers']:
   assert section=='7.36-3' and cap=='7.36-3.B' and abs(x-126)<.2;category=cap+'.'+text.split()[0];key=category;parent=cap;kind='subheading';number=alpha_parent=None
  elif marker:
   label=marker.group(1);kind='list-item'
   if label.isupper():assert abs(x-90)<.2;key=section+'.'+label;parent=section;cap=key;number=category=alpha_parent=None
   elif label.isdigit():assert abs(x-126)<.2;parent=category or cap;assert parent;key=parent+'.'+label;number=key;alpha_parent=key
   else:assert abs(x-162)<.2 and alpha_parent;parent=alpha_parent;key=parent+'.'+label
  elif text.startswith('The following '):assert abs(x-90)<.2;key=section+'.intro';parent=section;kind='paragraph'
  elif text.startswith('Vehicles of a Hauler’s subcontractor'):
   assert abs(x-162)<.2 and number=='7.36-1.B.6' and text.endswith('requirements:');parent=number;key=parent+'.paragraph';kind='paragraph';alpha_parent=key
  elif text.startswith('The written notice to customers required by this subsection B.'):
   assert cap=='7.36-3.B' and abs(x-126)<.2;parent=cap;key=parent+'.paragraph';kind='paragraph'
  else:raise AssertionError('Unexpected source paragraph/heading in dynamic hierarchy: '+sid)
  result.append({'source_tag_id':sid,'logical_key':key,'parent_id':uid(parent) if parent else None,'unit_type':kind,'source_label':label})
 assert len(result)==88 and len({r['logical_key'] for r in result})==88
 return result

def audit_inventory(data,folder,units,nodes):
 inv=json.loads((folder/'source-dependency-inventory.json').read_text());reader=PdfReader(io.BytesIO(data));assert inv['source_sha256']==PIN and inv['full_indirect_object_scan']
 forbidden={'m','l','c','v','y','h','re','S','s','f','F','f*','B','B*','b','b*','n','Do','BI','INLINE IMAGE','sh'}
 assert len(inv['pages'])==6
 for n,page in enumerate(reader.pages,1):
  ops=collections.Counter(op.decode('ascii') for _,op in ContentStream(page['/Contents'],reader).operations);actual=inv['pages'][n-1];assert actual['page']==n and actual['operators']==dict(ops);assert not set(ops)&forbidden and not actual['drawing_operators'];assert not page.get('/Annots') and not page['/Resources'].get('/XObject') and actual['annotations']==actual['resource_xobjects']==0
 for generation,entries in reader.xref.items():
  for number in entries:
   if number==0:continue
   obj=reader.get_object(IndirectObject(number,generation,reader))
   if isinstance(obj,dict):assert obj.get('/Type') not in ['/Filespec','/EmbeddedFile','/Annot','/Action'] and obj.get('/Subtype')!='/Image' and not set(obj)&{'/URI','/EF','/AF','/JavaScript','/JS','/EmbeddedFiles'}
 assert inv['xref_object_count']==sum(len(v) for v in reader.xref.values())-1 and inv['catalog_keys']==sorted(map(str,reader.root_object))
 assert not reader.root_object.get('/Names') and not reader.root_object.get('/AF') and inv['catalog_names']==inv['catalog_associated_files']==False
 assert not inv['embedded_or_annotation_or_URI_or_image_objects'];assert all(inv[k]==0 for k in ['embedded_files','annotations','hyperlinks','inline_images','image_xobjects'])
 assert inv['role_counts']==dict(collections.Counter(n['role'] for n in nodes)) and '/Table' not in inv['role_counts'] and '/Figure' not in inv['role_counts'];assert inv['table_disposition']['applicability']=='not-applicable'
 assert len(inv['textual_dependencies'])==2
 for dep in inv['textual_dependencies']:
  if dep['label']=='O.P.M.C. Chapter 7.36':matches=[u for u in units if re.search(r'O\.P\.M\.C\.\s+(?:Chapter|Section)\s+7\.36',u['text'])];assert dep['disposition']=='incorporated-by-reference' and any('are hereby incorporated by reference.' in u['text'] for u in matches)
  else:assert dep['label']=='County Solid Waste Regulations' and dep['disposition']=='referenced-regulations';matches=[u for u in units if 'County Solid Waste Regulations' in u['text']]
  assert [w['logical_owner_id'] for w in dep['witnesses']]==[u['id'] for u in matches]
  for w,u in zip(dep['witnesses'],matches):assert w=={'logical_owner_id':u['id'],'source_tag_id':u['source_tag_id'],'source_refs':u['source_refs'],'source_pages':u['source_pages'],'text':u['text'],'text_sha256':sha(u['text'].encode())}
  assert dep['source_url'] is None and dep['resolved_in_this_packet']==dep['edition_equivalence_qualified']==False
 assert inv['required_external_legal_dependencies_complete']==inv['edition_currentness_qualified']==inv['jurisdiction_complete']==False and inv['no_new_acquisition']==True and inv['image_policy']==POLICY
 return {'full6_content_operator_and_all_indirect_object_scan':True,'image_or_table_or_link_or_embedded_file_objects':0,'external_textual_dependencies':2,'external_dependencies_complete':False,'table_applicability':'not-applicable-source-proven','edition_currentness_qualified':False,'jurisdiction_complete':False}

def audit(data,folder):
 folder=pathlib.Path(folder);assert sha(data)==PIN;nodes,refs=original_tree(data);pages,native=original_glyphs(data);source=[g for p in pages for g in p];byid={g['glyph_id']:g for g in source};byref=collections.defaultdict(list)
 for g in source:
  if not g['source_artifact']:byref[(g['page'],g['source_mcid'])].append(g)
 out_glyphs=[json.loads(x) for x in (folder/'source-glyphs.jsonl').read_text().splitlines()];assert len(out_glyphs)==len(source)
 fields=['glyph_id','page','ordinal','text','cid','font','font_size','matrix','bbox','source_mcid','source_artifact']
 for expected,actual in zip(source,out_glyphs):assert all(expected[k]==actual[k] for k in fields),'Original glyph/CID/font/matrix ownership source differs'
 units=[json.loads(x) for x in (folder/'logical-units.jsonl').read_text().splitlines()];controls=[json.loads(x) for x in (folder/'source-controls.jsonl').read_text().splitlines()];ownrefs=collections.defaultdict(list)
 for r in refs:ownrefs[r['owner']].append(r)
 ordered=[];blanks=[]
 for n in nodes:
  if not ownrefs[n['id']]:continue
  gs=[g for r in ownrefs[n['id']] for g in byref[(r['page'],r['mcid'])]]
  if ''.join(g['text'] for g in gs).strip():ordered.append((n['id'],gs))
  else:blanks.append((n['id'],gs))
 expected=derive_hierarchy(ordered);assert len(units)==len(expected)==88;used=[]
 for unit,ref,(sid,gs) in zip(units,expected,ordered):
  for k,v in ref.items():assert unit[k]==v,'Logical source hierarchy/parent/order differs: '+sid+' '+k
  original_node=next(n for n in nodes if n['id']==sid);assert unit['source_tag_role']==original_node['role'] and unit['source_tag_parent_id']==original_node['parent'] and unit['source_order_path']==list(map(int,sid[4:].split('.'))),'Source tag hierarchy/path drift'
  assert unit['source_sha256']==PIN and unit['text_sha256']==sha(unit['text'].encode()),'Source/text hash drift'
  assert unit['id']==uid(ref['logical_key']) and unit['text']==expected_text(gs) and unit['raw_glyph_text']==''.join(g['text'] for g in gs),'Logical source text differs'
  assert unit['source_glyph_ids']==[g['glyph_id'] for g in gs] and unit['source_pages']==list(dict.fromkeys(g['page'] for g in gs)),'Unit glyph ownership/order/page continuation differs'
  assert unit['image_policy']==POLICY and unit['image_placeholders']==unit['tables']==[]
  assert [(r['page'],r['mcid']) for r in unit['source_refs']]==[(r['page'],r['mcid']) for r in ownrefs[sid]]
  used+=unit['source_glyph_ids'];lineglyphs=[]
  for line in unit['source_lines']:
   values=[byid[g] for g in line['source_glyph_ids']];assert values and len({g['page'] for g in values})==1 and max(g['matrix'][5] for g in values)-min(g['matrix'][5] for g in values)<=.25;assert line['raw_text']==''.join(g['text'] for g in values);lineglyphs+=line['source_glyph_ids']
  assert lineglyphs==unit['source_glyph_ids'],'Original linebreak/source glyph ledger differs'
 for name,rows in [('logical-units.csv',units),('source-controls.csv',controls)]:
  with (folder/name).open(newline='') as stream:csvrows=list(csv.DictReader(stream))
  assert len(csvrows)==len(rows),'CSV row omission/duplication'
  for c,r in zip(csvrows,rows):
   for k in ['id','unit_type','parent_id','source_label','text','source_tag_id','source_sha256']:assert c[k]==str(r.get(k) or ''),'CSV canonical field mismatch: '+k
   assert json.loads(c['source_pages'])==r.get('source_pages',[r.get('page')]),'CSV source page scope differs'
 assert len(controls)==26
 for c in controls:assert c['source_sha256']==PIN and c['source_pages']==list(dict.fromkeys(byid[g]['page'] for g in c['source_glyph_ids'])),'Control source binding drift'
 blank_by={c.get('source_tag_id'):c for c in controls if c['unit_type']=='blank-source-paragraph'}
 for sid,gs in blanks:
  c=blank_by[sid];assert c['source_glyph_ids']==[g['glyph_id'] for g in gs] and c['raw_glyph_text']==''.join(g['text'] for g in gs) and c['text']=='';used+=c['source_glyph_ids']
 for i,rows in enumerate(pages,1):
  gs=[g for g in rows if g['source_artifact']];c=next(c for c in controls if c['unit_type']=='native-Artifact-footer' and c['page']==i);assert c['source_glyph_ids']==[g['glyph_id'] for g in gs] and c['raw_glyph_text']==''.join(g['text'] for g in gs);assert c['text']==f'7/21/2011 7-21-11 AM  Page {i}';used+=c['source_glyph_ids']
 assert len(used)==len(set(used))==len(source) and set(used)==set(byid),'Source glyph omission/duplication'
 words=[json.loads(x) for x in (folder/'source-words.jsonl').read_text().splitlines()];wordglyphs=[];owners={g:unit['id'] for unit in units+controls for g in unit['source_glyph_ids']}
 for w in words:
  gs=[byid[g] for g in w['source_glyph_ids']];assert gs and all(not g['text'].isspace() for g in gs);assert len({g['page'] for g in gs})==1 and max(g['matrix'][5] for g in gs)-min(g['matrix'][5] for g in gs)<=.25;assert w['text']==''.join(g['text'] for g in gs) and all(owners[g['glyph_id']]==w['logical_owner_id'] for g in gs);wordglyphs+=w['source_glyph_ids']
 for u in units:assert u['source_word_ids']==[w['word_id'] for w in words if w['logical_owner_id']==u['id']],'Canonical unit word-ownership index differs'
 expected_wordglyphs={g['glyph_id'] for g in source if not g['text'].isspace()};assert len(wordglyphs)==len(set(wordglyphs)) and set(wordglyphs)==expected_wordglyphs,'Source word character omission/duplication'
 inventory=audit_inventory(data,folder,units,nodes)
 return {'source_dependency_and_table_applicability':inventory,'canonical_csv_agrees':True,'passed':True,'scope':'Whole exact native6-page source; independent source tree, dynamic text/indent hierarchy, low-level glyph/CID/font/matrix stream, MuPDF rawglyph and ownership/line/word audit','source_sha256':PIN,'pages':6,'source_nodes':len(nodes),'content_refs':len(refs),'logical_units':len(units),'controls':len(controls),'source_glyphs':len(source),'nonwhite_glyphs':len(expected_wordglyphs),'words':len(words),'sections':[r['logical_key'] for r in expected if r['unit_type']=='section'],'full_hierarchy_agrees':True,'raw_lines_and_source_word_characters_complete':True,'native_independent':native,'image_policy':POLICY,'images':0,'tables':0,'image_fetch_decode_extract_render_OCR':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--pdf',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
 try:result=audit(a.pdf.read_bytes(),a.out)
 except Exception as e:print(json.dumps({'passed':False,'error':type(e).__name__+': '+str(e)},indent=2));sys.exit(2)
 print(json.dumps(result,indent=2))
