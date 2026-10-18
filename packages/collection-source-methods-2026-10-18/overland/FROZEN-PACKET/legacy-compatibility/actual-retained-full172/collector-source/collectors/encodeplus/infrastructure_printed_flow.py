"""Whole retained-source printed structure projection. No legal intent inference."""
import collections,copy,csv,hashlib,html,io,json,re
from pathlib import Path
from .infrastructure_flow_inventory import inventory,marker,canon
PROFILE='infrastructure-exhaustive-printed-flow-v1'
SHA='915fe1fdf8ff5da33acfce7d08637808cb57886fbbc7f157b2b81bfcf970827c'
SOURCE_RECORDS='8bf0cf6e1d319d900fbdafff16dd8f051e945f39a6102aaad035fe3a4001afe9'
GEOMETRY_SHA='ce34644c285715bfb453e40b0431413bb10fa29287cac362cee7fd9c3bc4b732'
GEOMETRY_NAME='infrastructure-multiline-native-geometry.json'

def load_geometry():
 data=(Path(__file__).resolve().parent/GEOMETRY_NAME).read_bytes()
 assert hashlib.sha256(data).hexdigest()==GEOMETRY_SHA,'Source-bound native line geometry corrupt/wrong revision'
 d=json.loads(data)
 assert d['source_sha256']==SHA and d['target_pages']==[11,12,13,14] and d['target_fragments']==9 and d['physical_lines']==68
 assert d['all_source_word_ID_counters_equal'] and d['all_source_word_ID_sequences_equal'] and d['all_source_nonwhitespace_order_equal'] and d['independent_native_line_queries']==d['independent_native_line_queries_agree']==68 and d['forbidden_image_or_network_calls']==[]
 return {f['source_fragment']:f for f in d['fragments']}

def qualify_source_lines(fragment,witness):
 assert witness['source_fragment']==fragment['id'] and witness['page']==fragment['page'] and witness['block_index']==fragment['block_index'] and witness['source_bbox']==fragment['bbox']
 assert witness['original_source_text']==fragment['text'] and witness['original_word_ids']==fragment['word_ids']
 lines=copy.deepcopy(witness['lines']);original=fragment['text'].split('\n');assert len(lines)==len(original)
 assert [w['id']for line in lines for w in line['words']]==fragment['word_ids']
 groups=[]
 for i,(line,literal)in enumerate(zip(lines,original)):
  assert line['independent_nonwhitespace_order_equal'] is True and ''.join(line['text'].split())==''.join(literal.split())
  line['canonical_text']=literal;line['source_line_id']=fragment['id']+'::line:'+str(i)
  prev=groups[-1][-1]if groups else None
  if prev is None or abs(line['bbox'][0]-prev['bbox'][0])>.6 or line['bbox'][1]-prev['bbox'][1]>1.6*max(line['bbox'][3]-line['bbox'][1],prev['bbox'][3]-prev['bbox'][1]):groups.append([])
  groups[-1].append(line)
 return groups

def walk(n):
 if n['kind']=='source_leaf':yield n
 else:
  for c in n.get('children',[]):yield from walk(c)
def text(n):return '\n'.join(x['text']for x in walk(n))
def last_leaf(n):return list(walk(n))[-1]if list(walk(n))else None

def table_html(table):
 out=['<table data-source-role="printed-stroked-grid" data-header-meaning-qualified="false">'];cells=table['cells'];assert cells
 for row in sorted({c['row']for c in cells}):
  out.append('<tr>')
  for c in sorted([c for c in cells if c['row']==row],key=lambda c:c['column']):
   out.append('<td data-source-cell="'+html.escape(c['id'],quote=True)+'" rowspan="'+str(c['rowspan'])+'" colspan="'+str(c['colspan'])+'">'+html.escape(c['text'])+'</td>')
  out.append('</tr>')
 return ''.join(out)+'</table>'

def render(n):
 kind=n['kind']
 if kind=='source_leaf':
  attrs=' data-source-fragment="'+html.escape(n['id'],quote=True)+'" data-source-page="'+str(n['page'])+'"'
  if n.get('source_line_groups'):
   groups=['<p data-source-role="native-geometry-paragraph-group">'+'\n'.join('<span data-source-line="'+html.escape(line['source_line_id'],quote=True)+'">'+html.escape(line['canonical_text'])+'</span>'for line in group)+'</p>'for group in n['source_line_groups']]
   return '<div'+attrs+'>'+'\n'.join(groups)+'</div>'
  if n['role']=='printed_grid':return '<div'+attrs+'>'+table_html(n['table'])+'</div>'
  return '<span'+attrs+'>'+html.escape(n['text'])+'</span>'
 inside='\n'.join(render(c)for c in n['children'])
 if kind=='source_list':return '<'+n['html_tag']+' data-source-list="'+html.escape(n['id'],quote=True)+'" style="list-style-type:none">'+inside+'</'+n['html_tag']+'>'
 tag={'source_unit':'section','source_heading':'h2','printed_paragraph':'p','source_item':'li','running_page_control':'aside','contents_line':'div','image_placeholder':'div','printed_grid':'div','source_cover_line':'div','source_multiline_prose':'div'}[kind]
 return '<'+tag+' data-source-role="'+kind+'">'+inside+'</'+tag+'>'

