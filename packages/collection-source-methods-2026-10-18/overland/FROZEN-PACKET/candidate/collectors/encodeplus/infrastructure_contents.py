"""Exact-source Infrastructure TOC/revision-cover canonical projection, no pixels.

Unknown source/URL/page is a no-op; selected source drift refuses atomically.
Recomputes source words, glyph ownership and exact independent text queries.
"""
import collections,copy,hashlib,json
from .infrastructure_profile import PROFILE
from . import infrastructure_region_core as core

FIELDS=['tables','ordered_blocks','text','ordering','pdf_qualification']
SOURCE_SHA256=PROFILE['source_sha256']
PINS=PROFILE['pins']
def digest(x):return hashlib.sha256(x).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def neutral(x,doc):
    if isinstance(x,str):return x.replace(doc,'{DOC}')
    if isinstance(x,list):return[neutral(v,doc)for v in x]
    if isinstance(x,dict):return{k:neutral(v,doc)for k,v in x.items()}
    return x
def rebind(x,doc):
    if isinstance(x,str):return x.replace('{DOC}',doc)
    if isinstance(x,list):return[rebind(v,doc)for v in x]
    if isinstance(x,dict):return{k:rebind(v,doc)for k,v in x.items()}
    return x
def selected(record,item,sha):
    return sha==SOURCE_SHA256 and item.get('url')in PROFILE['urls']and record.get('physical_page')in PINS
def require(test,message):
    if not test:raise ValueError(message)
def physical_lines(words):
    rows=[]
    for w in sorted(words,key=lambda w:(w['top'],w['x0'])):
        if not rows or abs(rows[-1]['top']-w['top'])>3:rows.append({'top':w['top'],'words':[]})
        rows[-1]['words'].append(w)
    out=[]
    for row in rows:
        ws=sorted(row['words'],key=lambda w:w['x0'])
        out.append({'text':' '.join(w['text']for w in ws),'word_ids':[w['id']for w in ws],
                    'bbox':[min(w['x0']for w in ws),min(w['top']for w in ws),max(w['x1']for w in ws),max(w['bottom']for w in ws)]})
    return out
def make_ir(record,page,tp,item):
    require(page.page_number==record['physical_page'],'Actual native page differs from source owner')
    p=page.dedupe_chars(tolerance=.5)
    words=p.extract_words(x_tolerance=1.5,y_tolerance=3,extra_attrs=['fontname','size'])
    for i,w in enumerate(words):w['id']=record['id']+'::word:'+str(i+1)
    glyphs=[{k:c[k]for k in ['text','x0','top','x1','bottom','fontname','size']}for c in p.chars]
    lines=physical_lines(words)
    for line in lines:
        b=line['bbox'];h=float(p.height);q=[b[0]-.01,h-b[3]-.01,b[2]+.01,h-b[1]+.01]
        text=tp.get_text_bounded(left=q[0],bottom=q[1],right=q[2],top=q[3])
        line.update(native_bounded_text=text,native_character_agreement=collections.Counter(core.norm(line['text']))==collections.Counter(core.norm(text)),
                    native_query_bbox_pdf=q,native_query_coordinate_system='PDF points [left,bottom,right,top]',native_query_padding_points=.01,
                    native_query_result=text,native_full_line_spacing_agreement=core.space(line['text'])==core.space(text))
    return {'physical_page':record['physical_page'],'record_id':record['id'],'source_sha256':SOURCE_SHA256,'width':float(p.width),'height':float(p.height),
            'words':words,'deduplicated_glyphs':glyphs,'native_text':tp.get_text_range(),'lines':lines,'original_record':record}
def validate_binding(record,item,sha,ir):
    require('canonical_structure_selection'not in record and 'superseded_detector_diagnostics'not in record,'Existing canonical selection/diagnostics may not be overwritten')
    n=record['physical_page'];pin=PINS[n]
    require(record['raw_sha256']==sha==SOURCE_SHA256 and item.get('expected_sha256',sha)==sha,'Configured/source record hash mismatch')
    require(record['raw_ref']==item['raw_ref']and record['document_id']==item['id']and record['id']==item['id']+'::page:'+str(n),'Source/raw-reference/record owner mismatch')
    require(record['source_url']==item['url']+'#page='+str(n),'Source record URL mismatch')
    require([ir['width'],ir['height']]==[pin['width'],pin['height']],'Source page dimensions changed')
    require(digest(ir['native_text'].encode())==pin['native_text_sha256'],'Source native stream changed')
    require(digest(canonical(neutral({k:record[k]for k in FIELDS},item['id'])))==pin['baseline_fields_sha256'],'Original canonical detector fields changed')
    keys=['physical_page','width','height','words','deduplicated_glyphs','native_text','lines']
    require(digest(canonical(neutral({k:ir[k]for k in keys},item['id'])))==pin['source_geometry_sha256'],'Exact source words/glyphs/query geometry or transcript changed')
