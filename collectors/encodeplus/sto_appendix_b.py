"""Exact source-pinned STO Appendix B canonical projection. No file/network/image APIs."""
from collections import Counter,defaultdict
import copy,hashlib,json,re,unicodedata
import pypdfium2.raw as raw
PDF_SHA='594128464bdc6c0dd1336aa00acb93c1ecbfdc5980e4265e63d6e134df98f127'
SOURCE_URLS=('https://codes.opkansas.org/municipal-code/doclibrary.aspx?id=8615d268-3650-47cb-a6fd-c1732367f1e4','https://online.encodeplus.com/regs/overlandpark-ks/doclibrary.aspx?id=8615d268-3650-47cb-a6fd-c1732367f1e4')
def compact(s):return ''.join(c for c in unicodedata.normalize('NFKC',s) if not c.isspace() and c not in '\u200b\u00ad\ufeff')
def bbox(w):return [float(w[k]) for k in ['x0','top','x1','bottom']]
def inter(a,b):return min(a[2],b[2])>max(a[0],b[0]) and min(a[3],b[3])>max(a[1],b[1])
def lines(words):
 rows=[]
 for w in sorted(words,key=lambda w:(w['top'],w['x0'])):
  if not rows or abs(rows[-1][0]['top']-w['top'])>3:rows.append([w])
  else:rows[-1].append(w)
 return [sorted(row,key=lambda w:w['x0']) for row in rows]
