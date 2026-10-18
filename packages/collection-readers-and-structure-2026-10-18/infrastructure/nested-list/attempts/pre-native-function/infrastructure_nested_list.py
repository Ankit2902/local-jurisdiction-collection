"""Finite source-supported §5.3 list projection. No generalized indent/intent waiver."""
import copy,csv,hashlib,html,io,json
SHA='915fe1fdf8ff5da33acfce7d08637808cb57886fbbc7f157b2b81bfcf970827c'
DOC='82-0c6b3dc40877'
ID=DOC+'::printed-unit:54'
URL='https://online.encodeplus.com/regs/overlandpark-ks/doclibrary.aspx?id=3e3d98cc-890e-4630-9c2b-8f84375b0c67'
PROFILE='infrastructure-5-3-printed-nested-list-v1'
FRAGMENTS='ecf486499263aef952fce19f8a94661e0173da503d51fb5a34eb47b5deb56c01'
WITNESS='2501d22a32e27da8f5a7de91968c635105879de4bc710afbd5e7ecabef5d812a'

def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def leaf(f):return {'source_page':f['page'],'source_block_index':f['block_index'],'block':copy.deepcopy(f['block'])}
def own_text(item):return '\n'.join(x['block']['text'] for x in item['own_fragments'])
def item_text(item):return '\n'.join([own_text(item)]+[item_text(c) for c in item['children']])
def source_leaves(item):return item['own_fragments']+[f for c in item['children'] for f in source_leaves(c)]
def render_items(items,ordered):
 tag='ol' if ordered else 'ul';out=['<'+tag+' style="list-style-type:none" data-source-markers="literal">']
 for item in items:
  out.append('<li data-source-id="'+html.escape(item['id'],quote=True)+'"><span class="source-item-text">'+html.escape(own_text(item))+'</span>')
  if item['children']:out.append(render_items(item['children'],False))
  out.append('</li>')
 out.append('</'+tag+'>');return ''.join(out)

