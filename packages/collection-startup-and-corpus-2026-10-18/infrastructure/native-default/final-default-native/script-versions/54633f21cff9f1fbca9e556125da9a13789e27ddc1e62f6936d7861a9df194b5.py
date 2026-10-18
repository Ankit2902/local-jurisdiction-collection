"""Exact source-native UPOC index reconstruction; no edition/wholebook promotion.

Recomputes native words, glyphs, field ownership and queries. Source profiles are
bound by runtime module hash; no stored normalized output is injected.
"""
import copy,hashlib,json,re,unicodedata
from collections import Counter,defaultdict
import pypdfium2.raw as pdfium_raw

PROFILES={'877c6e874d4de7873d22dd51443fd5c42169445ad2955db3836841a105a57102': {'edition': '40th/POC-3460/2024', 'expected_group_CID_placeholders': 2, 'urls': ['https://codes.opkansas.org/municipal-code/doclibrary.aspx?id=29e4fde6-8eab-4f2c-a715-8914aa24cfe0'], 'pins': {1: {'page_size': [612.0, 792.0], 'native_text_sha256': '40c2ad063e42bed47017e8d59d61e5b87eb837989ba8e0eeeeb9fbd3f0bae25c', 'baseline_tables_sha256': '8b6259431dc3b9c13cf1b53593d79b012ebf9adbd3b421a6534dae1273aa6b8f', 'region_sha256': '8bad331d45b4a5295935e404d750c1fcdadc49a71e32f6cc48a7604b84e55037', 'old_failed_cells': 204, 'words': 248, 'glyphs': 1480}, 169: {'page_size': [612.0, 792.0], 'native_text_sha256': '989acacdbe0966e913f10ecee7dbe9bfc617a2f388bb898731c0c31ade0ec549', 'baseline_tables_sha256': '6bacbeced55a17cde82fd2e249a9e691e90b9d187523bddf1faa79ab78615023', 'region_sha256': '2ffc856f50f73bdb6b6ace1d319b4c20079b96ce5470c10c2d4bb90b141821bc', 'old_failed_cells': 68, 'words': 177, 'glyphs': 2065}}}, 'bb91ec51cf00684233649d4375aaa30111e3a6908492b1a1b3d862271662f0b2': {'edition': '42nd/POC-3529/2026', 'expected_group_CID_placeholders': 0, 'urls': ['https://codes.opkansas.org/municipal-code/doclibrary.aspx?id=9de1d37e-6388-41d6-b7b1-53865afebe6a', 'https://online.encodeplus.com/regs/overlandpark-ks/doclibrary.aspx?id=9de1d37e-6388-41d6-b7b1-53865afebe6a'], 'pins': {1: {'page_size': [612.0, 792.0], 'native_text_sha256': 'daef5da741a964858a60fe36737a402d3e70f2f3ecfedf2613d5fafd219547ac', 'baseline_tables_sha256': '588976b2c9ac3aece06ab89294bbea1f19fcad94ef291fc61d89363aa3d4683b', 'region_sha256': '8bd9ceb3be8c98d7f18ae4845b8bef66dbe5cd1761f147bf5ec6dc3ffce58950', 'old_failed_cells': 70, 'words': 247, 'glyphs': 1474}, 169: {'page_size': [306.0, 594.0], 'native_text_sha256': '829dac9df58568422205794bedd01e48ceb62fe864171f3ab7f28d06677e1d30', 'baseline_tables_sha256': '20910bf0bc45d0d2dd4a0a77c8a927273bf30145888eebcb7d7482dea58a60e8', 'region_sha256': '767e9c1ef91b85757cf0e688781cc680bbb3914b1cc0262ee8df4b8bb4b1dc7a', 'old_failed_cells': 75, 'words': 187, 'glyphs': 2093}}}}

def compact(s):return ''.join(c for c in unicodedata.normalize('NFKC',s) if not c.isspace() and c not in '\u200b\u00ad\ufeff')

def bbox(x):return [float(x[k]) for k in ['x0','top','x1','bottom']]

def intersects(a,b):return min(a[2],b[2])>max(a[0],b[0]) and min(a[3],b[3])>max(a[1],b[1])

def center_inside(c,b):return b[0]<=(c['x0']+c['x1'])/2<=b[2] and b[1]<=(c['top']+c['bottom'])/2<=b[3]