def projection(record,ir,item,sha):
    validate_binding(record,item,sha,ir)
    targets=rebind(PROFILE['target_footer_witnesses'],item['id'])
    proof=core.project(ir,targets,document_id=item['id'])
    require(len(proof['old_failed_cells'])==PINS[record['physical_page']]['old_failed_cells'],'Old failed payload count changed')
    require(len(proof['literal_leader_folio_spacing_discrepancies'])==PINS[record['physical_page']]['full_line_spacing_differences'],'Source spacing discrepancy lineage changed')
    by_word={w['id']:w for w in ir['words']};glyphs=[];word_glyphs=collections.defaultdict(list)
    for i,g in enumerate(ir['deduplicated_glyphs']):
        if not core.norm(g['text']):continue
        hits=[w for w in ir['words']if w['x0']-.001<=(g['x0']+g['x1'])/2<=w['x1']+.001 and w['top']-.001<=(g['top']+g['bottom'])/2<=w['bottom']+.001]
        require(len(hits)==1,'Source glyph has no unique whole-word owner')
        out=dict(g,id=record['id']+'::glyph:'+str(i+1),word_id=hits[0]['id']);glyphs.append(out);word_glyphs[hits[0]['id']].append(out)
    blocks=[]
    for i,u in enumerate(proof['source_owned_units']):
        ws=[by_word[k]for k in u['source_word_ids']];ids=set(u['source_word_ids']);ls=[l for l in ir['lines']if ids.intersection(l['word_ids'])]
        require(all(set(l['word_ids'])<=ids for l in ls),'Partial source physical line ownership')
        gs=[g['id']for wid in u['source_word_ids']for g in sorted(word_glyphs[wid],key=lambda g:g['x0'])]
        block={'kind':'text','id':record['id']+'::infrastructure-unit:'+str(i+1),'source_kind':u['kind'],
               'bbox':[min(w['x0']for w in ws),min(w['top']for w in ws),max(w['x1']for w in ws),max(w['bottom']for w in ws)],
               'text':u['source_text'],'word_ids':u['source_word_ids'],'source_glyph_ids':gs,'source_native_query_segments':ls,'reading_order':i+1,
               'independent_source_line_native_order_agreement':True,'full_line_native_spacing_agreement':all(l['native_full_line_spacing_agreement']for l in ls),
               'source_reference_component_spacing_agreement':True,'automatic_legal_section_target_resolution':False}
        if u['kind']=='source_contents_entry':
            block['source_printed_reference']={k:u[k]for k in ['label','leader','printed_folio','reference_kind','target_status','target','destination_legal_section_identity_verified']}
        blocks.append(block)
    assigned=[i for b in blocks for i in b['word_ids']];owned_glyphs=[i for b in blocks for i in b['source_glyph_ids']]
    require(collections.Counter(assigned)==collections.Counter(by_word.keys()),'Canonical source words lost/duplicated')
    require(collections.Counter(owned_glyphs)==collections.Counter(g['id']for g in glyphs),'Canonical source glyphs lost/duplicated')
    text='\n'.join(b['text']for b in blocks)
    require(text==proof['normalized_source_text'],'Canonical physical source order/text changed')
    require(collections.Counter(core.norm(text))==collections.Counter(core.norm(''.join(w['text']for w in ir['words']))),'Canonical source characters changed')
    diagnostics={'schema_version':1,'reason':'Exact source-explicit contents/revision-cover units supersede unsafe inferred numeric grids; all prior fields/false flags remain exact diagnostics.',
                 'raw_ref':record['raw_ref'],'raw_sha256':record['raw_sha256'],'original_record_fields':{k:copy.deepcopy(record[k])for k in FIELDS}}
    evidence_id=record['id']+'::infrastructure-source-structure';q=copy.deepcopy(record['pdf_qualification'])
    old_detector_conditions={t['id']+':independent_cell_text_disagreement'for t in record['tables']}
    q['review_conditions']=[s for s in q['review_conditions']if s not in old_detector_conditions]
    q.update(detected_table_count=0,detected_table_cells=0,independent_table_cells_agree=0,source_word_ownership_complete=True,word_ownership_failures=[],normalized_source_word_characters_agree=True,
             source_infrastructure_glyph_capture_complete=True,source_infrastructure_component_spacing_complete=True,
             source_infrastructure_full_line_spacing_complete=proof['whole_physical_line_native_spacing_complete'],
             table_scope='Only exact-source contents and appendix revision-cover units selected as non-grid text. Superseded detector tables remain diagnostics. No whole-book table/reading-order/legal semantics qualification.')
    if not proof['whole_physical_line_native_spacing_complete']:q['review_conditions'].append('source_contents_literal_leader_folio_spacing_discrepancy')
    evidence={'id':evidence_id,'source_sha256':sha,'source_url':record['source_url'],'physical_page':record['physical_page'],'classification':proof['classification'],
              'source_words':ir['words'],'source_glyphs':glyphs,'source_units':proof['source_owned_units'],'native_query_segments':ir['lines'],
              'old_failed_cell_ids':[c['id']for c in proof['old_failed_cells']],'unsafe_inferred_column_intersections':proof['unsafe_inferred_column_intersections'],
              'source_word_ownership_complete':True,'source_glyph_ownership_complete':True,'component_spacing_complete':True,
              'full_line_spacing_complete':proof['whole_physical_line_native_spacing_complete'],'literal_spacing_discrepancies':proof['literal_leader_folio_spacing_discrepancies'],
              'printed_folio_bindings_complete':proof.get('printed_folio_bindings_complete'),
              'publication_dates':proof.get('publication_dates',[]),'source_binding':PINS[record['physical_page']],
              'query_proof_manifest_sha256':PROFILE['query_proof_manifest_sha256'],'independent_review_sha256':PROFILE['independent_review_sha256'],
              'whole_book_semantic_or_table_completeness_qualified':False}
    selection={'profile':'infrastructure_contents_or_revision_cover','source_sha256':sha,'source_url':record['source_url'],'physical_page':record['physical_page'],
               'source_evidence_id':evidence_id,'canonical_table_ids':[],'authoritative_fields':FIELDS,
               'scope':'Four exact source-pinned contents/revision-cover pages only. No destination legal-section identity, other-page table detection, whole-book semantic/edition/reading-order qualification.'}
    return {'tables':[],'ordered_blocks':blocks,'text':text,'ordering':{'method':'Exact source single-column printed contents or revision-cover physical line order; native-query-qualified hanging continuations retained','gutter':None,'source_evidence_id':evidence_id,'reading_columns':1},
            'pdf_qualification':q,'superseded_detector_diagnostics':diagnostics,'canonical_structure_selection':selection,'source_infrastructure_structures':[evidence]}