def parenthetical_disposition(before,current,candidate):
 """Recognize only source-explicit wrapped prose, not arbitrary parenthesized labels."""
 if not before or before['page']!=current['page'] or before['role']!='body_text_line':return None
 if before['id'].split('::source:')[0]!=current['id'].split('::source:')[0]:return None
 xdelta=current['bbox'][0]-before['bbox'][0];dy=current['bbox'][1]-before['bbox'][1];height=max(before['bbox'][3]-before['bbox'][1],current['bbox'][3]-current['bbox'][1])
 if not (0<dy<=height*1.6 and -.6<=xdelta<=18.6):return None
 value=candidate['value'];text=current['text'];previous=before['text'].rstrip();reason=None;basis=None
 if re.match(r'^\(\d{3}\)\s*\d{3}\s*-\s*\d{4}\.?$',text):reason='wrapped_telephone_number';basis='Literal (three digits) three digits-hyphen-four digits plus adjacent same-paragraph geometry'
 elif value.isdigit() and re.match(r'^\(\d+\)\s+inches\b',text):
  ones=['zero','one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen'];tens=['','','twenty','thirty','forty','fifty','sixty','seventy','eighty','ninety'];n=int(value)
  spelled=ones[n]if n<20 else tens[n//10]+('-'+ones[n%10]if n%10 else'')if n<100 else None
  if spelled and re.search(r'\b'+re.escape(spelled)+r'$',previous,re.I):reason='wrapped_repeated_measurement';basis='Previous physical line ends exact spelled number; following line repeats same numeral in parentheses followed by inches'
 elif value.isupper() and value.isalpha() and len(value)>1:
  words=re.findall(r'[A-Za-z]+',previous)
  if len(words)>=len(value) and ''.join(w[0].upper()for w in words[-len(value):])==value:reason='wrapped_explicit_acronym';basis='Previous physical line ends exact words whose first letters equal the literal parenthesized acronym'
 elif re.search(r'\s',value):reason='wrapped_parenthetical_prose';basis='Multiword parenthetical at adjacent continuation geometry; not a single printed alphanumeric item label'
 if not reason:return None
 return {'kind':reason,'source_fragment':current['id'],'previous_fragment':before['id'],'literal':candidate['literal'],'source_based_nonlist_disposition':True,'basis':basis,'previous_text':previous,'text':text,'previous_bbox':before['bbox'],'bbox':current['bbox'],'previous_fragment_sha256':hashlib.sha256(canon(before)).hexdigest(),'current_fragment_sha256':hashlib.sha256(canon(current)).hexdigest(),'text_modified':False}

def project_record(record,fragments,geometry=None):
 geometry=load_geometry()if geometry is None else geometry
 r=copy.deepcopy(record);tree={'kind':'source_unit','id':r['id'],'children':[]};frames=[];unresolved=[];listnodes=[];paragraphs=[];nonlists=[];last_semantic=None
 tables={t['id']:t for t in record['tables']}
 def leaf(f):
  x={k:copy.deepcopy(f[k])for k in ['id','role','text','page','block_index','bbox','word_ids']};x['kind']='source_leaf'
  if f['role']=='printed_grid':
   original=next(z['block']for z in record['source_fragments']if z['page']==f['page']and z['block_index']==f['block_index']);t=tables[original['id']];assert ''.join(''.join(c['text']for c in t['cells']).split())==''.join(f['text'].split()),'Source grid nonwhitespace character sequence differs from owned block text';assert [w for c in t['cells']for w in c['word_ids']]==f['word_ids'];x['table']=copy.deepcopy(t);x['table_text_policy']='Exact retained bounded cell text/spans in HTML; original whole-word block text retained verbatim. Native linebreak/superscript spacing differs explicitly, not corrected.'
  if f['id']in geometry:x['source_line_groups']=qualify_source_lines(f,geometry[f['id']])
  return x
 def append_role(f):
  nonlocal last_semantic
  frames.clear()
  if f['role']=='source_heading' and tree['children'] and tree['children'][-1]['kind']=='source_heading':tree['children'][-1]['children'].append(leaf(f))
  else:
   node={'kind':f['role'],'id':f['id']+'::role','children':[leaf(f)]};tree['children'].append(node)
  if f['role']not in ['running_page_control']:last_semantic=leaf(f)
 def para(parent,f,hanging=False):
  nonlocal last_semantic
  x=leaf(f)
  if x.get('source_line_groups'):
   if last_semantic and last_semantic['page']!=f['page']:unresolved.append({'kind':'cross_page_paragraph_boundary','before':last_semantic['id'],'after':f['id'],'qualification':False,'reason':'Source line geometry does not establish semantic continuation across the physical page break'})
   parent['children'].append({'kind':'source_multiline_prose','id':f['id']+'::native-prose','children':[x]});paragraphs.extend({'id':f['id']+'::native-paragraph:'+str(i)}for i in range(len(x['source_line_groups'])));last_semantic=x;return
  prev=parent['children'][-1]if parent['children']else None;old=last_leaf(prev)if prev else None
  join=bool(prev and prev['kind']=='printed_paragraph'and old and old['page']==f['page']and 0<=f['bbox'][1]-old['bbox'][1]<=max(1,f['bbox'][3]-f['bbox'][1],old['bbox'][3]-old['bbox'][1])*1.6 and (abs(f['bbox'][0]-old['bbox'][0])<=.6 or hanging))
  if not join:
   node={'kind':'printed_paragraph','id':f['id']+'::paragraph','children':[],'grouping_basis':'Literal line geometry only; not a legal paragraph-intent claim'};parent['children'].append(node);paragraphs.append(node);prev=node
   if last_semantic and last_semantic['page']!=f['page']:
    unresolved.append({'kind':'cross_page_paragraph_boundary','before':last_semantic['id'],'after':f['id'],'qualification':False,'reason':'No semantic tags/paragraph controls retained; no merger inferred from text or indentation alone'})
  prev['children'].append(x);last_semantic=x
  if '\n'in f['text']:unresolved.append({'kind':'multi_line_fragment_geometry','source_fragment':f['id'],'lines':len(f['text'].split('\n')),'qualification':False,'reason':'One cached bounding box covers multiple source lines; per-line printed paragraph geometry is not supplied'})
 for f in fragments:
  role=f['role'];m=f['marker_candidate']
  if role=='running_page_control':
   parent=frames[-1]['item']if frames else tree;parent['children'].append({'kind':role,'id':f['id']+'::role','children':[leaf(f)]});continue
  if role!='body_text_line':append_role(f);continue
  x=f['bbox'][0]
  if m and m['kind']!='parenthesized_candidate':
   family=(m['kind'],m['delimiter'] if m['kind']!='literal_bullet'else m['value']);value=(ord(m['value'])-ord('a')+1)if m['kind']=='ordered_letter'else int(m['value'])if m['kind']=='ordered_decimal'else None
   while frames and x<frames[-1]['indent']-.6:frames.pop()
   frame=frames[-1]if frames else None;parent=tree
   if frame and x>frame['indent']+.6:
    prior=last_leaf(frame['item']);parent=frame['item']
    if not prior or not prior['text'].rstrip().endswith(':'):
     unresolved.append({'kind':'nested_marker_parent_context','source_fragment':f['id'],'qualification':False,'reason':'Indented literal marker lacks an immediately owned printed colon lead-in; parent relationship provisional'})
    frame=None
   elif frame and (abs(x-frame['indent'])>.6 or frame['family']!=family or value is not None and value!=frame['last_value']+1):
    if value is not None and value!=1:unresolved.append({'kind':'ordered_marker_sequence_gap','source_fragment':f['id'],'value':value,'qualification':False})
    frames.clear();frame=None
   if frame is None:
    if value is not None and value!=1:unresolved.append({'kind':'ordered_list_noninitial_start','source_fragment':f['id'],'value':value,'qualification':False})
    node={'kind':'source_list','id':f['id']+'::list','html_tag':'ul'if value is None else 'ol','family':family,'indent':x,'children':[],'qualification_scope':'Only literal marker sequence/observed geometry; no inferred legal numbering or whole-publication claim'};parent['children'].append(node);listnodes.append(node);frame={'list':node,'item':None,'indent':x,'family':family,'last_value':None};frames.append(frame)
   item={'kind':'source_item','id':f['id']+'::item','literal_marker':m['literal'],'children':[]};frame['list']['children'].append(item);frame['item']=item;frame['last_value']=value;para(item,f);continue
  # Parenthesized text is never automatically promoted into a list. Retain its
  # original physical paragraph/continuation and explicit candidate disposition.
  if m:
   disposition=parenthetical_disposition(last_semantic,f,m)
   if disposition:nonlists.append(disposition)
   else:unresolved.append({'kind':'parenthesized_marker_candidate','source_fragment':f['id'],'literal':m['literal'],'qualification':False,'reason':'No qualified printed parenthesized-item sequence or source-backed wrapped-prose disposition'})
  while frames and x<frames[-1]['indent']+4:frames.pop()
  parent=frames[-1]['item']if frames else tree;para(parent,f,hanging=bool(frames))
 leaves=list(walk(tree));assert [x['id']for x in leaves]==[x['id']for x in fragments],'Source flow reordered/dropped/duplicated';assert text(tree)==record['text'],'Canonical text differs from actual whole source record';assert len({w for x in leaves for w in x['word_ids']})==sum(len(x['word_ids'])for x in leaves)
 diagkeys=['ordered_blocks','text','tables','qualification','canonical_structure_selection']+(['html']if'html'in record else[])
 r['superseded_printed_flow_diagnostics']={'schema_version':1,'profile':PROFILE,'source_sha256':SHA,'original_fields':{k:copy.deepcopy(record[k])for k in diagkeys}}
 r['ordered_blocks']=tree['children'];r['text']=text(tree);r['html']=render(tree);r['source_printed_flow_evidence']={'profile':PROFILE,'source_record_id':r['id'],'source_fragments':[f['id']for f in fragments],'list_count':len(listnodes),'literal_marker_items':sum(len(n['children'])for n in listnodes),'printed_paragraph_groups':len(paragraphs),'unresolved':unresolved,'source_explicit_nonlist_dispositions':nonlists,'all_source_fragments_and_words_once':True,'legal_list_paragraph_intent_qualified':False,'whole_publication_qualified':False}
 r['canonical_structure_selection']=dict(r['canonical_structure_selection'],printed_flow_profile=PROFILE,authoritative_fields=list(dict.fromkeys(r['canonical_structure_selection']['authoritative_fields']+['html'])),scope='Whole-source literal flow/marker grouping, existing actual grids and exact IMAGE; unresolved list/paragraph/page-boundary intent explicit. No adoption/dependency/whole-publication qualification.')
 return r

def project(records):
 inv=inventory(records);geometry=load_geometry();by=collections.defaultdict(list)
 for f in inv['fragments']:by[f['unit_id']].append(f)
 result=[project_record(r,by[r['id']],geometry)for r in records];e=[r['source_printed_flow_evidence']for r in result]
 assert sum(r['text'].count('[IMAGE]')for r in result)==sum(r['html'].count('[IMAGE]')for r in result)==5
 return result,{'schema_version':1,'profile':PROFILE,'source_sha256':SHA,'units':172,'pages':62,'source_fragments':1776,'source_words':18662,'additional_native_geometry_fragments':9,'independent_native_line_geometry_queries':68,'source_list_groups':sum(x['list_count']for x in e),'literal_marker_items':sum(x['literal_marker_items']for x in e),'printed_paragraph_groups':sum(x['printed_paragraph_groups']for x in e),'source_explicit_nonlist_dispositions':sum(len(x['source_explicit_nonlist_dispositions'])for x in e),'source_literal_block_list_topology_qualified':not any(v['kind']in ['nested_marker_parent_context','ordered_marker_sequence_gap','ordered_list_noninitial_start','parenthesized_marker_candidate']for x in e for v in x['unresolved']),'unresolved_counts':dict(collections.Counter(v['kind']for x in e for v in x['unresolved'])),'all_source_text_and_order_exact':True,'all_source_fragment_word_ids_once':True,'IMAGE_count':5,'canonical_tables':sum(len(r['tables'])for r in result),'canonical_cells':sum(len(t['cells'])for r in result for t in r['tables']),'source_native_reading_order_complete':False,'nested_list_hierarchy_complete':False,'paragraph_continuation_semantics_complete':False,'required_dependencies_complete':False,'edition_complete':False,'publication_complete':False}

def outputs(records):
 out={'records.jsonl':''.join(json.dumps(r,sort_keys=True,ensure_ascii=False)+'\n'for r in records).encode()};buf=io.StringIO(newline='');fields=['id','document_id','unit','heading','source_pages','text','html'];w=csv.DictWriter(buf,fields);w.writeheader()
 for r in records:w.writerow({k:json.dumps(r[k])if k=='source_pages'else r.get(k,'')for k in fields})
 out['records.csv']=buf.getvalue().encode();return out