def lines(words):
    out=[]
    for w in sorted(words,key=lambda w:(w['top'],w['x0'])):
        if not out or abs(out[-1][0]['top']-w['top'])>3:out.append([w])
        else:out[-1].append(w)
    return [sorted(row,key=lambda w:w['x0']) for row in out]

def joined(words):return ' '.join(w['text'] for w in words)

def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def _reconstruct_page(page,tp,item,config,baseline):
    assert tp.get_text_range()==baseline['pdfium_stream_text'],'Native stream/source changed'
    assert baseline['raw_sha256']==item['expected_sha256'] and baseline['document_id']==item['id'] and baseline['source_url']==item['url']+'#page='+str(baseline['physical_page'])
    page=page.dedupe_chars(tolerance=.5);words=page.extract_words(x_tolerance=1.5,y_tolerance=3,extra_attrs=['fontname','size']);ident=baseline['id'];rows=lines(words)
    for i,w in enumerate(words):w['id']=ident+'::word:'+str(i+1)
    glyphs=[];word_glyphs=defaultdict(list)
    for i,c in enumerate(page.chars):
        if not compact(c['text']):continue
        hits=[w for w in words if center_inside(c,bbox(w))];assert len(hits)==1,'Missing/duplicate glyph-to-whole-word ownership'
        g={'id':ident+'::glyph:'+str(i+1),'text':c['text'],'bbox':bbox(c),'fontname':c['fontname'],'size':c['size'],'color':c.get('non_stroking_color'),'word_id':hits[0]['id']};glyphs.append(g);word_glyphs[hits[0]['id']].append(g)
    native_owner={}
    for ni in range(tp.count_chars()):
        code=int(pdfium_raw.FPDFText_GetUnicode(tp,ni));text=chr(code) if code else ''
        if not compact(text):continue
        nb=list(map(float,tp.get_charbox(ni)));nl=list(map(float,tp.get_charbox(ni,loose=True)));cx=(nb[0]+nb[2])/2;cy=float(page.height)-(nb[1]+nb[3])/2
        hits=[g for g in glyphs if g['bbox'][0]<=cx<=g['bbox'][2] and g['bbox'][1]<=cy<=g['bbox'][3]]
        assert len(hits)==1,('Native character has no unique source glyph owner',ni,text,nb)
        g=hits[0];assert g['id'] not in native_owner,'Duplicate native character owner';native_owner[g['id']]=ni
        g.update({'native_char_index':ni,'native_unicode':text,'native_tight_bbox':nb,'native_loose_bbox':nl,'native_unicode_agrees':compact(g['text'])==compact(text)})
    assert len(native_owner)==len(glyphs),'Native/source glyph cardinality differs'
    for w in words:
        word_glyphs[w['id']].sort(key=lambda g:g['bbox'][0]);assert compact(w['text'])==compact(''.join(g['text'] for g in word_glyphs[w['id']])),'Source word does not match its complete source glyphs'
    assert Counter(compact(''.join(w['text'] for w in words)))==Counter(compact(''.join(g['text'] for g in glyphs)))
    line_y=[]
    for i,row in enumerate(rows):
        low=min(w['top'] for w in row);high=max(w['bottom'] for w in row)
        before=max(w['bottom'] for w in rows[i-1]) if i else low-2
        after=min(w['top'] for w in rows[i+1]) if i+1<len(rows) else high+2
        assert before<low and high<after,'Overlapping printed lines require separate qualification'
        line_y.append([(before+low)/2,(high+after)/2])
    line_id={w['id']:i for i,row in enumerate(rows) for w in row};word_by={w['id']:w for w in words};glyph_by={g['id']:g for g in glyphs}
    units=[];unit_word_owner={};glyph_owner={};segments=[];current_group=None;pending=[]
    main_left=min(w['x0'] for w in words);group_cids=0
    def make_unit(kind,rids,roles=None,group=None):
        nonlocal group_cids
        ws=[w for ri in rids for w in rows[ri]];uid=ident+'::printed-index-unit:'+str(len(units)+1)
        for w in ws:assert w['id'] not in unit_word_owner;unit_word_owner[w['id']]=uid
        gs=[g for w in ws for g in word_glyphs[w['id']]]
        unicode_ok=not any('(cid:'in g['text'] for g in gs)
        if kind=='group_heading' and not unicode_ok:group_cids+=1
        if roles is None:roles={g['id']:kind for g in gs}
        assert set(roles)=={g['id'] for g in gs}
        role_order=[]
        for g in gs:
            if roles[g['id']] not in role_order:role_order.append(roles[g['id']])
        fields=[]
        for role in role_order:
            owned=[g for g in gs if roles[g['id']]==role];fid=uid+'::field:'+role
            for g in owned:assert g['id'] not in glyph_owner;glyph_owner[g['id']]=fid
            printed=[];field_segments=[]
            for ri in rids:
                line_g=[g for w in rows[ri] for g in word_glyphs[w['id']] if roles.get(g['id'])==role]
                if not line_g:continue
                # A role must be a contiguous run on each printed line. Full native bounds use
                # source glyph edges in exact precision, with vertical cuts in empty line gaps.
                full=[g for w in rows[ri] for g in word_glyphs[w['id']]];positions=[full.index(g) for g in line_g];assert positions==list(range(min(positions),max(positions)+1))
                lo=min(g['bbox'][0] for g in line_g);hi=max(g['bbox'][2] for g in line_g)
                prev=full[min(positions)-1] if min(positions)>0 else None;nxt=full[max(positions)+1] if max(positions)+1<len(full) else None
                advance_b=[(prev['bbox'][2]+lo)/2 if prev else lo-1,line_y[ri][0],(hi+nxt['bbox'][0])/2 if nxt else hi+1,line_y[ri][1]]
                # Preserve a reproducible rectangle diagnostic, but do not invent
                # a disjoint grid: actual label/leader ink can overlap. Independent
                # character-index/geometry bijection qualifies field glyph content.
                b=advance_b;left=b[0];right=b[2];native=tp.get_text_bounded(left,float(page.height)-b[3],right,float(page.height)-b[1]);text=''.join(g['text'] for g in line_g);agree=compact(text)==compact(native)
                native_indices=[g['native_char_index'] for g in line_g];index_text=''.join(chr(int(pdfium_raw.FPDFText_GetUnicode(tp,ni))) for ni in native_indices);index_agree=compact(text)==compact(index_text)
                if unicode_ok:assert index_agree,'Independent native glyph-index sequence differs'
                else:assert kind=='group_heading','Legacy body glyph uncertainty must not become qualified entry text'
                # Preserve word spaces only where the original extractor established a word boundary.
                tokens=[]
                for w in rows[ri]:
                    tok=''.join(g['text'] for g in word_glyphs[w['id']] if roles.get(g['id'])==role)
                    if tok:tokens.append(tok)
                printed.append(' '.join(tokens));sid=fid+'::line:'+str(ri+1)
                seg={'id':sid,'source_line':ri+1,'source_glyph_ids':[g['id'] for g in line_g],'source_word_references_nonowning':list(dict.fromkeys(g['word_id'] for g in line_g)),'text':' '.join(tokens),'extraction_bbox':b,'source_advance_midpoint_bbox':advance_b,'rectangular_field_boundary_qualified':agree,'native_character_indices':native_indices,'native_index_text':index_text,'independent_native_index_characters_agree':index_agree,'source_advance_bbox_boundary_overlap_points':{'left':max(0.0,left-lo),'right':max(0.0,hi-right)},'independent_native_text':native,'independent_ordered_characters_agree':agree,'unicode_qualified':unicode_ok};segments.append(seg);field_segments.append(sid)
            fields.append({'id':fid,'role':role,'text':'\n'.join(printed),'source_glyph_ids':[g['id'] for g in owned],'source_word_references_nonowning':list(dict.fromkeys(g['word_id'] for g in owned)),'native_query_segments':field_segments,'unicode_qualified':unicode_ok,'independent_native_index_characters_agree':all(g['native_unicode_agrees'] for g in owned)})
        unit_bbox=[min(w['x0'] for w in ws)-1,line_y[rids[0]][0],max(w['x1'] for w in ws)+1,line_y[rids[-1]][1]]
        unit_native=tp.get_text_bounded(unit_bbox[0],float(page.height)-unit_bbox[3],unit_bbox[2],float(page.height)-unit_bbox[1]);printed='\n'.join(joined(rows[ri]) for ri in rids)
        unit_agree=compact(printed)==compact(unit_native)
        if unicode_ok:assert unit_agree,('Whole source entry query differs',printed,unit_native)
        unit={'id':uid,'kind':kind,'source_lines':[ri+1 for ri in rids],'reading_column':1,'reading_order':len(units)+1,'source_word_ids':[w['id'] for w in ws],'canonical_printed_text':printed,'extraction_bbox':unit_bbox,'independent_native_text':unit_native,'independent_whole_entry_characters_agree':unit_agree,'fields':fields,'printed_group_heading_unit_id':group,'unicode_qualified':unicode_ok,'group_unicode_not_inferred':not unicode_ok,'printed_line_continuation':len(rids)>1,'source_hanging_indent':11.0 if len(rids)>1 else None,'automatic_cross_reference_target_resolution':False}
        units.append(unit);return uid
    if baseline['physical_page']==1:
        assert joined(rows[0])=='CRIMINAL CODE INDEX','Printed index title changed';make_unit('index_title',[0]);start=1
        if config['edition'].startswith('42nd'):
            assert joined(rows[1])=='NEW SECTIONS FOR 2026 IN RED','Source current-edition legend changed';make_unit('printed_legend',[1]);start=2
        for ri in range(start,len(rows)):
            row=rows[ri];assert abs(row[0]['x0']-main_left)<.05,'Unexpected reading column or index wrap';seps=[i for i,w in enumerate(row) if w['text']=='-'];assert len(seps)==1,'Unique printed standalone separator required';si=seps[0];assert si>0 and len(row)>si+2 and row[si+1]['text']in ['UPOC','OPMC'] and re.fullmatch(r'\d+(?:\.\d+)*\.?',row[si+2]['text']),'Exact printed code/citation pattern required'
            remaining=row[si+3:];assert not remaining or remaining[0]['text']in ['(Previously','Previously'],'Unrecognized citation trailing content'
            roles={}
            for wi,w in enumerate(row):
                role='entry_label' if wi<si else 'printed_separator' if wi==si else 'code_family' if wi==si+1 else 'printed_section_citation' if wi==si+2 else 'printed_previous_reference_clause'
                roles.update({g['id']:role for g in word_glyphs[w['id']]})
            make_unit('index_entry',[ri],roles)
    else:
        assert baseline['physical_page']==169
        for ri,row in enumerate(rows):
            is_group=len(row)==1 and row[0]['size']>=11 and (re.fullmatch('[A-Z]',row[0]['text']) or re.fullmatch(r'\(cid:\d+\)',row[0]['text']))
            is_footer=ri==len(rows)-1 and len(row)==1 and re.fullmatch(r'\d+',row[0]['text'])
            if is_group or is_footer:
                assert not pending,'Unterminated source entry before group/footer';uid=make_unit('group_heading' if is_group else 'printed_folio',[ri]);
                if is_group:current_group=uid
                continue
            expected=main_left if not pending else main_left+11;assert abs(row[0]['x0']-expected)<.06,('Ambiguous continuation or reading column',item['id'],baseline['physical_page'],ri,joined(row),row[0]['size'],expected,joined(rows[pending[-1]]) if pending else None);pending.append(ri)
            gs=[g for k in pending for w in rows[k] for g in word_glyphs[w['id']]];stream=''.join(compact(g['text']) for g in gs);match=re.fullmatch(r'(.+?)(\.{3,})(\d+(?:\.\d+)*\.?)',stream)
            if not match:continue
            roles={};offset=0
            for g in gs:
                value=compact(g['text']);end=offset+len(value)
                role='entry_label' if end<=match.end(1) else 'printed_dot_leader' if offset>=match.end(1) and end<=match.end(2) else 'printed_section_citation' if offset>=match.end(2) else None
                assert role,'One glyph crosses a semantic boundary; cannot split/guess';roles[g['id']]=role;offset=end
            make_unit('index_entry',pending,roles,current_group);pending=[]
        assert not pending,'Missing printed leader/citation at region end'
    assert group_cids==config['expected_group_CID_placeholders'] if baseline['physical_page']==169 else group_cids==0
    assert set(unit_word_owner)==set(word_by) and len(unit_word_owner)==len(words)
    assert set(glyph_owner)==set(glyph_by) and len(glyph_owner)==len(glyphs)
    failures=[]
    for table in baseline['tables']:
        for cell in table['cells']:
            if cell['independent_character_agreement']:continue
            b=cell['extraction_bbox'];ws=[w for w in words if intersects(b,bbox(w))];gs=[g for g in glyphs if intersects(b,g['bbox'])]
            native_old=tp.get_text_bounded(b[0],float(page.height)-b[3],b[2],float(page.height)-b[1]);assert native_old==cell['independent_pdfium_text'],'Original failed-cell query must reproduce exactly'
            # Some old grids touch, rather than positively intersect, the next
            # source line because of floating point y coordinates. Retain exact
            # native replay and all source boundary contacts separately; do not
            # pretend they are corrected geometric cells or choose a text match.
            contacts=[g for g in glyphs if min(b[2],g['bbox'][2])>max(b[0],g['bbox'][0]) and min(b[3],g['bbox'][3])>=max(b[1],g['bbox'][1])-1e-6]
            assert contacts,'Original failed cell lacks even source boundary contact'
            failures.append({'original_failed_cell':cell,'original_failure_retained':True,'source_word_intersections_nonowning':[w['id'] for w in ws],'source_glyph_intersections_nonowning':[g['id'] for g in gs],'reconstructed_unit_owners':sorted({unit_word_owner[w['id']] for w in ws}),'reconstructed_field_owners':sorted({glyph_owner[g['id']] for g in gs}),'exact_native_query_replay':native_old,'source_glyph_boundary_contacts_nonowning':[g['id'] for g in contacts],'source_boundary_contact_tolerance_points':1e-6,'source_boundary_field_owners':sorted({glyph_owner[g['id']] for g in contacts}),'crosswalk_geometry_qualified':bool(ws and gs),'original_inferred_cell_semantics_qualified':False})
    assert not page.images and not [b for b in baseline['ordered_blocks'] if b['kind']=='image_placeholder'],'Changed image metadata on finite source regions'
    cid=[g for g in glyphs if '(cid:'in g['text']]
    return {'id':ident+'::printed-index-reconstruction','document_id':item['id'],'physical_page':baseline['physical_page'],'source_url':item['url'],'raw_sha256':item['expected_sha256'],'edition':config['edition'],'page_size':[float(page.width),float(page.height)],'reading_columns':[{'number':1,'source_left_margin':main_left,'proof':'Every source entry begins at this margin and all hanging continuations at +11pt; each line has exactly one terminal printed citation, or a single inline code/citation on page1. No side-by-side reading columns observed.'}],'source_words':words,'source_glyphs':glyphs,'units':units,'native_query_segments':segments,'baseline_tables':baseline['tables'],'original_failed_cells_crosswalk':failures,'source_word_ownership_complete':True,'source_glyph_ownership_complete':True,'all_known_unicode_fields_independently_reconciled':True,'all_region_unicode_qualified':not cid,'unresolved_encoded_glyphs':cid,'unresolved_encoded_glyphs_never_inferred_from_alphabetical_order':True,'image_placeholders':[],'image_policy':'[IMAGE]; original selected regions contain zero image objects/markers; no decoding, extraction, render or OCR','whole_publication_table_semantics_complete':False,'cross_edition_substitution_performed':False,'legacy_40th_vs_primary_42nd_adoption_conflict_resolved':False,'source_reading_order_preserved':True}

