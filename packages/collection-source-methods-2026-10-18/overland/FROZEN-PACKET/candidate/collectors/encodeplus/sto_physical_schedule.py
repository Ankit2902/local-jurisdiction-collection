"""Exact retained STO physical schedule qualification. No legal-continuation inference.

Derived from independently reviewed finite source geometry; no file/network/image APIs.
All constants are bound by this module's runtime source hash.
"""
import collections,copy,hashlib,json,re,unicodedata

SOURCE_SHA256='594128464bdc6c0dd1336aa00acb93c1ecbfdc5980e4265e63d6e134df98f127'
SOURCE_URLS=('https://codes.opkansas.org/municipal-code/doclibrary.aspx?id=8615d268-3650-47cb-a6fd-c1732367f1e4', 'https://online.encodeplus.com/regs/overlandpark-ks/doclibrary.aspx?id=8615d268-3650-47cb-a6fd-c1732367f1e4')
HEADER_ROLES=[['STO', 'Section'], ['Statute'], ['O.P.M.C', 'Number'], ['Description', 'of', 'Offense']]
PINS={5: {'width': 612.0, 'height': 792.0, 'native_text_sha256': 'bd692c802f366e950a9e2a3766c9f5fbbef53644353c66eb0655af02b0115e11', 'word_geometry_sha256': '2e139f1a0b95f8bcc0ea57b065ad2c58a327da0a56209817f7082f0bccdc809e', 'glyph_geometry_sha256': '66b4f916d9c3f2bc366f1f930d06f3a85d5a59a8426a7c79d98ed0669e4ab30a', 'column_boundaries': [35.0, 103.0733318460375, 169.011474435, 293.45277410209127, 575.6711859100001], 'row_boundaries': [51.19515763851496, 70.81851708925751, 94.89242654000003, 118.79392654000003, 142.69532654, 166.59682654, 190.49842654000003, 214.39992654000002, 238.30127654, 262.20272654, 286.10432654, 310.00582654000004, 333.90722654, 357.80872654, 381.71032654, 405.61182654000004, 429.51317654, 453.41467654, 477.31632654, 501.21777654, 525.11912654, 549.02062654, 572.92222654, 596.82372654, 620.72512654, 644.62662654, 668.52822654, 692.42967654, 716.33102654, 733.78172654], 'baseline_tables_sha256': '6f9aac7d5ac5d535938b51b8a7ea1c28e0dba8ff085019d2948add29456a645c', 'failed_cells': 30}, 9: {'width': 612.0, 'height': 792.0, 'native_text_sha256': '50c826a048f24d8817e9b3d1b27e5626716576c4e6352e5d00ba5f2af3469d1a', 'word_geometry_sha256': 'b58ae631155329dbafcb97d0d742dd2c398a71a0788a757d65b9827792bb8591', 'glyph_geometry_sha256': '1641590b5ee7c71a5525d33a3522fd2a707fb14c8c11a9278b91d5eaac896a33', 'column_boundaries': [35.0, 103.05986398951904, 167.77221664500001, 293.436192396626, 573.1416028900001], 'row_boundaries': [51.194823355478434, 70.8183588589892, 94.89233361250001, 118.79370111250006, 142.69555660125008, 166.59692260125001, 190.4980461125, 214.3996561125, 238.3015111125, 262.2031261125, 286.10425111250004, 310.00561611250004, 333.90747111250005, 357.80884111250003, 381.7099611125, 405.6115711125, 429.51342611250004, 453.41503611250005, 477.3161611125, 501.21753111250007, 525.1193861125, 549.0207511125, 572.9218761125001, 596.8234861125001, 620.7253411125, 644.6269561125, 668.5280761125, 692.4294411125, 716.3313011125001, 733.7822311125001], 'baseline_tables_sha256': 'd86531470c19aedc399d353dc701e8094e86d3129a95da290282cfdaedf51e13', 'failed_cells': 22}, 10: {'width': 612.0, 'height': 792.0, 'native_text_sha256': 'd08a8c8fc665663f0f78a1b7fb411038d2dbf1aa3da6b6e66e7e53f1fb7ea115', 'word_geometry_sha256': '5d86ede99ad371964711c9e5d0b8a1be53fb35b3c1f6fe418c66f182650417fe', 'glyph_geometry_sha256': '55566ea94ccf3c99ed977b5fc1ecfea399da86531a529b500f1c2f480d57301c', 'column_boundaries': [35.0, 103.05986398951904, 162.94598402701905, 293.436192396626, 545.0869106800001], 'row_boundaries': [51.194823355478434, 70.8183588477392, 94.89233360125002, 118.79370111250006, 142.69555661250007, 166.5969226125, 190.4980461125, 214.3996561125, 238.3015111125, 262.2031261125, 286.10425111250004, 310.00561611250004, 333.90747111250005, 357.80884111250003, 381.7099611125, 405.6115711125, 429.51342611250004, 453.41503611250005, 477.3161611125, 494.76660111250004], 'baseline_tables_sha256': '375c72806dd29beb91cf8617d01640aa7b1ed318fd02fbbfd19d5d83e1e5d783', 'failed_cells': 8}}
SOURCE_LEGEND={'blank_physical_lines_not_automatically_converted_to_logical_blank_cells': True, 'color_styling_preserved_not_inferred_from_pixels': True, 'physical_page': 1, 'text': 'STO INDEX\nKey: N/A: The STO was not adopted. If the STO section is blank, then there is no STO equivalent.\nNew Sections for 2026 are in Red.'}
SOURCE_STRUCTURE={'Marked': False, 'logical_table_cells_available': False, 'structure_element_counts': {'/Document': 1, '/P': 278}}

