#!/usr/bin/env python3
"""Exact-source full-publication logical export; original glyphs/roles/order retained."""
import argparse,collections,csv,hashlib,io,json,pathlib,re,sys
from pypdf import PdfReader
import pdf_glyphs,pdf_tags,profile

def sha(data):return hashlib.sha256(data).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def source_id(key):return profile.PUBLICATION+'::'+key

def shaped(glyphs):
 parts=[];inferences=[];previous=None
 for g in glyphs:
  value=g['text']
  if previous is not None and parts and not parts[-1].endswith(tuple(' \t\n\r')) and value and not value[0].isspace():
   dy=abs(g['matrix'][5]-previous['matrix'][5]);dx=g['bbox'][0]-previous['bbox'][2];size=max(g['font_size'],previous['font_size'],1)
   if g['page']!=previous['page'] or dy>size*.5:parts.append('\n');inferences.append({'kind':'line-or-page','before':g['glyph_id'],'after':previous['glyph_id'],'separator':'\n'})
   elif dx>size*.2:parts.append(' ');inferences.append({'kind':'word-gap','before':g['glyph_id'],'after':previous['glyph_id'],'separator':' '})
  parts.append(value);previous=g
 return ''.join(parts),inferences

def lines_and_words(glyphs):
 lines=[];words=[];current=[]
 def finish():
  if not current:return
  lineid='line:'+current[0]['glyph_id'];line={'line_id':lineid,'page':current[0]['page'],'source_glyph_ids':[g['glyph_id'] for g in current],'raw_text':''.join(g['text'] for g in current),'baseline':current[0]['matrix'][5],'bbox':[min(g['bbox'][0] for g in current),min(g['bbox'][1] for g in current),max(g['bbox'][2] for g in current),max(g['bbox'][3] for g in current)],'text_is_derived_source_view':True};lines.append(line);word=[]
  def finish_word():
   if not word:return
   words.append({'word_id':'word:'+word[0]['glyph_id'],'page':word[0]['page'],'line_id':lineid,'source_glyph_ids':[g['glyph_id'] for g in word],'text':''.join(g['text'] for g in word),'bbox':[min(g['bbox'][0] for g in word),min(g['bbox'][1] for g in word),max(g['bbox'][2] for g in word),max(g['bbox'][3] for g in word)],'fonts':sorted({g['font'] for g in word}),'cids':[g['cid'] for g in word],'text_is_derived_source_view':True});word.clear()
  for g in current:
   if g['text'].isspace():finish_word();continue
   if word and g['bbox'][0]-word[-1]['bbox'][2]>max(g['font_size'],word[-1]['font_size'])*.2:finish_word()
   word.append(g)
  finish_word();current.clear()
 for g in glyphs:
  if current and (g['page']!=current[-1]['page'] or abs(g['matrix'][5]-current[-1]['matrix'][5])>.25):finish()
  current.append(g)
 finish();return lines,words