def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def _neutral(value,prefix,document):
    if isinstance(value,str):return value.replace(prefix,'{PAGE}').replace(document,'{DOCUMENT}')
    if isinstance(value,list):return [_neutral(v,prefix,document) for v in value]
    if isinstance(value,dict):return {k:_neutral(v,prefix,document) for k,v in value.items()}
    return value

def _region_digest(region,prefix,document):
    region=copy.deepcopy(region);region['source_url']='{SOURCE}'
    return _digest(_neutral(region,prefix,document))

def _canonical_projection(record,index):
    """Replace failed inferred grids with the actual single-column printed index.

    Old values remain exact in an explicitly superseded diagnostic container.
    This selects source reading units, not legal-reference intent or adoption.
    """
    assert 'canonical_structure_selection' not in record,'A canonical source representation is already selected'
    assert 'superseded_detector_diagnostics' not in record,'Detector diagnostics already superseded'
    fields=['tables','ordered_blocks','text','ordering','pdf_qualification']
    diagnostics={'schema_version':1,'reason':'Source-pinned printed index supersedes inferred numeric table grids and their reading order; every original field/false flag remains exact diagnostics.','raw_ref':record['raw_ref'],'raw_sha256':record['raw_sha256'],'original_record_fields':{k:copy.deepcopy(record[k]) for k in fields}}
    blocks=[]
    for unit in index['units']:
        blocks.append({'kind':'text','id':unit['id'],'source_kind':unit['kind'],'bbox':unit['extraction_bbox'],'text':unit['canonical_printed_text'],'word_ids':unit['source_word_ids'],'source_glyph_ids':[g for f in unit['fields'] for g in f['source_glyph_ids']],'source_printed_fields':unit['fields'],'source_lines':unit['source_lines'],'reading_order':unit['reading_order'],'reading_column':unit['reading_column'],'printed_line_continuation':unit['printed_line_continuation'],'source_hanging_indent':unit['source_hanging_indent'],'printed_group_heading_unit_id':unit['printed_group_heading_unit_id'],'unicode_qualified':unit['unicode_qualified'],'independent_whole_entry_characters_agree':unit['independent_whole_entry_characters_agree'],'automatic_cross_reference_target_resolution':False})
    owned=[w for block in blocks for w in block['word_ids']]
    assert Counter(owned)==Counter(w['id'] for w in index['source_words']),'Canonical index word ownership changed'
    text='\n'.join(b['text'] for b in blocks)
    assert Counter(compact(text))==Counter(compact(''.join(w['text'] for w in index['source_words']))),'Canonical index source characters changed'
    q=copy.deepcopy(record['pdf_qualification'])
    detector_conditions={t['id']+':independent_cell_text_disagreement' for t in record['tables']}
    q['review_conditions']=[s for s in q['review_conditions'] if s not in detector_conditions]
    q.update({'detected_table_count':0,'detected_table_cells':0,'independent_table_cells_agree':0,'source_word_ownership_complete':True,'word_ownership_failures':[],'normalized_source_word_characters_agree':True,'table_scope':'Source-pinned single-column printed index; no authoritative tabular grid. All superseded inferred grids/false flags remain under superseded_detector_diagnostics. Whole-PDF table/legal semantics remain unqualified.','source_index_glyph_capture_complete':True,'source_index_unicode_complete':index['all_region_unicode_qualified'],'source_index_rectangle_boundaries_complete':all(s['rectangular_field_boundary_qualified'] for s in index['native_query_segments'])})
    if not q['source_index_unicode_complete']:q['review_conditions'].append('source_index_CID_heading_unqualified')
    if not q['source_index_rectangle_boundaries_complete']:q['review_conditions'].append('source_index_rectangular_field_boundary_unqualified')
    selection={'profile':'upoc_printed_index','source_sha256':record['raw_sha256'],'source_url':record['source_url'],'physical_page':record['physical_page'],'source_evidence_id':index['id'],'canonical_table_ids':[],'authoritative_fields':fields,'scope':'Printed entry/heading/legend/folio order and fields only; no whole-book/legal intent/adoption qualification.'}
    return {'tables':[],'ordered_blocks':blocks,'text':text,'ordering':{'method':'Source-pinned single printed index column; original printed-unit order with native-query-qualified hanging continuations; headings and folios retained','gutter':None,'source_evidence_id':index['id'],'reading_columns':index['reading_columns']},'pdf_qualification':q,'superseded_detector_diagnostics':diagnostics,'canonical_structure_selection':selection}


