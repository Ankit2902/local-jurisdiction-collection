"""Exact source-driven complete printable attachment; no PDF/image dependencies.

This profile is only for the retained Cleveland frontage grid. A complete linked
attachment is one document unit; a PDF physical page is never inferred a section.
"""
import copy,html,re
from common import *
from reader_utils import finish,lines

SOURCE_SHA='eb1ea94cca6abefd0a8a6645c59cc2cfac5ce704adc4b76240b1ee0f3e858c7a'
SOURCE_URL='https://export.amlegal.com/media/32eb4da1492d2ce5e4435e569daed30a1af89a42/DATAOBJECTS/0-0-0-13294.pdf'
CODE_UUID='e72333de-d88b-4f92-a990-a3aca5ab5a0f'
OWNER_DOCUMENT='0-0-0-45110'
OWNER_HEADING='§ 348.02 Frontage Features'
TITLE='Required Frontage Features'
PROFILE='cleveland-frontage-complete-printable-grid-v1'
IMAGE_POLICY='literal-[IMAGE]-no-image-fetch-v1'

def compact(value):return ''.join(c for c in value if not c.isspace())
def contains(box,x,y):return box[0]<=x<=box[2] and box[1]<=y<=box[3]
def qualify(root,a,p,source_record,family,requests):
    """Recompute text/grid/image ownership from already source-verified native IR."""
    require(a['url']==SOURCE_URL and a['sha256']==SOURCE_SHA and sha(safe(root,a['file']).read_bytes())==SOURCE_SHA,'Attachment original bytes/profile drift')
    require(family['publication_identity']['code_uuid']==CODE_UUID and source_record['document_id']==OWNER_DOCUMENT and source_record['heading']==OWNER_HEADING,'Attachment source publication/owner drift')
    require(sum(x['url']==SOURCE_URL for x in source_record['assets'])==1,'Missing/duplicate exact printable attachment reference')
    owner='attachment:'+SOURCE_SHA
    require(a['required'] is True and a['status']=='retained' and a['validation']=={'kind':'pdf','qualified':True,'pages':1} and a['normalized_pdf_owner_id']==owner and a['normalized_pdf_document_pages']==1 and a['normalized_pdf_page_ids']==[owner+':page:1'],'Incomplete full native attachment metadata')
    require(p['owner_id']==owner and p['document_id']==owner+':page:1' and type(p['page']) is int and p['page']==1 and p['source_url']==SOURCE_URL and p['image_policy']==IMAGE_POLICY,'Wrong or incomplete attachment page')
    require(family.get('pdf_semantic_text_completeness_qualified') is True and family.get('pdf_table_completeness_qualified') is True,'Missing actual standard family source qualification')
    receipts=[e for e in requests.values() if e['requested_url']==SOURCE_URL and e['op']=='binary' and e['response']['status']==200 and e['file']==a['file'] and e['sha256']==SOURCE_SHA]
    require(len(receipts)==1,'Missing exact native binary receipt')
    q=p['source_qualification'];native=p['native_source_evidence'];layout=p['layout']
    require(q.get('profile')=='single-closed-native-grid-source-wide-v1' and all(q.get(k) is True for k in ['source_text_qualified','source_tables_qualified','source_reading_order_qualified']) and not q['reasons'] and not q['unowned_or_duplicate_glyph_indices'],'Unqualified original whole-document text/grid/order')
    require(native['glyph_count']==len(native['glyphs'])==q['source_text_glyph_count']==2589 and native['unmapped_glyph_count']==0 and native['image_decode_enabled'] is False and native['image_binary_extraction_count']==layout['image_binary_extraction_count']==0,'Native glyph/image policy evidence incomplete')
    glyphs=native['glyphs'];glyphtext=''.join(g['text'] for g in glyphs);require(glyphtext==native['glyph_text'] and sha(glyphtext.encode())==native['glyph_text_sha256'],'Native glyph sequence corrupt')
    require(sha(p['text'].encode())==p['text_sha256'],'Original normalized page text corrupt')
    require(len(layout['table_candidates'])==1,'Missing/additional original grid')
    table=layout['table_candidates'][0];cells=[c for row in table['cells'] for c in row]
    require(table['row_count']==9 and table['column_count']==2 and len(table['cells'])==9 and all(len(row)==2 for row in table['cells']) and len(cells)==18,'Incomplete original grid rows/cells')
    require(table['qualification']=='ruled-grid-geometry' and not table['reasons'] and all(c['rowspan']==c['colspan']==1 for c in cells),'Unqualified/mutated original cell spans')
    require(cells[0]['text']==TITLE and all(re.match('^'+chr(97+i)+r'\.\s',cells[2+2*i]['text']) for i in range(8)),'Printed document title/table row labels changed')
    require(len(q['cells'])==18 and all(e['cell_index']==i and all(e.get(k) is True for k in ['closed_original_border','original_unicode_order_equal','unmerged_source_span']) for i,e in enumerate(q['cells'])) and q['original_edge_count']==188,'Missing original closed-border/cell qualification')
    note=q['trailing_source_note'];note_indices=note['source_glyph_indices'];require(note['kind']=='source-trailing-ordinance-note' and len(set(note_indices))==len(note_indices)==39,'Trailing source note not fully bound')
    blocks=layout['text_blocks'];require(len(blocks)==10 and len(blocks[-1]['lines'])==1,'Unknown extra source text block/structure')
    note_text=blocks[-1]['lines'][0]['text'];require(note_text=='(Ord. No. 364-16. Passed 5-2-16, eff. 5-4-16)' and compact(note_text)==note['text'],'Exact source ordinance note changed')
    nonwhite=[i for i,g in enumerate(glyphs) if compact(g['text'])];owned=[];cell_witness=[]
    for ci,c in enumerate(cells):
        indices=[i for i in nonwhite if contains(c['bbox'],glyphs[i]['x'],glyphs[i]['y'])]
        require(''.join(glyphs[i]['text'] for i in indices)==compact(c['text'].replace('[IMAGE]','')),'Cell text differs from original source glyphs')
        require(len(indices)==q['cells'][ci]['source_nonwhitespace_glyph_count'],'Cell glyph counter differs')
        owned.extend(indices);cell_witness.append({'cell_index':ci,'source_glyph_indices':indices,'bbox':c['bbox'],'text_sha256':sha(c['text'].encode()),'rowspan':1,'colspan':1})
    require(''.join(glyphs[i]['text'] for i in note_indices)==compact(note_text),'Trailing note glyph sequence differs')
    owned.extend(note_indices);require(owned==nonwhite and len(owned)==len(set(owned))==q['original_nonwhitespace_glyph_count']==2201,'Unowned/duplicate/reordered original glyphs')
    require(compact(p['text'].replace('[IMAGE]',''))==''.join(glyphs[i]['text'] for i in nonwhite),'Whole original page text not conserved')
    require(p['image_placeholder_count']==p['image_xobject_count']==len(native['image_placements'])==9 and p['text'].count('[IMAGE]')==9,'Missing original image placeholders')
    require(q['image_cell_owners']==[{'cell_indices':[2*i+1],'source_ordinal':i} for i in range(9)],'Changed source image/cell ownership')
    for i,placement in enumerate(native['image_placements']):
        cell=cells[2*i+1];box=placement['bbox'];h=layout['page_size'][3];top=[box[0],h-box[3],box[2],h-box[1]]
        require(placement['ordinal']==i and placement['placeholder']=='[IMAGE]' and cell['text']=='[IMAGE]' and cell['image_placement_ordinals']==[i] and contains(cell['bbox'],top[0],top[1]) and contains(cell['bbox'],top[2],top[3]),'Source image placement not within its exact grid cell')
    table_html='<table data-source-document="'+owner+'"><tbody>'
    for ri,row in enumerate(table['cells']):
        table_html+='<tr>'
        for ci,c in enumerate(row):table_html+='<td rowspan="1" colspan="1" data-source-cell="'+str(ri*2+ci)+'" style="white-space:pre-wrap">'+html.escape(c['text'],quote=False)+'</td>'
        table_html+='</tr>'
    table_html+='</tbody></table><p data-source-role="ordinance-note">'+html.escape(note_text,quote=False)+'</p>'
    check_html(table_html)
    return table_html,receipts[0],{'profile':PROFILE,'unit_kind':'source-explicit complete printable attachment, not inferred page/section','source_sha256':SOURCE_SHA,'source_page_ids':[p['document_id']],'source_page_count':1,'source_title':TITLE,'source_row_labels':[chr(97+i)+'.' for i in range(8)],'cell_witnesses':cell_witness,'source_ordinance_note':{'text':note_text,'source_glyph_indices':note_indices},'owned_nonwhitespace_glyph_count':2201,'source_glyph_count':2589,'source_image_placeholder_count':9,'source_image_cell_owners':q['image_cell_owners'],'source_native_metadata':{'raw_sha256':SOURCE_SHA,'physical_pages':1,'catalog_has_StructTreeRoot':False,'catalog_has_Outlines':False,'page_Annotations':None,'page_size':[612,792],'source_basis':'Bounded original PDF catalog/fonts/native text/grid inspection under no-image guards; exact bytes pin this profile'},'source_text_layout':blocks,'native_diagnostic_page_sha256':sha(canonical(p)),'original_page_legal_segmentation_flag':q.get('legal_provision_segmentation_qualified'),'scope':'Whole linked printable source document. Its a.-h. table labels remain internal rows; no independent legal sections or corrected/completed source clauses are invented.'}