def attach_record(record,page,textpage,item,source_sha256):
    if not selected(record,item,source_sha256):return False
    ir=make_ir(record,page,textpage,item);out=projection(record,ir,item,source_sha256);record.update(out);return True
def attach_retained_ir(record,ir,item,source_sha256):
    """Source-profile-checked derivative only; no fresh acquisition/parse claim."""
    if not selected(record,item,source_sha256):return False
    adjusted=rebind(neutral(copy.deepcopy(ir),core.DOC),item['id']);adjusted['original_record']=record
    out=projection(record,adjusted,item,source_sha256);record.update(out);return True
def summary(records):
    regions=[s for r in records for s in r.get('source_infrastructure_structures',[])]
    if not regions:return None
    pages=[s['physical_page']for s in regions];require(len(pages)==len(set(pages)),'Duplicate source infrastructure page')
    return {'source_sha256':SOURCE_SHA256,'expected_physical_pages':sorted(PINS),'observed_physical_pages':sorted(pages),'source_regions':len(regions),
            'finite_source_structure_complete':set(pages)==set(PINS)and all(s['source_word_ownership_complete']and s['source_glyph_ownership_complete']for s in regions),
            'contents_entries':sum(u['kind']=='source_contents_entry'for s in regions for u in s['source_units']),
            'source_words':sum(len(s['source_words'])for s in regions),'source_glyphs':sum(len(s['source_glyphs'])for s in regions),
            'source_printed_units':sum(len(s['source_units'])for s in regions),'original_failed_detector_cells_retained':sum(len(s['old_failed_cell_ids'])for s in regions),
            'literal_leader_folio_spacing_discrepancies':sum(len(s['literal_spacing_discrepancies'])for s in regions),
            'full_line_spacing_complete':all(s['full_line_spacing_complete']for s in regions),'component_spacing_complete':all(s['component_spacing_complete']for s in regions),
            'whole_book_semantic_or_table_completeness_qualified':False,'destination_legal_section_identity_qualified':False,
            'image_policy':'[IMAGE] unchanged; no separate image download, extraction, decoding, rendering or OCR'}
