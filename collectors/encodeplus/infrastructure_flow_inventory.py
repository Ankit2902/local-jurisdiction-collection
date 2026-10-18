"""Pure exhaustive native source-fragment inventory; no file/native/transport I/O."""
import collections,hashlib,json,re
canon=lambda v:json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()

def marker(text):
 for pattern,kind in [(r'^([a-z])([.)])\s','ordered_letter'),(r'^(\d+)(\.)\s','ordered_decimal'),(r'^([●○▸•▪◦])\s','literal_bullet'),(r'^\(([^)]+)\)\s','parenthesized_candidate')]:
  m=re.match(pattern,text)
  if m:return {'kind':kind,'literal':m[0].rstrip(),'value':m[1],'delimiter':m[2]if len(m.groups())>1 else None}
 return None

def inventory(records):
 assert len(records)==172 and all(r['raw_sha256']=='915fe1fdf8ff5da33acfce7d08637808cb57886fbbc7f157b2b81bfcf970827c'for r in records)
 fragments=[];units=[];transitions=[];roles=collections.Counter();words=[];markers=[];control_text=collections.Counter()
 for r in records:
  a=r.get('source_outline');headcount=a['blocks']if a else 0;uf=[];prior=None
  for i,f in enumerate(r['source_fragments']):
   b=f['block'];t=b.get('text','');m=marker(t);role='running_page_control'if f['page_control']else 'source_heading'if i<headcount else 'image_placeholder'if b['kind']=='image_placeholder'else 'printed_grid'if b['kind']=='table'else 'source_cover_line'if r['unit_type']=='frontmatter'else 'contents_line'if r['unit_type']=='table-of-contents'else 'body_text_line'
   ident=r['id']+'::source:'+str(f['page'])+':'+str(f['block_index']);item={'id':ident,'unit_id':r['id'],'unit_heading':r['heading'],'page':f['page'],'block_index':f['block_index'],'role':role,'text':t,'bbox':b['bbox'],'kind':b['kind'],'marker_candidate':m if role=='body_text_line'else None,'word_ids':b.get('word_ids',[]),'source_fragment_sha256':hashlib.sha256(canon(f)).hexdigest()};uf.append(item);fragments.append(item);roles[role]+=1;words.extend(item['word_ids'])
   if role=='running_page_control':control_text[t]+=1
   if role=='body_text_line'and m:markers.append(item)
   if prior is not None:
    transitions.append({'unit_id':r['id'],'before_id':prior['id'],'after_id':ident,'before_role':prior['role'],'after_role':role,'page_break':prior['page']!=f['page'],'x_delta':b['bbox'][0]-prior['bbox'][0],'vertical_start_delta':b['bbox'][1]-prior['bbox'][1]if prior['page']==f['page']else None,'before_text':prior['text'],'after_text':t})
   prior=item
  units.append({'id':r['id'],'heading':r['heading'],'unit_type':r['unit_type'],'source_pages':r['source_pages'],'fragments':len(uf),'roles':dict(collections.Counter(f['role']for f in uf)),'source_record_sha256':hashlib.sha256(canon(r)).hexdigest()})
 assert len(fragments)==1776 and len(words)==len(set(words))==18662 and roles['running_page_control']==142
 return {'schema_version':1,'source_units':172,'source_pages':62,'source_fragments':1776,'unique_source_words':18662,'cross_page_units':sum(len(r['source_pages'])>1 for r in records),'fragment_roles':dict(roles),'marker_candidate_counts':dict(collections.Counter(m['marker_candidate']['kind']for m in markers)),'units':units,'fragments':fragments,'transitions':transitions,'marker_candidates':markers,'running_controls':dict(control_text),'scope':'Exhaustive source-role inventory, not automatic list/paragraph legal qualification; parenthesized candidates include phone/acronym/measurement continuations and must not become list items.'}
