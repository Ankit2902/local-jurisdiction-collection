"""Exact-source Infrastructure bookmark/printed-heading projection, without guessed hierarchy."""
import collections,copy,csv,hashlib,io,json,pathlib,re
SHA='915fe1fdf8ff5da33acfce7d08637808cb57886fbbc7f157b2b81bfcf970827c'
ID='82-0c6b3dc40877'
URL='https://online.encodeplus.com/regs/overlandpark-ks/doclibrary.aspx?id=3e3d98cc-890e-4630-9c2b-8f84375b0c67'
PROFILE='infrastructure-native-printed-outline-v1'
INVENTORY_SHA='ddedccc901bc14801c80a9b2c7ff2c481d35bc5476d9e5828354fb5c9f2af1e8'
BASELINE_SHA='2f627b1800628560014798685a6be778178e4068bb3d9cbd417f2be9bd2efc94'
PROSE_PAGES={11:1,12:3,13:4,14:1}
GRID_PAGES={51:2,53:2,56:1}
def digest(b):return hashlib.sha256(b).hexdigest()
def norm(s):return re.sub('[^a-z0-9]','',s.lower())
def citation(s):
 m=re.match(r'^(Section\s+\d+|\d+(?:\.\d+)*)(?:\.|\s|$)',s,re.I)
 return m.group(1).lower() if m else None
def native_inventory(data,records):
 from pypdf import PdfReader
 import pdfplumber
 if digest(data)!=SHA:raise ValueError('Wrong exact native Infrastructure source')
 reader=PdfReader(io.BytesIO(data),strict=True);root=reader.trailer['/Root']
 assert '/StructTreeRoot' not in root,'Unexpected source tagged-tree disposition'
 pageids={p.indirect_reference.idnum:i+1 for i,p in enumerate(reader.pages)};out=[];seen=set()
 def walk(ref,parent=None):
  while ref:
   obj=ref.get_object();refid=getattr(obj,'indirect_reference',None);key=(refid.idnum,refid.generation) if refid else id(obj)
   assert key not in seen;seen.add(key);a=obj['/A'];d=a['/D'];assert a['/S']=='/GoTo' and isinstance(d,list)
   n=len(out);out.append({'ordinal':n,'parent_ordinal':parent,'title':str(obj['/Title']),'object_reference':list(key) if isinstance(key,tuple) else None,'destination_page':pageids[d[0].idnum],'destination_coordinates':list(d[1:])})
   if obj.get('/First'):walk(obj['/First'],n)
   ref=obj.get('/Next')
 walk(root['/Outlines']['/First']);assert len(out)==171 and all(x['parent_ordinal'] is None for x in out)
 bypage={r['physical_page']:r for r in records}
 for x in out:
  bs=bypage[x['destination_page']]['ordered_blocks'];matches=[]
  for i,b in enumerate(bs):
   for count in [1,2,3]:
    text=' '.join(z.get('text','') for z in bs[i:i+count])
    if norm(text)==norm(x['title']):matches.append({'block_index':i,'blocks':count,'printed_title':text,'title_match':'separator_normalized_exact'})
  if matches:matches=[min(matches,key=lambda m:m['blocks'])]
  else:
   for i,b in enumerate(bs):
    text=b.get('text','');c=citation(x['title'])
    if (c and citation(text)==c) or (x['ordinal']==106 and text.startswith('SMALL CELL AESTHETIC STANDARDS')):matches.append({'block_index':i,'blocks':1,'printed_title':text,'title_match':'explicit_printed_title_differs_from_outline'})
  assert len(matches)==1,('Ambiguous/missing source heading',x['ordinal'],matches)
  x.update(matches[0])
 vectors={};styles=[]
 with pdfplumber.open(io.BytesIO(data)) as pdf:
  for x in out:
   bs=bypage[x['destination_page']]['ordered_blocks'][x['block_index']:x['block_index']+x['blocks']]
   chars=[c for c in pdf.pages[x['destination_page']-1].chars if any(b['bbox'][0]-.2<=(c['x0']+c['x1'])/2<=b['bbox'][2]+.2 and b['bbox'][1]-.3<=(c['top']+c['bottom'])/2<=b['bbox'][3]+.3 for b in bs)]
   assert norm(''.join(c['text'] for c in chars))==norm(x['printed_title']),('Native printed heading differs',x['ordinal'])
   # The exact source uses one plain applicability M after heading129; keep it literal.
   notbold=''.join(c['text'] for c in chars if c['text'].strip() and 'Bold' not in c['fontname'])
   assert not notbold or (x['ordinal']==129 and notbold=='M'),('Source heading style is not qualified',x['ordinal'],notbold)
   x['source_characters']=[{k:c.get(k) for k in ['text','fontname','size','x0','x1','top','bottom','stroking_color','non_stroking_color']} for c in chars]
  for n in sorted(set(PROSE_PAGES)|set(GRID_PAGES)):
   p=pdf.pages[n-1];vectors[str(n)]={'rectangles':p.rects,'lines':p.lines,'curves':p.curves}
 # Preserve duplicate destinations, including competing Y positions; do not let a dictionary parser overwrite.
 ref=root.raw_get('/Dests');offset=reader.xref[ref.generation][ref.idnum];end=data.index(b'endobj',offset)+6;raw=data[offset:end]
 entries=re.findall(rb'/([^\s]+)\s*\[([^\]]+)\]',raw);dests=collections.defaultdict(list)
 for key,value in entries:dests[key.decode('ascii')].append(value.decode('ascii'))
 duplicate={k:v for k,v in dests.items() if len(v)>1}
 return {'source_sha256':SHA,'outlines':out,'vectors':vectors,'duplicate_destination_entries':duplicate,'raw_destination_object_sha256':digest(raw),'struct_tree_present':False,'source_outline_hierarchy_flat':True,'native_images_decoded':False}