def project(root,proof,family,projection):
    assets=load(root/'assets.json');matches=[a for a in assets if a['url']==SOURCE_URL]
    if not matches:return projection
    require(len(matches)==1,'Duplicate supported attachment source');a=matches[0]
    # A changed source at the same URI must never inherit this exact profile.
    require(a.get('sha256')==SOURCE_SHA,'Supported attachment URL changed native source; requalification required')
    records=lines(root/'sections.jsonl');owners=[r for r in records if any(x['url']==SOURCE_URL for x in r['assets'])]
    require(len(owners)==1,'Whole printable attachment needs one exact referring source provision')
    pages=[p for p in lines(root/'pdf-pages.jsonl') if p.get('source_url')==SOURCE_URL];require(len(pages)==1,'Missing/additional complete attachment page')
    body,receipt,witness=qualify(root,a,pages[0],owners[0],family,load(root/'requests.json'))
    aid='american-legal-asset:'+sha(SOURCE_URL.encode());ni=next(i for i,n in enumerate(projection.nodes) if n['node_id']==aid);require(projection.dispositions[ni]['disposition']=='unresolved' and not projection.dispositions[ni]['record_ids'],'Attachment inherited disposition changed')
    source_i=next(i for i,p in enumerate(projection.provenance) if p.get('source_document_id')==OWNER_DOCUMENT);parent=projection.provenance[source_i];rid='american-legal-attachment:'+SOURCE_SHA
    row=copy.deepcopy(projection.rows[source_i]);row.update(section_number='',section_name=TITLE,full_text=body,source_url=SOURCE_URL,scrape_date=receipt['retrieved_at'])
    pr={'record_id':rid,'node_ids':[aid],'source_version':parent['source_version'],'raw_artifact_path':'evidence/input/'+a['file'],'raw_sha256':SOURCE_SHA,'record_unit':'complete source-explicit linked printable attachment','same_provision_owner_record_id':parent['record_id'],'same_provision_heading':OWNER_HEADING,'source_chain':parent['source_chain'],'source_hierarchy_evidence':parent['source_hierarchy_evidence'],'source_hierarchy_conflicts':parent['source_hierarchy_conflicts'],'citation_evidence':'Exact referring source provision caption; attachment has no separate printed section number','canonical_attachment_qualification':witness,'original_normalized_page_path':'evidence/input/pdf-pages.jsonl','source_order_domain':'Whole attached document immediately follows its exact referring provision; original HTML relative order unchanged','image_policy':IMAGE_POLICY}
    projection.rows.insert(source_i+1,row);projection.provenance.insert(source_i+1,pr)
    projection.nodes[ni].update(parent_node_id=parent['record_id'],node_kind='source_explicit_complete_printable_attachment',canonical_record_unit=rid,source_reference_relation='Printable document explicitly linked by this provision; not an invented publisher TOC section')
    projection.dispositions[ni]={'node_id':aid,'disposition':'included','record_ids':[rid],'evidence':{'profile':PROFILE,'source_sha256':SOURCE_SHA,'source_owner_document_id':OWNER_DOCUMENT,'source_page_ids':[pages[0]['document_id']],'reason':'All source glyphs/grid cells/note/image placeholders project once into one explicit whole printable attachment unit'}}
    projection.exceptions=[e for e in projection.exceptions if not(e.get('kind')=='required_nonimage_source_not_canonically_projected' and e.get('asset_node_id')==aid)]
    projection.metadata.update(canonical_attachment_units=[{'record_id':rid,'source_sha256':SOURCE_SHA,'profile':PROFILE,'source_page_count':1,'unit_kind':'Complete source-explicit printable attachment'}],required_nonimage_canonical_disposition_counts={'whole_printable_documents':1,'zero_glyph_source_policy_NA':sum(n['node_kind']=='required_nonimage_document' and d['disposition']=='excluded_by_scope' for n,d in zip(projection.nodes,projection.dispositions)),'unresolved':sum(n['node_kind']=='required_nonimage_document' and d['disposition']=='unresolved' for n,d in zip(projection.nodes,projection.dispositions))},attachment_scope='Exact source-bound document profile only; original producer coverage and its false segmentation/jurisdiction flags unchanged')
    return finish(projection.publication_id,projection.rows,projection.publications,projection.nodes,projection.dispositions,projection.provenance,projection.exceptions,projection.metadata,projection.inherited_coverage)