def build(data):
 assert sha(data)==profile.SOURCE_SHA256,'Unqualified source SHA; refuse semantic profile on another edition/file'
 reader=PdfReader(io.BytesIO(data));assert len(reader.pages)==6 and '/StructTreeRoot' in reader.root_object
 for page in reader.pages:assert list(map(float,page.mediabox))==[0,0,612,792] and not page['/Resources'].get('/XObject'),'Unexpected page/image source profile'
 tagged=pdf_tags.parse(data);assert tagged and tagged['qualification']['source_structure_supported'];q=tagged['qualification'];assert q['source_node_count']==191 and q['source_reference_count']==109 and q['source_table_count']==q['source_figure_placeholders']==q['actual_text_variant_count']==0
 pages=pdf_glyphs.extract(data);assert len(pages)==6 and sum(len(p['glyphs']) for p in pages)==15574
 glyphs={g['glyph_id']:g for p in pages for g in p['glyphs']};byref=collections.defaultdict(list);artifacts=collections.defaultdict(list)
 for page in pages:
  for g in page['glyphs']:
   if g['source_artifact']:artifacts[page['page']].append(g)
   else:assert g['source_mcid'] is not None;byref[(g['page'],g['source_mcid'])].append(g)
 inv=tagged['source_inventory'];nodes={n['source_id']:n for n in inv['nodes']};refs=collections.defaultdict(list)
 for ref in inv['references']:refs[ref['owner_id']].append(ref)
 assert set(byref)=={(r['page'],r['mcid']) for r in inv['references']}
 bindings={r['source_tag_id']:r for r in profile.bindings()};units=[];controls=[];words=[];used=[]
 for node in inv['nodes']:
  own=refs[node['source_id']]
  if not own:continue
  assert node['role'] in ['/P','/LBody'];gs=[g for r in own for g in byref[(r['page'],r['mcid'])]];raw=''.join(g['text'] for g in gs);text,inferences=shaped(gs);text=text.strip();line_rows,word_rows=lines_and_words(gs);used.extend(g['glyph_id'] for g in gs)
  if not text:
   assert node['source_id'] not in bindings and node['role']=='/P';control={'id':source_id('control:'+node['source_id']),'unit_type':'blank-source-paragraph','source_tag_id':node['source_id'],'text':'','raw_glyph_text':raw,'source_glyph_ids':[g['glyph_id'] for g in gs],'source_refs':own,'source_lines':line_rows,'source_order_path':node['index_path'],'image_policy':profile.IMAGE_POLICY};controls.append(control);continue
  assert node['source_id'] in bindings,'Unexpected nonempty source content owner';binding=bindings[node['source_id']];first=next(g for g in gs if not g['text'].isspace());assert abs(first['bbox'][0]-binding['first_glyph_x'])<.2 and abs(first['font_size']-binding['first_glyph_size'])<1e-5,'Source geometry/font-size binding failed'
  assert text.startswith(binding['text_prefix']),'Source label/heading binding failed: '+binding['key']
  if binding['bold_nonspace']:assert {g['font'] for g in gs if not g['text'].isspace()}=={'TimesNewRomanPS-BoldMT'},'Source heading/subheading bold font differs'
  unit={'id':source_id(binding['key']),'document_id':source_id(binding['key']),'publication_id':profile.PUBLICATION,'jurisdiction':'Overland Park, Kansas','state':'KS','publication':'Administrative Regulations - Collection & Storage of Solid Waste & Recyclables','unit_type':binding['unit_type'],'source_label':binding['source_label'],'parent_id':source_id(binding['parent_key']) if binding['parent_key'] else None,'logical_key':binding['key'],'text':text,'raw_glyph_text':raw,'source_tag_id':node['source_id'],'source_tag_role':node['role'],'source_tag_parent_id':node['parent_id'],'source_order_path':node['index_path'],'source_refs':own,'source_pages':list(dict.fromkeys(g['page'] for g in gs)),'source_glyph_ids':[g['glyph_id'] for g in gs],'source_word_ids':[w['word_id'] for w in word_rows],'source_lines':line_rows,'separator_inferences':inferences,'text_sha256':sha(text.encode()),'source_sha256':sha(data),'source_url':profile.SOURCE_URL,'image_policy':profile.IMAGE_POLICY,'image_placeholders':[],'tables':[],'logical_profile':'overland-solid-waste-2011-source-pinned-v1','source_binding':{'first_glyph_id':first['glyph_id'],'x':first['bbox'][0],'font':first['font'],'font_size':first['font_size'],'source_prefix':binding['text_prefix'],'basis':'Exact native source hash + original StructTreeRoot content ownership/order + printed labels/font/position source-specific hierarchy.'}}
  for w in word_rows:w['logical_owner_id']=unit['id']
  words.extend(word_rows);units.append(unit)
 assert len(units)==len(bindings)==88 and {r['source_tag_id'] for r in units}==set(bindings)
 for page in pages:
  gs=artifacts[page['page']];assert gs;raw=''.join(g['text'] for g in gs);assert raw==f'7/21/2011 7-21-11 AM  Page {page["page"]} ';line_rows,word_rows=lines_and_words(gs);control={'id':source_id('footer:'+str(page['page'])),'unit_type':'native-Artifact-footer','page':page['page'],'text':raw.strip(),'raw_glyph_text':raw,'source_glyph_ids':[g['glyph_id'] for g in gs],'source_lines':line_rows,'image_policy':profile.IMAGE_POLICY};controls.append(control);used.extend(g['glyph_id'] for g in gs)
  for w in word_rows:w['logical_owner_id']=control['id']
  words.extend(word_rows)
 assert len(controls)==26 and len(used)==len(set(used))==len(glyphs) and set(used)==set(glyphs),'Glyph omission/duplication'
 bykey={u['logical_key']:u for u in units};assert len(bykey)==len(units)
 for u in units:
  if u['parent_id']:assert u['parent_id'] in {v['id'] for v in units}
  if u['source_label'] and u['unit_type']=='list-item':assert re.match(re.escape(u['source_label'])+r'\.\s',u['text'])
 assert [u['logical_key'] for u in units if u['unit_type']=='section']==['7.36-1','7.36-2','7.36-3','7.36-4','7.36-5']
 assert bykey['7.36-5.D']['source_pages']==[5,6] and len(bykey['7.36-5.D']['source_refs'])==2
 assert 'behind the existing building line' in bykey['7.36-5.D']['text'] and 'rights-of-\nway.' in bykey['7.36-5.G']['text']
 return {'units':units,'controls':controls,'glyph_pages':pages,'words':words,'tagged':tagged,'profile_bindings':profile.bindings(),'qualification':{'scope':'Only exact source pinned full6-page native document, logical units and controls separated','source_sha256':sha(data),'pages':6,'logical_units':88,'source_controls':26,'glyphs':15574,'source_content_refs':109,'sections':5,'tables':0,'images':0,'source_glyph_ownership_complete':True,'image_policy':profile.IMAGE_POLICY,'source_specific_logical_profile':True,'new_acquisition':False,'jurisdiction_complete':False}}

def write(data,out):
 out=pathlib.Path(out);assert not out.exists(),'Fresh output required';result=build(data);out.mkdir(parents=True)
 def jsonl(name,rows):(out/name).write_bytes(b''.join(canonical(r)+b'\n' for r in rows))
 jsonl('logical-units.jsonl',result['units']);jsonl('source-controls.jsonl',result['controls']);jsonl('source-words.jsonl',result['words']);jsonl('source-glyphs.jsonl',[g for p in result['glyph_pages'] for g in p['glyphs']])
 for filename,rows in [('logical-units.csv',result['units']),('source-controls.csv',result['controls'])]:
  fields=['id','unit_type','parent_id','source_label','text','source_tag_id','source_pages','source_sha256'];stream=io.StringIO(newline='');w=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows({**r,'source_pages':json.dumps(r.get('source_pages',[r.get('page')]))} for r in rows);(out/filename).write_text(stream.getvalue(),newline='')
 for filename,value in [('source-tags.json',result['tagged']['source_inventory']),('source-profile-bindings.json',result['profile_bindings']),('qualification.json',result['qualification'])]:(out/filename).write_bytes(canonical(value)+b'\n')
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--pdf',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();r=write(a.pdf.read_bytes(),a.out);print(json.dumps(r['qualification'],indent=2))