def footer(b,page):
 text=b.get('text','');top=b['bbox'][1]
 return top>680 and (text=='Manual of Infrastructure Standards' or text.startswith('City of Overland Park, Public Works') or re.fullmatch(r'(?:Page \d+|A-\d+)',text) is not None)
def covers(interval,segments,tolerance=.6):
 lo,hi=interval;end=lo
 for a,b in sorted(segments):
  if a<=end+tolerance:end=max(end,b)
 return end>=hi-tolerance
def qualify_cell_grid(cell,table,lines):
 x0,y0,x1,y1=cell['bbox']
 for y in [y0,y1]:assert covers((x0,x1),[(l['x0'],l['x1']) for l in lines if abs(l['top']-y)<.6 and abs(l['bottom']-l['top'])<.1]),'Missing printed horizontal cell boundary'
 for x in [x0,x1]:assert covers((y0,y1),[(l['top'],l['bottom']) for l in lines if abs(l['x0']-x)<.6 and abs(l['x1']-l['x0'])<.1]),'Missing printed vertical cell boundary'
 assert abs(table['row_boundaries'][cell['row']]-y0)<.6 and abs(table['row_boundaries'][cell['row']+cell['rowspan']]-y1)<.6,'Rowspan differs from printed boundaries'
 assert abs(table['column_boundaries'][cell['column']]-x0)<.6 and abs(table['column_boundaries'][cell['column']+cell['colspan']]-x1)<.6,'Colspan differs from printed boundaries'
def canonical_pages(records,inventory):
 assert digest(json.dumps(inventory,sort_keys=True,separators=(',',':')).encode())==INVENTORY_SHA,'Source inventory binding differs'
 assert digest(json.dumps(records,sort_keys=True,separators=(',',':')).encode())==BASELINE_SHA,'Retained canonical native IR differs'
 assert inventory['source_sha256']==SHA and len(records)==62
 pages=copy.deepcopy(records);prose=0;grids=0
 for n,r in enumerate(pages,1):
  assert r['physical_page']==n and r['document_id']==ID and r['raw_sha256']==SHA
  assert all(r['pdf_qualification'][k] is True for k in ['source_word_ownership_complete','normalized_source_word_characters_agree','independent_text_engine_characters_agree','source_words_cover_deduplicated_glyph_characters'])
  if n in PROSE_PAGES:
   assert len(r['tables'])==PROSE_PAGES[n];v=inventory['vectors'][str(n)]
   assert all(not a['stroke'] and a['fill'] and list(a['non_stroking_color'])==[1.0,1.0,1.0] for a in v['rectangles'])
   for t in r['tables']:
    # Short printed word underlines may occur; no source vertical/full-width grid boundary exists.
    box=t['bbox']
    assert not any((abs(a['x1']-a['x0'])<.1 and box[0]-.1<=a['x0']<=box[2]+.1 and max(a['top'],box[1])<min(a['bottom'],box[3])) or (a['x0']<=box[0]+.1 and a['x1']>=box[2]-.1 and box[1]-.1<=a['top']<=box[3]+.1) for a in v['lines'])
   r['source_false_table_diagnostics']=copy.deepcopy({k:r[k] for k in ['tables','ordered_blocks','text','ordering','pdf_qualification']})
   for b in r['ordered_blocks']:
    if b['kind']=='table':b['kind']='text';b['source_projection_disposition']='Prose over white un-stroked fill rectangles; original detector table retained';prose+=1
   r['tables']=[]
   r['pdf_qualification'].update({'detected_table_count':0,'detected_table_cells':0,'independent_table_cells_agree':0,'table_scope':'Exact source white-fill prose disposition; removed inferred grids retained verbatim as diagnostics'})
  elif n in GRID_PAGES:
   assert len(r['tables'])==GRID_PAGES[n]
   v=inventory['vectors'][str(n)];assert len(v['lines'])=={51:27,53:27,56:16}[n]
   for t in r['tables']:
    # Native solid grid geometry/merged spans remain as printed. No textual correction.
    t['source_structure_disposition']='Printed stroked requirements grid; title/header/footnote rows remain literal'
    t['source_stroked_line_count']=len(v['lines'])
    for cell in t['cells']:qualify_cell_grid(cell,t,v['lines'])
    t['source_physical_grid_cells_and_spans_qualified']=True
    grids+=1
 assert prose==9 and grids==5
 return pages