def compact(s):return ''.join(c for c in unicodedata.normalize('NFKC',s) if not c.isspace() and c not in '\u200b\u00ad\ufeff')

def bbox(x):return [float(x[k]) for k in ['x0','top','x1','bottom']]

def intersects(a,b):return min(a[2],b[2])>max(a[0],b[0]) and min(a[3],b[3])>max(a[1],b[1])

def center_inside(c,b):return b[0]<=((c['x0']+c['x1'])/2)<=b[2] and b[1]<=((c['top']+c['bottom'])/2)<=b[3]

def lines(words):
    out=[]
    for w in sorted(words,key=lambda w:(w['top'],w['x0'])):
        if not out or abs(out[-1][0]['top']-w['top'])>3:out.append([w])
        else:out[-1].append(w)
    return [sorted(row,key=lambda w:w['x0']) for row in out]

def headers(words,roles):
    rows=lines(words);matches=[]
    for ri,row in enumerate(rows):
        if [w['text'] for w in row]==[v for role in roles for v in role]:matches.append((ri,row))
    assert len(matches)==1,'Header roles must be observed once, in exact source order'
    ri,row=matches[0];parts=[];offset=0
    for role in roles:parts.append(row[offset:offset+len(role)]);offset+=len(role)
    return rows,ri,parts