def attach_record(record,page,textpage,item,source_sha256):
    """Add finite index evidence. Unknown profile is no-op; selected drift refuses."""
    profile=PROFILES.get(source_sha256)
    physical=record.get('physical_page')
    if not profile or item.get('url') not in profile['urls'] or physical not in profile['pins']:return False
    pin=profile['pins'][physical]
    assert record['raw_sha256']==source_sha256,'UPOC source-record hash mismatch'
    assert item.get('expected_sha256',source_sha256)==source_sha256,'UPOC configured source hash mismatch'
    assert record['raw_ref']==item['raw_ref'],'UPOC record raw-reference ownership mismatch'
    assert record['document_id']==item['id'] and record['source_url']==item['url']+'#page='+str(physical),'UPOC record ownership/source URL mismatch'
    assert [float(page.width),float(page.height)]==pin['page_size'],'UPOC source page geometry changed'
    assert hashlib.sha256(textpage.get_text_range().encode()).hexdigest()==pin['native_text_sha256'],'UPOC native text fingerprint changed'
    assert _digest(_neutral(record['tables'],record['id'],item['id']))==pin['baseline_tables_sha256'],'UPOC detector diagnostics changed'
    source_item=dict(item,expected_sha256=source_sha256)
    index=_reconstruct_page(page,textpage,source_item,profile,record)
    assert _region_digest(index,record['id'],item['id'])==pin['region_sha256'],'UPOC full source word/glyph/style/field/geometry/diagnostic fingerprint changed'
    assert len(index['original_failed_cells_crosswalk'])==pin['old_failed_cells'],'UPOC old failed-cell evidence missing'
    index['source_binding']={'raw_sha256':source_sha256,'source_url':item['url'],'physical_page':physical,'native_text_sha256':pin['native_text_sha256'],'region_sha256':pin['region_sha256'],'qualification':'Exact source-native printed units, word/glyph/style geometry and independent native queries; CID and rectangle gaps retained.'}
    index['detector_evidence_disposition']='Original inferred detector cells and false flags remain unchanged diagnostics; index fields do not relabel detector results.'
    projection=_canonical_projection(record,index)
    record.update(projection)
    record['source_printed_indexes']=[index]
    return True