def project(records,inventory):
 pages=canonical_pages(records,inventory);anchors=inventory['outlines'];flat=[]
 for r in pages:
  for i,b in enumerate(r['ordered_blocks']):flat.append({'page':r['physical_page'],'block_index':i,'block':copy.deepcopy(b),'page_control':footer(b,r['physical_page'])})
 position={(x['page'],x['block_index']):i for i,x in enumerate(flat)}
 locations=[position[(a['destination_page'],a['block_index'])] for a in anchors]
 assert locations==sorted(set(locations)),'Source bookmark order and printed order disagree'
 starts=[0]+locations;labels=[None]+anchors;units=[]
 for i,(start,a) in enumerate(zip(starts,labels)):
  end=starts[i+1] if i+1<len(starts) else len(flat);frags=flat[start:end]
  assert frags
  heading=' '.join(f['block'].get('text','') for f in frags[:a['blocks']]) if a else ''
  if a:assert heading==a['printed_title']
  units.append({'id':ID+'::printed-unit:'+str(i),'document_id':ID,'unit':'source_printed_outline_unit' if a else 'source_frontmatter','heading':heading,'parent_id':None,'source_outline_parent_ordinal':None,'source_outline':copy.deepcopy(a),'source_pages':sorted({f['page'] for f in frags}),'raw_sha256':SHA,'source_document_url':URL,'source_fragments':frags,'ordered_blocks':[f['block'] for f in frags],'text':'\n'.join(f['block'].get('text','') for f in frags),'tables':[t for r in pages for t in r['tables'] if any(f['page']==r['physical_page'] and f['block']['kind']=='table' and f['block'].get('id')==t['id'] for f in frags)],'qualification':{'flat_bookmark_and_printed_heading_binding':a is not None,'cross_page_source_fragment_ownership':True,'nested_list_hierarchy_qualified':False,'paragraph_continuation_semantics_qualified':False,'external_dependencies_complete':False,'adopted_edition_qualified':False,'whole_publication_complete':False}})
 for u in units:u['qualification'].update({'source_stroked_grid_count':len(u['tables']),'source_stroked_grid_cell_count':sum(len(t['cells']) for t in u['tables'])})
 # Every source block and whole-word ownership ID must occur once, not merely the same text bag.
 assert [(f['page'],f['block_index']) for u in units for f in u['source_fragments']]==[(f['page'],f['block_index']) for f in flat]
 ids=[w for u in units for b in u['ordered_blocks'] for w in b.get('word_ids',[])]
 assert len(ids)==len(set(ids))
 assert sum(u['text'].count('[IMAGE]') for u in units)==5
 return units,{'source_sha256':SHA,'source_pages':62,'primary_units':len(units),'printed_bookmark_units':171,'source_blocks':len(flat),'source_control_blocks':sum(f['page_control'] for f in flat),'cross_page_units':sum(len(u['source_pages'])>1 for u in units),'white_fill_false_table_regions':9,'diagnostic_detector_cells':149,'remaining_source_stroked_grids':5,'remaining_grid_cells':79,'all79_grid_cell_boundaries_and_spans_match_native_strokes':True,'source_outline_title_differences':sum(a['title_match']!='separator_normalized_exact' for a in anchors),'source_named_destination_duplicate_keys':len(inventory['duplicate_destination_entries']),'all_word_ids_once':True,'image_markers':5,'whole_publication_complete':False,'logical_hierarchy_qualified':False,'required_dependency_completeness':False,'original_page_records':records,'canonical_pages':pages}
def outputs(units):
 j=''.join(json.dumps(u,sort_keys=True,ensure_ascii=False)+'\n' for u in units).encode();s=io.StringIO();w=csv.DictWriter(s,fieldnames=['id','document_id','unit','heading','source_pages','text']);w.writeheader()
 for u in units:w.writerow({k:json.dumps(u[k]) if k=='source_pages' else u[k] for k in w.fieldnames})
 return {'records.jsonl':j,'records.csv':s.getvalue().encode()}