def _reconstruct_page(page,tp,item,config,baseline):
    assert tp.get_text_range()==baseline['pdfium_stream_text'],'Native page/source stream changed'
    q=baseline['pdf_qualification'];assert q['independent_text_engine_characters_agree'] and q['source_words_cover_deduplicated_glyph_characters'] and not q['undecoded_cid_literals'],'Required source text qualification missing'
    page=page.dedupe_chars(tolerance=.5);words=page.extract_words(x_tolerance=1.5,y_tolerance=3,extra_attrs=['fontname','size']);ident=baseline['id']
    for i,w in enumerate(words):w['id']=ident+'::word:'+str(i+1)
    source_rows,header_row,header_parts=headers(words,config['header_roles']);assert header_row==0,'Unexpected text above selected source header'
    desc_start=min(w['x0'] for w in header_parts[3]);body=[w for row in source_rows[1:] for w in row];left_words=[w for w in body if w['x0']<desc_start-.25];starts=[]
    for w in sorted(left_words,key=lambda w:w['x0']):
        if not starts or abs(starts[-1]-w['x0'])>.25:starts.append(w['x0'])
    assert len(starts)==3,'Exactly three recurring left-field start positions required'
    field_words=[[],[],[],[]]
    for w in body:
        if w['x0']>=desc_start-.25:col=3
        else:
            hits=[i for i,x in enumerate(starts) if abs(w['x0']-x)<=.25];assert len(hits)==1,'Ambiguous left-column word start';col=hits[0]
        w['column']=col;field_words[col].append(w)
    # All boundaries lie in a globally empty source-word gap, including header.
    cuts=[min(w['x0'] for w in words)-1]
    for c in range(3):
        left=max(w['x1'] for w in field_words[c]+header_parts[c]);right=min(w['x0'] for w in field_words[c+1]+header_parts[c+1]);assert left<right,'No whole-word intercolumn gap';cuts.append((left+right)/2)
    cuts.append(max(w['x1'] for w in words)+1)
    glyphs=[];word_glyphs=collections.defaultdict(list)
    for ordinal,c in enumerate(page.chars,1):
        if not compact(c['text']):continue
        hits=[w for w in words if center_inside(c,bbox(w))];assert len(hits)==1,'Missing/duplicate source glyph-to-word owner'
        g={'id':ident+'::glyph:'+str(ordinal),'text':c['text'],'bbox':bbox(c),'fontname':c['fontname'],'size':c['size'],'non_stroking_color':c.get('non_stroking_color'),'mcid':c.get('mcid'),'tag':c.get('tag')};glyphs.append(g);word_glyphs[hits[0]['id']].append(g['id'])
    assert collections.Counter(compact(''.join(w['text'] for w in words)))==collections.Counter(compact(''.join(c['text'] for c in page.chars))),'Whole words do not cover source glyph characters'
    ycuts=[min(w['top'] for w in source_rows[0])-1]
    for before,after in zip(source_rows,source_rows[1:]):
        low=max(w['bottom'] for w in before);high=min(w['top'] for w in after);assert low<high,'Source rows overlap';ycuts.append((low+high)/2)
    ycuts.append(max(w['bottom'] for w in source_rows[-1])+1)
    cells=[];rows=[];word_owner={};anomalies=[];unresolved=[];last_described=None
    for ri,line in enumerate(source_rows):
        rid=ident+'::observed-four-column::row:'+str(ri);rowcells=[]
        for ci in range(4):
            ws=header_parts[ci] if ri==0 else [w for w in line if w['column']==ci];b=[cuts[ci],ycuts[ri],cuts[ci+1],ycuts[ri+1]];text=' '.join(w['text'] for w in ws);native=tp.get_text_bounded(b[0],float(page.height)-b[3],b[2],float(page.height)-b[1]);assert compact(text)==compact(native),'Independent full-cell ordered text disagreement'
            cid=rid+'::column:'+str(ci);ids=[w['id'] for w in ws]
            for wid in ids:assert wid not in word_owner;word_owner[wid]=cid
            cell={'id':cid,'row':ri,'column':ci,'role':' '.join(config['header_roles'][ci]),'kind':'header' if ri==0 else 'printed_physical_cell','text':text,'source_word_ids':ids,'source_glyph_ids':[g for wid in ids for g in word_glyphs[wid]],'extraction_bbox':b,'independent_native_text':native,'independent_ordered_characters_agree':True,'source_empty_disposition':None if ids else 'Printed physical blank; no logical rowspan inferred','source_styles':[{'word_id':w['id'],'glyph_styles':[{'glyph_id':g['id'],'fontname':g['fontname'],'size':g['size'],'color':g['non_stroking_color']} for g in glyphs if g['id']in word_glyphs[w['id']]]} for w in ws]};cells.append(cell);rowcells.append(cell)
        values=[c['text'] for c in rowcells];rr={'id':rid,'source_physical_row':ri,'cells':[c['id'] for c in rowcells],'printed_values':values,'logical_merge_performed':False}
        if ri:
            if values[3]:last_described=rid
            if values[1] and not values[0] and not values[2] and not values[3]:
                rr['statute_only_line']={'preceding_described_physical_row_id':last_described,'logical_continuation_association_qualified':False,'reason':'Source preserves a statute-only physical line with other roles blank; no trustworthy TR/TD/rowspan relation. Do not merge or fill blanks.'};unresolved.append(rid)
            if baseline['physical_page']==9 and ri==1:
                assert values==['8-1743','12.04.178.2','','Safety Glazing Material Required'],'Changed known source-alignment anomaly'
                rr['source_alignment_anomaly']={'qualification':'Source-native physical placement retained exactly; intended reference-role alignment unresolved','no_value_shift_or_reinterpretation':True};anomalies.append(rid)
        rows.append(rr)
    assert set(word_owner)=={w['id'] for w in words};assert len(word_owner)==len(words)
    assert collections.Counter(compact(''.join(c['text'] for c in cells)))==collections.Counter(compact(tp.get_text_range())),'Native page characters omitted/duplicated across cells'
    old_failures=[]
    for table in baseline['tables']:
        for cell in table['cells']:
            if cell['independent_character_agreement']:continue
            b=cell['extraction_bbox'];intersecting=[w for w in words if intersects(b,bbox(w))];targets=sorted({word_owner[w['id']] for w in intersecting});assert targets,'A prior hard cell has no reconstructed source-word coverage'
            old_failures.append({'original_failed_cell':cell,'source_word_intersections':[w['id'] for w in intersecting],'reconstructed_cell_owners':targets,'original_failure_retained':True})
    source_images=[{'source_name':str(x.get('name','')),'bbox':bbox(x),'text':'[IMAGE]','pixel_extraction':False} for x in page.images];old_images=[b for b in baseline['ordered_blocks'] if b['kind']=='image_placeholder'];assert not source_images and not old_images,'Finite STO pages were image-free; unexpected source image requires explicit new qualification'
    return {'id':ident+'::observed-four-column','unit':'source_exact_physical_schedule','physical_page':baseline['physical_page'],'source_url':baseline['source_url'],'raw_sha256':baseline['raw_sha256'],'source_header_roles':[' '.join(x) for x in config['header_roles']],'column_boundaries':cuts,'row_boundaries':ycuts,'source_words':words,'source_glyphs':glyphs,'rows':rows,'cells':cells,'baseline_tables':baseline['tables'],'original_failed_cells_crosswalk':old_failures,'image_placeholders':source_images,'image_policy':'[IMAGE]; source pages have no image objects; never decode/extract/render/OCR','source_word_ownership_complete':True,'source_glyph_ownership_complete':True,'independent_full_cell_content_complete':True,'literal_printed_row_column_mapping_complete':True,'unresolved_statute_only_physical_rows':unresolved,'source_alignment_anomaly_rows':anomalies,'logical_continuation_semantics_complete':not unresolved,'reference_role_intent_complete':not anomalies,'publication_or_whole_PDF_table_semantics_complete':False}