def project(record,witness):
 if record.get('id')!=ID:return copy.deepcopy(record)
 # Exact source/owner/native glyph binding, before any mutation. No nearest text/indent fallback.
 assert record.get('document_id')==DOC and record.get('raw_sha256')==SHA and record.get('source_document_url')==URL
 assert record.get('heading')=='5.3. Utility Potholes' and record.get('source_pages')==[26] and record.get('raw_ref')=='raw/start.pdf'
 assert record.get('publication')=='Manual of Infrastructure Standards' and record.get('jurisdiction')=='Overland Park, Kansas' and record.get('state')=='KS'
 fs=record['source_fragments'];assert digest(fs)==FRAGMENTS,'Exact source fragments/words/geometry differ'
 assert digest(witness)==WITNESS,'Bounded native text/glyph witness differs'
 assert witness['source_sha256']==SHA and witness['record_id']==ID and witness['physical_page']==26 and witness['native_text_only'] is True and witness['image_operations']==0
 assert record['ordered_blocks']==[f['block'] for f in fs] and record['text']=='\n'.join(f['block']['text'] for f in fs) and record['tables']==[]
 assert [f['block_index'] for f in fs]==list(range(9,19)) and all(f['page']==26 for f in fs)
 for f,g in zip(fs,witness['blocks']):
  assert g['page']==f['page'] and g['block_index']==f['block_index'] and g['bbox']==f['block']['bbox'] and g['text']==f['block']['text']
  assert ''.join(''.join(c['text'] for c in g['glyphs']).split())==''.join(g['text'].split())
  if g['text'].startswith('▸'):
   assert g['glyphs'][0]['text']=='▸' and g['glyphs'][0]['fontname']=='DAAAAA+MS-PGothic'
 parents=[];current=None
 for f in fs[3:]:
  text=f['block']['text'];x=f['block']['bbox'][0]
  if text[:2] in ('a)','b)'):
   assert x==108 and text[2]==' ' and text[0]==chr(ord('a')+len(parents))
   current={'id':ID+'::list:0::item:'+text[0],'printed_marker':text[:2],'own_fragments':[leaf(f)],'children':[]};parents.append(current)
  elif text.startswith('▸ '):
   assert current is not None and x==126 and own_text(current).endswith(':')
   current['children'].append({'id':current['id']+'::bullet:'+str(len(current['children'])),'printed_marker':'▸','own_fragments':[leaf(f)],'children':[]})
  else:
   # Actual b) wrapping is same indent as bullets; only literal marked text creates a child.
   assert current and not current['children'] and x==126
   current['own_fragments'].append(leaf(f))
 assert len(parents)==2 and [len(p['children']) for p in parents]==[2,2]
 assert fs[2]['block']['text']=='noted below or as necessary to protect existing utilities.'
 leaves=[f for p in parents for f in source_leaves(p)]
 assert [(f['source_page'],f['source_block_index']) for f in leaves]==[(f['page'],f['block_index']) for f in fs[3:]]
 words=[w for f in leaves for w in f['block']['word_ids']];assert len(words)==len(set(words))
 text='\n'.join(item_text(p) for p in parents)
 assert text=='\n'.join(f['block']['text'] for f in fs[3:])
 result=copy.deepcopy(record)
 result['superseded_flat_list_diagnostics']={'schema_version':1,'profile':PROFILE,'source_sha256':SHA,'source_url':URL,'physical_page':26,'original_fields':{k:copy.deepcopy(record[k]) for k in ['text','ordered_blocks','qualification','canonical_structure_selection']}}
 listblock={'id':ID+'::list:0','kind':'nested_list','ordered':True,'marker_encoding':'literal_source_characters','items':parents,'text':text,'word_ids':words,'bbox':[108.0,fs[3]['block']['bbox'][1],max(f['block']['bbox'][2] for f in fs[3:]),fs[-1]['block']['bbox'][3]],'source_page':26,'source_block_indices':[f['block_index'] for f in fs[3:]],'source_nested_list_qualified':True}
 result['ordered_blocks']=copy.deepcopy(record['ordered_blocks'][:3])+[listblock]
 assert '\n'.join(b['text'] for b in result['ordered_blocks'])==record['text']
 result['html']='<section data-source-profile="'+PROFILE+'"><h2>'+html.escape(fs[0]['block']['text'])+'</h2><p>'+html.escape('\n'.join(f['block']['text'] for f in fs[1:3]))+'</p>'+render_items(parents,True)+'</section>'
 result['source_nested_list_evidence']={'profile':PROFILE,'source_sha256':SHA,'source_url':URL,'physical_page':26,'record_id':ID,'source_fragments_sha256':FRAGMENTS,'native_glyph_witness_sha256':WITNESS,'native_text_glyphs':sum(len(x['glyphs']) for x in witness['blocks']),'outer_items':2,'child_items':4,'levels':2,'word_ids_once':True,'body_marker_basis':'literal a)/b) then U+25B8 MS-PGothic glyphs; colon lead-ins; x108/x126 source geometry; hanging unmarked b) line retained as its own text','qualification_scope':'Only exact §5.3 printed two-level list; source has no semantic tags. No generalized numbering/indent inference. No adoption/dependency/whole-publication lift.'}
 result['qualification']['selected_printed_nested_list_hierarchy_qualified']=True
 result['qualification']['nested_list_hierarchy_qualified']=True
 result['qualification']['paragraph_continuation_semantics_qualified']=False
 result['qualification']['whole_publication_complete']=False
 result['canonical_structure_selection']['selected_nested_list_profile']=PROFILE
 result['canonical_structure_selection']['scope']+=' Exact §5.3 printed list canonicalized; whole-document list/paragraph/reading-order qualification remains false.'
 result['canonical_structure_selection']['authoritative_fields']=list(dict.fromkeys(result['canonical_structure_selection']['authoritative_fields']+['html']))
 return result

def outputs(records):
 buf=io.StringIO(newline='');fields=['id','document_id','unit','unit_type','heading','source_pages','text','html'];w=csv.DictWriter(buf,fields);w.writeheader()
 for r in records:w.writerow({k:json.dumps(r[k]) if k=='source_pages' else r.get(k,'') for k in fields})
 return {'records.jsonl':''.join(json.dumps(r,sort_keys=True,ensure_ascii=False)+'\n' for r in records).encode(),'records.csv':buf.getvalue().encode()}