def summary(records):
    """Per-source index dimensions; never satisfy whole-PDF or edition semantics."""
    regions=[x for r in records for x in r.get('source_printed_indexes',[])]
    if not regions:return None
    groups=[]
    for digest in sorted({x['raw_sha256'] for x in regions}):
        assert digest in PROFILES,'Unknown UPOC region profile'
        xs=[x for x in regions if x['raw_sha256']==digest];pages=[x['physical_page'] for x in xs]
        assert len(pages)==len(set(pages)),'Duplicate UPOC source index page'
        assert all(x['source_binding']['raw_sha256']==digest for x in xs),'Mixed UPOC source binding'
        groups.append({'source_sha256':digest,'edition':PROFILES[digest]['edition'],'expected_physical_pages':[1,169],'observed_physical_pages':sorted(pages),'source_regions':len(xs),'source_index_glyph_capture_complete':set(pages)=={1,169} and all(x['source_word_ownership_complete'] and x['source_glyph_ownership_complete'] for x in xs),'all_region_unicode_qualified':all(x['all_region_unicode_qualified'] for x in xs),'known_unicode_field_content_reconciled':all(x['all_known_unicode_fields_independently_reconciled'] for x in xs),'rectangle_boundaries_complete':all(s['rectangular_field_boundary_qualified'] for x in xs for s in x['native_query_segments']),'index_entries':sum(u['kind']=='index_entry' for x in xs for u in x['units']),'printed_units':sum(len(x['units']) for x in xs),'source_words':sum(len(x['source_words']) for x in xs),'source_glyphs':sum(len(x['source_glyphs']) for x in xs),'fields':sum(len(u['fields']) for x in xs for u in x['units']),'unqualified_CID_headings':sum(len(x['unresolved_encoded_glyphs']) for x in xs),'known_unicode_rectangle_overlap_diagnostics':sum(not s['rectangular_field_boundary_qualified'] and s['unicode_qualified'] for x in xs for s in x['native_query_segments']),'original_failed_detector_cells_retained':sum(len(x['original_failed_cells_crosswalk']) for x in xs),'whole_book_semantic_or_edition_complete':False})
    return {'scope':'Only source-pinned UPOC physical1+169 printed indexes; not entire books or edition/adoption qualification','sources':groups,'whole_book_semantic_or_table_completeness_qualified':False,'legacy_40th_vs_primary_42nd_adoption_conflict_resolved':False,'image_policy':'[IMAGE]; original image placeholders/ownership unchanged, no separate image fetch/decode/extract/render/OCR'}