def text(ws):return ' '.join(w['text'] for w in ws)
def _hash(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def _neutral(value,prefix):
 if isinstance(value,str):return value.replace(prefix,'{PAGE}')
 if isinstance(value,list):return [_neutral(v,prefix) for v in value]
 if isinstance(value,dict):return {k:_neutral(v,prefix) for k,v in value.items()}
 return value
PINS={198: {'page_size': [306.0, 594.0], 'native_text_sha256': '90ee5bfa0d112bb7fb30aeec6273cd23889c18fcfd92015da6b69223602f2685', 'baseline_tables_sha256': '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945', 'word_geometry_sha256': '4ff14a18119b74d6253c39a598be01204f7bcc50baba713976d5d37124bd0519', 'glyph_geometry_sha256': 'cd16032d10eca3e8204624f6432206500f6b754ba5a2f055179ddf678ed06159', 'physical_structure_sha256': 'f7449e40ac629fd8c7969897abaaf772c70b957b7770baf8dd05727114460153', 'failed_cells': 0, 'source_words': 268, 'source_glyphs': 1493}, 199: {'page_size': [306.0, 594.0], 'native_text_sha256': '72c2dd1664df25dda7e567972c94df928d80484b9491670ba0a7c3f09aaf9de2', 'baseline_tables_sha256': '7dc003266ff6f2203b24c6675ca1c5fd29bf04805efab65286eb6fac59d4838f', 'word_geometry_sha256': 'bdd9a82f3c2955b414254abe799720084a0309d93d7789a1447d318fb597ad05', 'glyph_geometry_sha256': 'a22ba7a18745dadb17df7e172360748bad4d90b23e762d276637ac58549d91c6', 'physical_structure_sha256': 'f6ec698a6b5deb786d440ac0c21961e2073e5476f011c3c91bf18e972c4461b1', 'failed_cells': 48, 'source_words': 251, 'source_glyphs': 1367}, 200: {'page_size': [306.0, 594.0], 'native_text_sha256': '802caf9206797e84d83e5a62315eefe62a9fd50c933c2b53782fbfc90e97f723', 'baseline_tables_sha256': '4920e56de5246f971dd6883f81f8706dcceb9bb471bcbfd15eb14c5feb18a566', 'word_geometry_sha256': '2accbc819937a15ec65f0b55139e010b9dc41821e41e28cf950a84c867fc2dcf', 'glyph_geometry_sha256': 'ab99b7f7fc60bc491d9355473d139c7498f13b9080f126b7444d7fbd1fdb0960', 'physical_structure_sha256': '1ca63a81dfb9e637a028395b46c2ac395614695f968a6347467dc25a721a9e38', 'failed_cells': 81, 'source_words': 251, 'source_glyphs': 1388}, 201: {'page_size': [306.0, 594.0], 'native_text_sha256': '84452f82bccd444bbed20930171c578573c2b009a17f7dae25f8f1481e27aff8', 'baseline_tables_sha256': 'b20d8c09ac97f7bb0f2bec53ce43774cc999bafa0e63eda5853c690fba9b70a3', 'word_geometry_sha256': '9e5cde7b0e06d1f439ca29cec069124a50ce343773d393377cb73023148a9e56', 'glyph_geometry_sha256': '93a6b2d60fa7a786358944de46025b98e675197b94a866c0aec935fa94b0933a', 'physical_structure_sha256': 'e0227fb0cd75e6d715c1477476480dd884170e6f4ef5488ffdc34d6019b0124f', 'failed_cells': 71, 'source_words': 245, 'source_glyphs': 1435}, 202: {'page_size': [306.0, 594.0], 'native_text_sha256': '07d009414343fa38477c77830d81c5f7ca4c247239a5a24524cca6eb16fe3dfa', 'baseline_tables_sha256': 'a5ff435ef7a769d4eb98257cf8d23dea9543a5ab50f999febf584ed766174c54', 'word_geometry_sha256': '9c94e8a58863a5c7cec77d3e609885f437cfc25bacce5ce5cecf648509c87cb3', 'glyph_geometry_sha256': 'b3cd2c7b27f7b8011e5dbb5bcdbb38c5db307963f14ac4e561c06c831054cd2a', 'physical_structure_sha256': '65649cba67adce302a64bb9948f8d5d7ec9c3d4638597f999c9e67c379a2d1b0', 'failed_cells': 60, 'source_words': 227, 'source_glyphs': 1338}, 203: {'page_size': [306.0, 594.0], 'native_text_sha256': '1dc18d1c3f1ef91abf019f4852c3a1b6a8b2bff14ec849ba7c7c2b8f9d7ce40a', 'baseline_tables_sha256': '7019e04a0d9fc32626c6904b24c9abde0a08f364ca74ffa793f0b06e35ce5c99', 'word_geometry_sha256': 'fad7b86573b86f0418da70c6f8bbd917b57fea0cc5e4b2be4c41dadf193b5721', 'glyph_geometry_sha256': '8fe964881ae1149d0288f08843a2dde1063bbd9260d7c37512ead267e802d7c8', 'physical_structure_sha256': 'ef4a0ad097c15749c94982304405a81fe5c4a3e4a14a47a2f01838fd3629ebec', 'failed_cells': 14, 'source_words': 76, 'source_glyphs': 494}}
SOURCE_INTRO={'description_is_reference_only_not_legal_description': True, 'literal_text': 'APPENDIX B\nOrdinance Traffic Infractions\nThe following sections of the Standard Traffic Ordinance\n(STO) are classified as Ordinance Traffic Infractions by state\nlaw (K.S.A. 8-2118). The fine for violation of these sections must\nbe established by the municipal judge in a schedule of fines.\n(K.S.A. 12-4305) The sections of the STO shown prohibit the\nsame offense prohibited by state statute. The description of\noffense is for reference only and is not a legal description.', 'physical_page': 198}
CARRYOVER={'association': 'Consecutive printed Appendix B description column; next source line has no competing left-role anchor; exact-source pair pinned', 'description_after_break': 'clearance', 'description_before_break': 'Passing on left with insufficient', 'entry_id': 'overland-required-57f6356897e1::page:198::source-three-column::entry:22', 'from_physical_page': 198, 'qualified_source_text_continuation': True, 'source_page_folios': ['187', '188'], 'source_section': '42', 'source_statute': '8-1518', 'to_physical_page': 199}
ENDING_WITNESS={'extraction_bbox': [65.33790000000002, 39.908300000000054, 258.6464000000001, 111.6493000000001], 'full_page_record_sha256': '429427863d4a79efd312ce01db7ddff7295c88ff0e5f85b91ec868b35458b03b', 'independent_native_text': 'INDEX\r\nTo\r\nStandard Traffic Ordinance for Kansas Cities\r\n(Figures refer to section numbers)', 'physical_page': 204, 'text': 'INDEX\nTo\nStandard Traffic Ordinance for Kansas Cities\n(Figures refer to section numbers)'}
def page_ir(page,tp,item,bs):
 assert tp.get_text_range()==bs['pdfium_stream_text'] and bs['raw_sha256']==PDF_SHA and bs['source_url']==item['url']+'#page='+str(bs['physical_page'])
 page=page.dedupe_chars(tolerance=.5);ws=page.extract_words(x_tolerance=1.5,y_tolerance=3,extra_attrs=['fontname','size']);ident=bs['id']
 for i,w in enumerate(ws,1):w['id']=ident+'::word:'+str(i)
 rows=lines(ws);headers=[i for i,r in enumerate(rows) if text(r)=='STO'];assert len(headers)==1;hi=headers[0];assert text(rows[hi+1])=='Section Statute Description of Offense';assert hi==9 if bs['physical_page']==198 else hi==1
 stat_x=rows[hi+1][1]['x0'];desc_x=rows[hi+1][2]['x0'];assert stat_x in [61,79] and desc_x==stat_x+44
 assert len(rows[-1])==1 and re.fullmatch(r'\d+',rows[-1][0]['text']);footer=len(rows)-1
 preamble=set(range(hi)) if bs['physical_page']==198 else set();table_lines=[i for i in range(len(rows)) if i not in preamble and i!=footer]
 glyphs=[];wg=defaultdict(list)
 for i,c in enumerate(page.chars,1):
  if not compact(c['text']):continue
  cx=(c['x0']+c['x1'])/2;cy=(c['top']+c['bottom'])/2;owners=[w for w in ws if w['x0']<=cx<=w['x1'] and w['top']<=cy<=w['bottom']];assert len(owners)==1
  g={'id':ident+'::glyph:'+str(i),'text':c['text'],'bbox':bbox(c),'word_id':owners[0]['id'],'fontname':c['fontname'],'size':c['size'],'color':c.get('non_stroking_color')};glyphs.append(g);wg[owners[0]['id']].append(g)
 for w in ws:
  wg[w['id']].sort(key=lambda g:g['bbox'][0]);assert compact(w['text'])==compact(''.join(g['text'] for g in wg[w['id']]))
 assert Counter(compact(''.join(w['text'] for w in ws)))==Counter(compact(''.join(g['text'] for g in glyphs)))
 native_seen=set()
 for ni in range(tp.count_chars()):
  ch=chr(int(raw.FPDFText_GetUnicode(tp,ni)))
  if not compact(ch):continue
  nb=list(map(float,tp.get_charbox(ni)));cx=(nb[0]+nb[2])/2;cy=float(page.height)-(nb[1]+nb[3])/2;owners=[g for g in glyphs if g['bbox'][0]<=cx<=g['bbox'][2] and g['bbox'][1]<=cy<=g['bbox'][3]];assert len(owners)==1
  g=owners[0];native_seen.add(g['id']);g.setdefault('native_char_indices',[]).append(ni);g.setdefault('native_characters',[]).append({'index':ni,'unicode':ch,'tight_bbox':nb,'loose_bbox':list(map(float,tp.get_charbox(ni,loose=True)))})
 assert len(native_seen)==len(glyphs)
 for g in glyphs:
  g['native_unicode']=''.join(c['unicode'] for c in g['native_characters']);assert compact(g['native_unicode'])==compact(g['text']),('Native/source glyph content differs',bs['physical_page'],g)
  g['source_ligature_native_character_count']=len(g['native_characters'])
 groups=[[],[],[]]
 for ri in table_lines:
  for w in rows[ri]:
   col=0 if w['x0']<stat_x-.1 else 1 if w['x0']<desc_x-.1 else 2;w['column']=col;groups[col].append(w)
 cuts=[min(w['x0'] for g in groups for w in g)-1]
 for i in [0,1]:
  left=max(w['x1'] for w in groups[i]);right=min(w['x0'] for w in groups[i+1]);assert left<right,'No whole-word intercolumn gap';cuts.append((left+right)/2)
 cuts.append(max(w['x1'] for g in groups for w in g)+1)
 yc=[];source_advance_y=[];native_ink_lines=[]
 for row in rows:
  chars=[c for w in row for g in wg[w['id']] for c in g['native_characters']];native_ink_lines.append([min(float(page.height)-c['tight_bbox'][3] for c in chars),max(float(page.height)-c['tight_bbox'][1] for c in chars)])
 for i,row in enumerate(rows):
  slo=min(w['top'] for w in row);shi=max(w['bottom'] for w in row);sprev=max(w['bottom'] for w in rows[i-1]) if i else slo-2;snxt=min(w['top'] for w in rows[i+1]) if i+1<len(rows) else shi+2;source_advance_y.append([(sprev+slo)/2,(shi+snxt)/2])
  lo,high=native_ink_lines[i];prev=native_ink_lines[i-1][1] if i else lo-2;nxt=native_ink_lines[i+1][0] if i+1<len(rows) else high+2;assert prev<lo and high<nxt,'Actual native ink lines overlap; no rectangular row inference';yc.append([(prev+lo)/2,(high+nxt)/2])
 cells=[];physical=[];word_owner={};glyph_owner={}
 def cell(kind,ri,col,words,b):
  cid=ident+'::source-three-column::line:'+str(ri+1)+'::'+str(col);value=text(words);native=tp.get_text_bounded(b[0],float(page.height)-b[3],b[2],float(page.height)-b[1]);assert compact(value)==compact(native),('Independent complete cell content differs',bs['physical_page'],ri,col,value,native)
  for w in words:
   assert w['id']not in word_owner;word_owner[w['id']]=cid
   for g in wg[w['id']]:assert g['id']not in glyph_owner;glyph_owner[g['id']]=cid
  c={'id':cid,'kind':kind,'source_physical_line':ri+1,'column':col,'role':['STO Section','Statute','Description of Offense'][col] if isinstance(col,int) else col,'text':value,'source_word_ids':[w['id'] for w in words],'source_glyph_ids':[g['id'] for w in words for g in wg[w['id']]],'extraction_bbox':b,'independent_native_text':native,'independent_ordered_characters_agree':True,'physical_empty_disposition':None if words else 'Source physical blank; no value/rowspan filled'};cells.append(c);return c
 for ri,row in enumerate(rows):
  if ri in preamble or ri==footer:
   kind='printed_folio' if ri==footer else 'printed_context_line';c=cell(kind,ri,kind,row,[min(w['x0'] for w in row)-1,yc[ri][0],max(w['x1'] for w in row)+1,yc[ri][1]]);physical.append({'source_line':ri+1,'kind':kind,'cell_ids':[c['id']],'printed_values':[c['text']]});continue
  kind='header_top' if ri==hi else 'header_bottom' if ri==hi+1 else 'printed_data_line';cs=[]
  for col in range(3):cs.append(cell(kind,ri,col,[w for w in row if w['column']==col],[cuts[col],yc[ri][0],cuts[col+1],yc[ri][1]]))
  values=[c['text'] for c in cs]
  if kind=='printed_data_line':
   if values[0]:assert re.fullmatch(r'\d+(?:\.\d+)*',values[0]) and re.fullmatch(r'8-\d+(?:,\d+)?[a-z]?',values[1]),('Unrecognized left-role anchor',values)
   else:assert values[2] and (not values[1] or re.fullmatch(r'8-\d+(?:,\d+)?[a-z]?',values[1]))
  physical.append({'source_line':ri+1,'kind':kind,'cell_ids':[c['id'] for c in cs],'printed_values':values,'header_physically_below_first_data_line':hi>0 and bs['physical_page']!=198})
 assert len(word_owner)==len(ws) and len(glyph_owner)==len(glyphs)
 fail=[]
 for t in bs['tables']:
  for c in t['cells']:
   if c['independent_character_agreement']:continue
   b=c['extraction_bbox'];native=tp.get_text_bounded(b[0],float(page.height)-b[3],b[2],float(page.height)-b[1]);assert native==c['independent_pdfium_text'];contact=[g for g in glyphs if min(b[2],g['bbox'][2])>max(b[0],g['bbox'][0]) and min(b[3],g['bbox'][3])>=max(b[1],g['bbox'][1])-1e-6];native_contacts=[(g,c) for g in glyphs for c in g['native_characters'] if inter(b,[c['tight_bbox'][0],float(page.height)-c['tight_bbox'][3],c['tight_bbox'][2],float(page.height)-c['tight_bbox'][1]])];assert contact or native_contacts,('Old failed cell lacks source advance/native ink contact',bs['physical_page'],c)
   fail.append({'original_failed_cell':c,'original_failure_retained':True,'original_inferred_cell_semantics_qualified':False,'exact_native_query_replay':native,'positive_ink_intersection_glyph_ids':[g['id'] for g in glyphs if inter(b,g['bbox'])],'source_boundary_contact_glyph_ids':[g['id'] for g in contact],'source_boundary_tolerance_points':1e-6,'native_ink_intersection_char_indices':[z['index'] for g,z in native_contacts],'native_ink_intersection_source_glyphs':sorted({g['id'] for g,z in native_contacts}),'reconstructed_cell_owners':sorted({glyph_owner[g['id']] for g in contact}|{glyph_owner[g['id']] for g,z in native_contacts})})
 assert not page.images and not [b for b in bs['ordered_blocks'] if b['kind']=='image_placeholder']
 return {'id':ident+'::source-three-column','document_id':item['id'],'physical_page':bs['physical_page'],'source_url':bs['source_url'],'raw_sha256':PDF_SHA,'page_size':[float(page.width),float(page.height)],'source_words':ws,'source_glyphs':glyphs,'source_header_roles':['STO Section','Statute','Description of Offense'],'source_header_physical_lines':[hi+1,hi+2],'column_boundaries':cuts,'source_advance_row_boundaries':source_advance_y,'native_ink_row_boundaries':yc,'native_ink_line_extents':native_ink_lines,'physical_lines':physical,'cells':cells,'baseline_tables':bs['tables'],'original_failed_cells_crosswalk':fail,'source_word_ownership_complete':True,'source_glyph_ownership_complete':True,'all_complete_physical_cell_native_queries_agree':True,'image_placeholders':[],'image_policy':'[IMAGE]; selected pages have no image objects; no image decoding/extraction/render/OCR','publication_or_whole_PDF_semantic_qualification':False}


def _projection(record,region):
 """Canonical physical order only. Preserve all five previous fields exactly."""
 assert 'canonical_structure_selection' not in record and 'superseded_detector_diagnostics' not in record,'Canonical source already selected'
 assert not region['image_placeholders'] and record['image_placeholder_count']==0
 fields=['tables','ordered_blocks','text','ordering','pdf_qualification'];diag={'schema_version':1,'reason':'Exact source-bound Appendix B three-column physical structure supersedes inferred detector grids/order; all original fields/false flags retained without correction.','raw_ref':record['raw_ref'],'raw_sha256':record['raw_sha256'],'original_record_fields':{k:copy.deepcopy(record[k]) for k in fields}}
 words={w['id']:w for w in region['source_words']};glyphs={g['id']:g for g in region['source_glyphs']};source_cells={c['id']:c for c in region['cells']};table_lines=[ln for ln in region['physical_lines'] if ln['kind']in ['header_top','header_bottom','printed_data_line']];cells=[];owned_words=[];owned_glyphs=[];table_word_ids=[];table_glyph_ids=[];table_text=[]
 for rownum,line in enumerate(table_lines):
  assert len(line['cell_ids'])==3
  vals=[]
  for ci,cid in enumerate(line['cell_ids']):
   src=source_cells[cid];b=src['extraction_bbox'];wids=src['source_word_ids'];gids=src['source_glyph_ids'];assert src['column']==ci and src['text']==' '.join(words[i]['text'] for i in wids);assert compact(src['text'])==compact(''.join(glyphs[i]['text'] for i in gids))==compact(src['independent_native_text']);assert src['independent_ordered_characters_agree'];assert re.sub(r'\s+',' ',src['text']).strip()==re.sub(r'\s+',' ',src['independent_native_text']).strip()
   # Cells own complete words/glyphs. Query bounds enclose actual native ink,
   # not a misleading font advance box that may extend into a neighboring line.
   for gid in gids:
    for nc in glyphs[gid]['native_characters']:
     z=nc['tight_bbox'];ink=[z[0],region['page_size'][1]-z[3],z[2],region['page_size'][1]-z[1]];assert b[0]<ink[0]<=ink[2]<b[2] and b[1]<ink[1]<=ink[3]<b[3]
   cc={'id':src['id'],'row':rownum,'column':ci,'rowspan':1,'colspan':1,'kind':src['kind'],'role':src['role'],'text':src['text'],'bbox':[round(v,3) for v in b],'extraction_bbox':copy.deepcopy(b),'word_ids':copy.deepcopy(wids),'source_glyph_ids':copy.deepcopy(gids),'independent_pdfium_text':src['independent_native_text'],'qualified_pdfium_text':src['independent_native_text'],'independent_character_agreement':True,'independent_ordered_characters_agree':True,'source_physical_line':src['source_physical_line'],'source_empty_disposition':src['physical_empty_disposition'],'logical_rowspan_generated':False,'source_styles':[{'word_id':wid,'glyph_styles':[{'glyph_id':gid,'fontname':glyphs[gid]['fontname'],'size':glyphs[gid]['size'],'color':glyphs[gid]['color']} for gid in gids if glyphs[gid]['word_id']==wid]} for wid in wids]};cells.append(cc);vals.append(src['text']);table_word_ids.extend(wids);table_glyph_ids.extend(gids)
  table_text.append('\t'.join(vals))
 table_id=region['id']+'::canonical-table';table_bounds=[region['column_boundaries'][0],min(c['extraction_bbox'][1] for c in cells),region['column_boundaries'][-1],max(c['extraction_bbox'][3] for c in cells)];header_rows=[i for i,l in enumerate(table_lines) if l['kind']in ['header_top','header_bottom']];assert len(header_rows)==2 and header_rows==([0,1] if record['physical_page']==198 else [1,2]),'Preheader source data order changed'
 table={'id':table_id,'bbox':[round(v,3) for v in table_bounds],'extraction_bbox':table_bounds,'detection':'source-pinned-appendix-b-physical-three-column','cells':cells,'column_boundaries':copy.deepcopy(region['column_boundaries']),'row_boundaries':[cells[3*i]['extraction_bbox'][1] for i in range(len(table_lines))]+[cells[-1]['extraction_bbox'][3]],'header_rows':header_rows,'source_header_roles':copy.deepcopy(region['source_header_roles']),'source_physical_lines':copy.deepcopy(table_lines),'source_evidence_id':region['id'],'physical_cell_fidelity_complete':True,'logical_rowspan_generated':False,'source_description_is_reference_only_not_legal_description':True,'logical_legal_reference_semantics_complete':False}
 blocks=[];table_emitted=False
 for line in region['physical_lines']:
  if line['kind']in ['header_top','header_bottom','printed_data_line']:
   if table_emitted:continue
   block={'kind':'table','id':table_id,'bbox':table['bbox'],'text':'\n'.join(table_text),'word_ids':table_word_ids,'source_glyph_ids':table_glyph_ids,'source_evidence_id':region['id'],'reading_order':'Exact source physical lines then three observed columns; first data line remains before repeated header on199–203, source blanks kept'};blocks.append(block);owned_words.extend(table_word_ids);owned_glyphs.extend(table_glyph_ids);table_emitted=True
  else:
   assert len(line['cell_ids'])==1;sc=source_cells[line['cell_ids'][0]];blocks.append({'kind':'text','id':sc['id'],'bbox':[round(v,3) for v in sc['extraction_bbox']],'extraction_bbox':copy.deepcopy(sc['extraction_bbox']),'text':sc['text'],'word_ids':copy.deepcopy(sc['source_word_ids']),'source_glyph_ids':copy.deepcopy(sc['source_glyph_ids']),'source_kind':sc['kind'],'source_evidence_id':region['id']});owned_words.extend(sc['source_word_ids']);owned_glyphs.extend(sc['source_glyph_ids'])
 assert Counter(owned_words)==Counter(words.keys()) and Counter(owned_glyphs)==Counter(glyphs.keys()),'Canonical output lost/duplicated source owners'
 canonical_text='\n'.join(b['text'] for b in blocks);assert Counter(compact(canonical_text))==Counter(compact(''.join(w['text'] for w in region['source_words']))),'Canonical text lost/duplicated source characters'
 q=copy.deepcopy(record['pdf_qualification']);old={t['id']+':independent_cell_text_disagreement' for t in record['tables']};q['review_conditions']=[v for v in q['review_conditions'] if v not in old];q.update({'detected_table_count':1,'detected_table_cells':len(cells),'independent_table_cells_agree':len(cells),'source_word_ownership_complete':True,'word_ownership_failures':[],'normalized_source_word_characters_agree':True,'source_physical_cell_fidelity_complete':True,'source_physical_logical_semantics_complete':False,'table_scope':'Exact Appendix B physical three-column source cells/order only; old inferred grids and false flags exact under superseded_detector_diagnostics. Description text is expressly reference-only, not a legal description; no legal rowspan, edition or whole-PDF acceptance.'})
 return {'tables':[table],'ordered_blocks':blocks,'text':canonical_text,'ordering':{'method':'Exact Appendix B printed physical source order, including preheader data lines; three observed columns; context/folios preserved','gutter':None,'source_evidence_id':region['id'],'source_order_qualified':True,'logical_rowspan_generated':False},'pdf_qualification':q,'superseded_detector_diagnostics':diag,'canonical_structure_selection':{'profile':'sto_appendix_b','source_sha256':record['raw_sha256'],'source_url':record['source_url'],'physical_page':record['physical_page'],'source_evidence_id':region['id'],'canonical_table_ids':[table_id],'authoritative_fields':fields,'scope':'Exact physical rows/headers/columns/word-glyph ownership and printed order; reference-only descriptions, no legal/edition/whole-PDF qualification'}}

def attach_record(record,page,textpage,item,source_sha256):
 physical=record.get('physical_page')
 if source_sha256!=PDF_SHA or item.get('url')not in SOURCE_URLS or physical not in PINS:return False
 pin=PINS[physical];assert record['raw_sha256']==source_sha256 and record['document_id']==item['id'] and record['source_url']==item['url']+'#page='+str(physical),'Appendix B source-record/owner binding mismatch'
 assert [float(page.width),float(page.height)]==pin['page_size'];assert hashlib.sha256(textpage.get_text_range().encode()).hexdigest()==pin['native_text_sha256'],'Appendix B native source text drift'
 assert _hash(_neutral(record['tables'],record['id']))==pin['baseline_tables_sha256'],'Appendix B original detector evidence drift'
 region=page_ir(page,textpage,item,record)
 wk=('text','x0','top','x1','bottom','fontname','size','column');gk=('text','bbox','fontname','size','color','native_char_indices','native_characters','native_unicode','source_ligature_native_character_count')
 assert _hash([{k:w.get(k) for k in wk} for w in region['source_words']])==pin['word_geometry_sha256'],'Appendix B whole-word/header geometry drift'
 assert _hash([{k:g.get(k) for k in gk} for g in region['source_glyphs']])==pin['glyph_geometry_sha256'],'Appendix B original glyph/native geometry drift'
 assert _hash(_neutral({k:region[k] for k in ['column_boundaries','source_advance_row_boundaries','native_ink_row_boundaries','native_ink_line_extents','physical_lines','cells']},record['id']))==pin['physical_structure_sha256'],'Appendix B source physical order/complete cell bounds drift'
 assert len(region['original_failed_cells_crosswalk'])==pin['failed_cells']
 projection=_projection(record,region)
 region['source_binding']={'raw_sha256':source_sha256,'source_url':item['url'],'physical_page':physical,'native_text_sha256':pin['native_text_sha256'],'word_geometry_sha256':pin['word_geometry_sha256'],'glyph_geometry_sha256':pin['glyph_geometry_sha256'],'physical_structure_sha256':pin['physical_structure_sha256'],'qualification':'Exact observed source bytes/URL/page, header/body source words, native ink/advance bounds, glyph styles and source physical order'}
 region['source_reference_only_caveat']=copy.deepcopy(SOURCE_INTRO)
 if physical in [198,199]:region['cross_page_continuation_witness']={k:copy.deepcopy(v) for k,v in CARRYOVER.items() if k!='entry_id'};region['cross_page_continuation_witness']['canonical_text_filled_or_merged']=False
 if physical==203:region['source_ending_index_witness']=copy.deepcopy(ENDING_WITNESS)
 record.update(projection);record['source_appendix_b_schedules']=[region];return True

def summary(records):
 schedules=[s for r in records for s in r.get('source_appendix_b_schedules',[])]
 if not schedules:return None
 pages=[s['physical_page'] for s in schedules];assert len(pages)==len(set(pages));assert all(s['raw_sha256']==PDF_SHA for s in schedules)
 observed=set(pages);complete=observed==set(PINS);return {'scope':'Source-pinned complete Appendix B physical198–203 plus204opening-index witness; notwholePDF/legal/edition qualification','source_sha256':PDF_SHA,'expected_physical_pages':sorted(PINS),'observed_physical_pages':sorted(pages),'source_regions':len(schedules),'source_word_ownership_complete':all(s['source_word_ownership_complete'] for s in schedules),'source_glyph_ownership_complete':all(s['source_glyph_ownership_complete'] for s in schedules),'complete_physical_cells':sum(len(s['cells']) for s in schedules),'physical_cell_fidelity_complete':complete and all(s['all_complete_physical_cell_native_queries_agree'] for s in schedules),'source_cross_page_42_continuation_witness_present':{198,199}<=observed,'preheader_source_data_order_preserved':True,'source_duplicate_section62_occurrences_not_deduplicated':199 in observed,'source_description_reference_only_not_legal_description':True,'additional_blank_section_statute_lines_no_legal_merge_inferred':2 if 198 in observed else 0,'original_failed_detector_cells_retained':sum(len(s['original_failed_cells_crosswalk']) for s in schedules),'whole_pdf_table_semantics_complete':False,'image_policy':'[IMAGE]; no separate image acquisition/decoding/extraction/render/OCR; originalpositions/ownershipunchanged'}