def _canonical(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def _neutral(value,prefix):
    if isinstance(value,str):return value.replace(prefix,'{PAGE}')
    if isinstance(value,list):return [_neutral(v,prefix) for v in value]
    if isinstance(value,dict):return {k:_neutral(v,prefix) for k,v in value.items()}
    return value


def _canonical_projection(record,schedule):
    """Select the verified printed grid; retain failed detector output as diagnostics.

    Physical blanks remain independent cells. Neither this projection nor its
    row/column order asserts a logical continuation or an intended legal meaning.
    All checks finish before the caller mutates the delivered record.
    """
    assert 'canonical_structure_selection' not in record,'A canonical source representation is already selected'
    assert 'superseded_detector_diagnostics' not in record,'Detector diagnostics already superseded'
    assert record['image_placeholder_count']==0 and not schedule['image_placeholders'],'Unexpected image placeholder in pinned image-free STO region'
    fields=['tables','ordered_blocks','text','ordering','pdf_qualification']
    diagnostics={'schema_version':1,'reason':'Source-pinned physical four-column schedule supersedes inferred detector grids and their reading order; all original fields and false flags remain exact diagnostics.','raw_ref':record['raw_ref'],'raw_sha256':record['raw_sha256'],'original_record_fields':{k:copy.deepcopy(record[k]) for k in fields}}
    words={w['id']:w for w in schedule['source_words']};glyphs={g['id']:g for g in schedule['source_glyphs']}
    assert len(words)==len(schedule['source_words']) and len(glyphs)==len(schedule['source_glyphs']),'Duplicate source word/glyph identity'
    cells=[];ordered_word_ids=[];ordered_glyph_ids=[]
    for source in schedule['cells']:
        ids=source['source_word_ids'];gids=source['source_glyph_ids']
        assert all(i in words for i in ids) and all(i in glyphs for i in gids),'Canonical cell has unknown source owner'
        assert source['role']==schedule['source_header_roles'][source['column']],'Canonical printed header role changed'
        assert source['text']==' '.join(words[i]['text'] for i in ids),'Canonical cell source-word order changed'
        assert compact(source['text'])==compact(''.join(glyphs[i]['text'] for i in gids)),'Canonical cell source-glyph order changed'
        assert compact(source['text'])==compact(source['independent_native_text']),'Canonical cell differs from bounded original text'
        assert source['independent_ordered_characters_agree'] is True,'Canonical cell lacks ordered source comparison'
        ordered_word_ids.extend(ids);ordered_glyph_ids.extend(gids);b=source['extraction_bbox']
        assert all(b[0]<=words[i]['x0']<=words[i]['x1']<=b[2] and b[1]<=words[i]['top']<=words[i]['bottom']<=b[3] for i in ids),'Canonical cell cuts a source word'
        assert all(b[0]<=(glyphs[i]['bbox'][0]+glyphs[i]['bbox'][2])/2<=b[2] and b[1]<=(glyphs[i]['bbox'][1]+glyphs[i]['bbox'][3])/2<=b[3] for i in gids),'Canonical glyph lies outside its source cell'
        if source['row']==0:assert source['kind']=='header' and source['text']==source['role'],'Canonical header text/role disagreement'
        cells.append({'id':source['id'],'bbox':[round(v,3) for v in b],'extraction_bbox':copy.deepcopy(b),'row':source['row'],'column':source['column'],'rowspan':1,'colspan':1,'kind':source['kind'],'role':source['role'],'text':source['text'],'word_ids':copy.deepcopy(ids),'source_glyph_ids':copy.deepcopy(gids),'independent_pdfium_text':source['independent_native_text'],'qualified_pdfium_text':source['independent_native_text'],'independent_character_agreement':True,'independent_ordered_characters_agree':True,'source_empty_disposition':source['source_empty_disposition'],'source_styles':copy.deepcopy(source['source_styles'])})
    assert collections.Counter(ordered_word_ids)==collections.Counter(words.keys()),'Canonical word ownership missing/duplicated'
    assert collections.Counter(ordered_glyph_ids)==collections.Counter(glyphs.keys()),'Canonical glyph ownership missing/duplicated'
    assert len(cells)==4*len(schedule['rows']) and [(c['row'],c['column']) for c in cells]==[(r,col) for r in range(len(schedule['rows'])) for col in range(4)],'Canonical printed cell order/shape changed'
    text='\n'.join('\t'.join(c['text'] for c in cells if c['row']==ri) for ri in range(len(schedule['rows'])))
    assert collections.Counter(compact(text))==collections.Counter(compact(''.join(w['text'] for w in schedule['source_words']))),'Canonical source characters lost/duplicated'
    table_id=schedule['id']+'::canonical-table';bounds=[schedule['column_boundaries'][0],schedule['row_boundaries'][0],schedule['column_boundaries'][-1],schedule['row_boundaries'][-1]]
    table={'id':table_id,'bbox':[round(v,3) for v in bounds],'extraction_bbox':bounds,'detection':'source-pinned-physical-four-column-schedule','row_boundaries':copy.deepcopy(schedule['row_boundaries']),'column_boundaries':copy.deepcopy(schedule['column_boundaries']),'header_rows':[0],'source_header_roles':copy.deepcopy(schedule['source_header_roles']),'cells':cells,'source_physical_rows':copy.deepcopy(schedule['rows']),'source_evidence_id':schedule['id'],'physical_cell_fidelity_complete':True,'logical_continuation_semantics_complete':schedule['logical_continuation_semantics_complete'],'reference_role_intent_complete':schedule['reference_role_intent_complete'],'logical_merge_performed':False}
    block={'kind':'table','id':table_id,'bbox':table['bbox'],'text':text,'word_ids':ordered_word_ids,'source_glyph_ids':ordered_glyph_ids,'source_evidence_id':schedule['id'],'reading_order':'Exact printed physical row order, then the four source header columns; blanks retained, no continuation merge or value shift'}
    q=copy.deepcopy(record['pdf_qualification']);detector_conditions={t['id']+':independent_cell_text_disagreement' for t in record['tables']}
    q['review_conditions']=[s for s in q['review_conditions'] if s not in detector_conditions]
    q.update({'detected_table_count':1,'detected_table_cells':len(cells),'independent_table_cells_agree':len(cells),'source_word_ownership_complete':True,'word_ownership_failures':[],'normalized_source_word_characters_agree':True,'source_physical_cell_fidelity_complete':True,'source_physical_logical_semantics_complete':False,'table_scope':'Authoritative source-pinned physical four-column STO grid only. Original inferred grids and all false flags remain under superseded_detector_diagnostics. Source blanks, continuation uncertainty and alignment anomaly are preserved; whole-PDF/legal semantics remain unqualified.'})
    selection={'profile':'sto_physical_schedule','source_sha256':record['raw_sha256'],'source_url':record['source_url'],'physical_page':record['physical_page'],'source_evidence_id':schedule['id'],'canonical_table_ids':[table_id],'authoritative_fields':fields,'scope':'Printed physical headers, rows, columns, source words/glyphs and blanks only; no intended legal relationship or whole-PDF semantic qualification.'}
    return {'tables':[table],'ordered_blocks':[block],'text':text,'ordering':{'method':'Source-pinned printed physical row order then four source columns; no logical row merge','gutter':None,'source_evidence_id':schedule['id'],'source_order_qualified':True,'logical_continuation_semantics_complete':schedule['logical_continuation_semantics_complete']},'pdf_qualification':q,'superseded_detector_diagnostics':diagnostics,'canonical_structure_selection':selection}


def attach_record(record,page,textpage,item,source_sha256):
    """Add a source-exact alternative physical representation only on pinned pages.

    Nonmatching source/URL/page returns without touching any ordinary record.
    A matching profile with drifted text/geometry/diagnostics fails closed.
    """
    physical=record.get('physical_page')
    if source_sha256!=SOURCE_SHA256 or item.get('url') not in SOURCE_URLS or physical not in PINS:return False
    pin=PINS[physical]
    assert record['raw_sha256']==source_sha256,'STO source-record hash mismatch'
    assert record['document_id']==item['id'] and record['source_url']==item['url']+'#page='+str(physical),'STO record ownership/source URL mismatch'
    assert float(page.width)==pin['width'] and float(page.height)==pin['height'],'STO source page geometry mismatch'
    assert hashlib.sha256(textpage.get_text_range().encode()).hexdigest()==pin['native_text_sha256'],'STO source native text fingerprint mismatch'
    assert _canonical(_neutral(record['tables'],record['id']))==pin['baseline_tables_sha256'],'STO original detector diagnostics changed'
    schedule=_reconstruct_page(page,textpage,item,{'header_roles':HEADER_ROLES},record)
    wordkeys=('text','x0','top','x1','bottom','fontname','size')
    glyphkeys=('text','bbox','fontname','size','non_stroking_color','mcid','tag')
    assert _canonical([{k:w.get(k) for k in wordkeys} for w in schedule['source_words']])==pin['word_geometry_sha256'],'STO whole-word geometry/header fingerprint changed'
    assert _canonical([{k:g.get(k) for k in glyphkeys} for g in schedule['source_glyphs']])==pin['glyph_geometry_sha256'],'STO glyph geometry/style fingerprint changed'
    assert schedule['column_boundaries']==pin['column_boundaries'] and schedule['row_boundaries']==pin['row_boundaries'],'STO exact extraction bounds changed'
    assert len(schedule['original_failed_cells_crosswalk'])==pin['failed_cells'],'STO original failed-cell evidence missing'
    assert all(re.sub(r'\s+',' ',c['text']).strip()==re.sub(r'\s+',' ',c['independent_native_text']).strip() for c in schedule['cells']),'STO independent native word spacing mismatch'
    schedule['source_binding']={'raw_sha256':source_sha256,'source_url':item['url'],'physical_page':physical,'native_text_sha256':pin['native_text_sha256'],'word_geometry_sha256':pin['word_geometry_sha256'],'glyph_geometry_sha256':pin['glyph_geometry_sha256'],'qualification':'Exact observed source bytes, page/header/word/glyph styles and full-precision row/column bounds; physical placement only.'}
    schedule['source_structure_tree']=SOURCE_STRUCTURE
    schedule['printed_source_legend']=SOURCE_LEGEND
    schedule['detector_evidence_disposition']='Original detector tables and all false cell flags remain diagnostics. New physical cells do not relabel the original detector cells.'
    projection=_canonical_projection(record,schedule)
    record.update(projection)
    record['source_physical_schedules']=[schedule]
    return True


def summary(records):
    """Report scoped physical fidelity separately; never grant whole-PDF semantics."""
    schedules=[s for r in records for s in r.get('source_physical_schedules',[])]
    if not schedules:return None
    pages=[s['physical_page'] for s in schedules]
    assert all(s['source_binding']['raw_sha256']==SOURCE_SHA256 for s in schedules),'Mixed physical schedule sources'
    assert len(pages)==len(set(pages)),'Duplicate source physical schedule page'
    return {'scope':'Exactly three source-pinned physical schedule regions, not whole-PDF/legal table semantics','source_sha256':SOURCE_SHA256,'expected_physical_pages':sorted(PINS),'observed_physical_pages':sorted(pages),'source_regions':len(schedules),'physical_data_rows':sum(len(s['rows'])-1 for s in schedules),'header_rows':len(schedules),'complete_physical_cells':sum(len(s['cells']) for s in schedules),'physical_cell_fidelity_complete':set(pages)==set(PINS) and all(s['independent_full_cell_content_complete'] and s['source_word_ownership_complete'] and s['source_glyph_ownership_complete'] for s in schedules),'unresolved_statute_only_lines':sum(len(s['unresolved_statute_only_physical_rows']) for s in schedules),'source_alignment_anomalies':sum(len(s['source_alignment_anomaly_rows']) for s in schedules),'logical_continuation_semantics_complete':all(s['logical_continuation_semantics_complete'] for s in schedules),'reference_role_intent_complete':all(s['reference_role_intent_complete'] for s in schedules),'original_failed_detector_cells_retained':sum(len(s['original_failed_cells_crosswalk']) for s in schedules),'whole_pdf_table_semantics_complete':False,'image_policy':'[IMAGE]; unchanged source image positions/ownership; no separate image download/extraction/render/OCR'}
