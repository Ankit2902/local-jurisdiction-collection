#!/usr/bin/env python3
"""Finite exact-source TOC/date-cover projection. No PDF/image/network APIs."""
import argparse, collections, hashlib, json, pathlib, re, unicodedata
SHA = '915fe1fdf8ff5da33acfce7d08637808cb57886fbbc7f157b2b81bfcf970827c'
DOC = 'overland-required-0768ee8be4a8'
PAGES = (2, 3, 6, 46)
COUNTS = {2:191,3:211,6:182,46:19}
def need(test, message):
    if not test: raise ValueError(message)
def norm(s): return ''.join(c for c in unicodedata.normalize('NFKC', s) if not c.isspace() and c not in '\u200b\u00ad\ufeff')
def space(s): return ' '.join(unicodedata.normalize('NFKC',s).split())
def native_spacing_proof(source,native):
    if space(source)==space(native):return {'full_line_spacing_agreement':True,'component_spacing_agreement':True}
    pattern=re.compile(r'(.+?)(\.{3,})\s*((?:A-)?\d+)')
    a=pattern.fullmatch(space(source));b=pattern.fullmatch(space(native))
    need(a is not None and b is not None and space(a[1])==space(b[1]) and a[2]==b[2] and a[3]==b[3], 'Native source word spacing/component disagreement')
    return {'full_line_spacing_agreement':False,'component_spacing_agreement':True,'reason':'Literal whitespace differs only between exact dotted leader and printed folio; source serialization and both transcripts remain unchanged.'}
def sha(b): return hashlib.sha256(b).hexdigest()
def stable(v): return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',',':')).encode()
def near(a,b): return len(a)==len(b) and all(abs(x-y)<1e-8 for x,y in zip(a,b))

def validate_region(d,document_id=DOC):
    n=d['physical_page']; need(n in PAGES, 'Unqualified source page')
    need(d['source_sha256']==SHA, 'Source SHA mismatch')
    ident=document_id+f'::page:{n}'; old=d['original_record']
    need(d['record_id']==old['id']==ident and old['document_id']==document_id and old['raw_sha256']==SHA, 'Source owner mismatch')
    need(old['physical_page']==n and old['page_count']==62, 'Native page mismatch')
    q=old['pdf_qualification']; need(not q['unmapped_or_private_use_codepoints'] and not q['undecoded_cid_literals'] and not q['invalid_decoder_glyph_resolutions'], 'Unqualified source decoder')
    need(all(q[k] for k in ['source_word_ownership_complete','normalized_source_word_characters_agree','source_words_cover_deduplicated_glyph_characters','independent_text_engine_characters_agree']), 'Source text fidelity unqualified')
    words=d['words']; need(len(words)==COUNTS[n], 'Source word count mismatch')
    need([w['id'] for w in words]==[ident+f'::word:{i+1}' for i in range(len(words))], 'Missing/duplicate/reordered source word')
    by_id={w['id']:w for w in words}; glyph_counts=collections.Counter()
    for w in words:
        gs=[]
        for i,g in enumerate(d['deduplicated_glyphs']):
            if w['x0']-.001<=(g['x0']+g['x1'])/2<=w['x1']+.001 and w['top']-.001<=(g['top']+g['bottom'])/2<=w['bottom']+.001:
                glyph_counts[i]+=1;gs.append(g)
        need(norm(''.join(g['text'] for g in sorted(gs,key=lambda g:(g['x0'],g['top']))))==norm(w['text']), 'Word/glyph order or boundary mismatch')
    need(all(glyph_counts[i]==1 for i,g in enumerate(d['deduplicated_glyphs']) if not g['text'].isspace()), 'Missing/duplicate glyph ownership')
    need(collections.Counter(norm(d['native_text']))==collections.Counter(norm(''.join(g['text']for g in d['deduplicated_glyphs']))), 'Whole native glyph disagreement')
    assigned=[]; previous_top=-1
    for l in d['lines']:
        ws=[by_id[i] for i in l['word_ids']]; need(ws==sorted(ws,key=lambda w:w['x0']), 'Reordered physical line words')
        need(l['text']==' '.join(w['text']for w in ws), 'Physical line/source text mismatch')
        b=[min(w['x0']for w in ws),min(w['top']for w in ws),max(w['x1']for w in ws),max(w['bottom']for w in ws)]
        need(near(b,l['bbox']), 'Rounded/changed tight source-word boundary')
        query=[b[0]-.01,d['height']-b[3]-.01,b[2]+.01,d['height']-b[1]+.01]
        need(near(query,l.get('native_query_bbox_pdf',[])) and l.get('native_query_padding_points')==.01 and l.get('native_query_coordinate_system')=='PDF points [left,bottom,right,top]', 'Changed or falsely reported actual native query rectangle')
        need(l['native_query_result']==l['native_bounded_text'],'Independent native requery/transcript mismatch')
        spacing=native_spacing_proof(l['text'],l['native_query_result'])
        need(spacing['full_line_spacing_agreement']==l['native_full_line_spacing_agreement'],'Cached spacing proof mismatch')
        need(b[1]>previous_top,'Reordered physical source line'); previous_top=b[1]
        need(norm(l['text'])==norm(l['native_bounded_text']), 'Independent bounded native order/text mismatch')
        assigned+=l['word_ids']
    need(collections.Counter(assigned)==collections.Counter(list(by_id)),'Missing/duplicate physical line word ownership')
    tables=old['tables']; need(len(tables)==1 and tables[0]['detection']=='aligned_text_numeric_schedule','Unexpected source detector model')
    table=tables[0]; cuts=[]
    for x in table['column_boundaries'][1:-1]:
        for w in words:
            if w['x0']+1e-6<x<w['x1']-1e-6 and min(w['bottom'],table['bbox'][3])-max(w['top'],table['bbox'][1])>0:
                cuts.append({'boundary_x':x,'word_id':w['id'],'source_word':w['text'],'word_bbox':[w['x0'],w['top'],w['x1'],w['bottom']]})
    need(cuts,'No source-proven unsafe grid boundary')
    return {'source_sha256':SHA,'record_id':ident,'physical_page':n,'source_word_count':len(words),
            'whole_word_glyph_ownership_complete':True,'physical_lines_native_order_agree':True,
            'exact_native_query_rectangles_verified':True,
            'whole_physical_line_native_spacing_complete':all(l['native_full_line_spacing_agreement']for l in d['lines']),
            'source_reference_component_native_spacing_complete':True,
            'literal_leader_folio_spacing_discrepancies':[l for l in d['lines']if not l['native_full_line_spacing_agreement']],
            'original_detector':table,'original_detector_sha256':sha(stable(table)),
            'old_failed_cells':[c for c in table['cells']if not c['independent_character_agreement']],
            'unsafe_inferred_column_intersections':cuts}

def associate_contents(lines, targets):
    rows=[];pending=[]
    starts=re.compile(r'^(?:Section\s+)?\d+(?:\.\d+)*\.?\s+')
    pattern=re.compile(r'(.+?)(\.{3,})\s*((?:A-)?\d+)')
    for line in lines:
        if not pending:
            need(starts.match(line['text']), 'Unknown TOC row start/continuation')
            pending=[line]
        else:
            need(not starts.match(line['text']), 'Ambiguous missing-folio row before next entry')
            need(line['bbox'][0]>pending[0]['bbox'][0] and 0<line['bbox'][1]-pending[-1]['bbox'][1]<26,'Ambiguous wrapped-row geometry')
            pending.append(line)
        full=' '.join(l['text']for l in pending);m=pattern.fullmatch(full)
        if not m: continue
        folio=m[3];matches=targets.get(folio,[])
        rows.append({'kind':'source_contents_entry','source_text':'\n'.join(l['text']for l in pending),
                     'source_lines':pending,'source_word_ids':[i for l in pending for i in l['word_ids']],
                     'label':m[1].rstrip(),'leader':m[2],'printed_folio':folio,'reference_kind':'printed_folio',
                     'independent_comparison_scope':'Every physical source line agrees in ordered nonspace characters with its explicit expanded native_query_bbox_pdf query. Label, leader and printed-folio components also agree under collapsed whitespace; any full-line literal leader-to-folio spacing differences remain explicit.',
                     'target_status':'unique_printed_folio' if len(matches)==1 else 'unknown_folio' if not matches else 'ambiguous_folio',
                     'target':matches[0] if len(matches)==1 else None,'target_candidates':matches,
                     'destination_legal_section_identity_verified':False})
        pending=[]
    need(not pending,'Unresolved wrapped TOC row')
    return rows

def project(d, targets,document_id=DOC):
    proof=validate_region(d,document_id);n=d['physical_page'];lines=d['lines']
    if n!=46:
        need(lines[0]['text']=='TABLE OF CONTENTS','Source TOC heading mismatch')
        need(lines[-2]['text']=='Manual of Infrastructure Standards' and lines[-1]['text']==f'City of Overland Park, Public Works TOC- {n-1}','Source TOC publication/footer mismatch')
        rows=associate_contents(lines[1:-2],targets)
        need(len(rows)=={2:31,3:32,6:33}[n], 'Unexpected source TOC row count')
        units=[{'kind':'source_heading','source_text':lines[0]['text'],'source_word_ids':lines[0]['word_ids']}]+rows+[
            {'kind':'source_publication_footer','source_text':l['text'],'source_word_ids':l['word_ids']}for l in lines[-2:]]
        proof.update(classification='source_explicit_contents',source_owned_units=units,contents_entries=len(rows),
                     printed_folio_bindings_complete=all(r['target_status']=='unique_printed_folio'for r in rows))
    else:
        expected=['APPENDIX A','Small Cell Aesthetic Standards','Originally Published March 26, 2019','Revised January 21, 2020','Revised March 1, 2024']
        need([l['text']for l in lines]==expected,'Source revision cover changed/unqualified')
        proof.update(classification='exact_source_appendix_revision_cover',source_owned_units=[
            {'kind':'source_heading'if i<2 else'publication_revision_metadata','source_text':l['text'],'source_word_ids':l['word_ids'],'source_line':l} for i,l in enumerate(lines)],
            publication_dates=[{'kind':'original_publication','date':'2019-03-26'},{'kind':'revision','date':'2020-01-21'},{'kind':'revision','date':'2024-03-01'}])
    ids=[i for u in proof['source_owned_units']for i in u['source_word_ids']]
    need(collections.Counter(ids)==collections.Counter(w['id']for w in d['words']),'Reconstructed source-word loss/duplication')
    proof.update(typed_source_region_qualified=True,source_words_emitted_once=True,original_failed_cells_unchanged=True,
                 replacement_is_legal_body_table=False,legal_semantic_complete=False,
                 normalized_source_text='\n'.join(l['text']for l in lines),
                 scope='Only this exact source SHA/page/owner, complete physical text/geometry and explicit TOC or revision-cover form. Original failed detector cells retained, not made to agree or silently discarded.')
    return proof

def target_footers(records):
    out=collections.defaultdict(list)
    for d in records:
        need(d['raw_sha256']==SHA and d['document_id']==DOC,'Target source edition/owner mismatch')
        for b in d['ordered_blocks']:
            if b['bbox'][1]<=700:continue
            m=re.fullmatch(r'Page (\d+)|(A-\d+)',b['text'].strip())
            if m:
                folio=m[1]or m[2];out[folio].append({'physical_page':d['physical_page'],'record_id':d['id'],
                    'raw_sha256':SHA,'source_footer':b,'provenance':'Retained complete v3 page record/footer; no new parse of destination pages, no legal section-identity claim.'})
    return dict(out)

def main():
    p=argparse.ArgumentParser();p.add_argument('--ir',type=pathlib.Path,required=True);p.add_argument('--records',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
    need(not a.out.exists(),'Fresh output required');a.out.mkdir()
    data=json.loads(a.ir.read_text());need(tuple(d['physical_page']for d in data)==PAGES,'Four-page set mismatch')
    need(sha((a.ir.parent/'source.pdf').read_bytes())==SHA,'Actual native bytes/source SHA mismatch')
    targets=target_footers(list(map(json.loads,a.records.open())))
    results=[project(d,targets)for d in data]
    (a.out/'regions.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    (a.out/'targets.json').write_text(json.dumps(targets,ensure_ascii=False,indent=2)+'\n')
    summary={'source_sha256':SHA,'script_sha256':sha(pathlib.Path(__file__).read_bytes()),'ir_sha256':sha(a.ir.read_bytes()),'retained_records_sha256':sha(a.records.read_bytes()),
             'regions':len(results),'contents_entries':sum(d.get('contents_entries',0)for d in results),'source_words':sum(d['source_word_count']for d in results),
             'all_typed_regions_qualified':all(d['typed_source_region_qualified']for d in results),'all_words_emitted_once':all(d['source_words_emitted_once']for d in results),
             'old_failed_cells_retained':sum(len(d['old_failed_cells'])for d in results),'old_detector_cells_retained':sum(len(d['original_detector']['cells'])for d in results),
             'unknown_or_ambiguous_folios':[u for d in results for u in d['source_owned_units']if u.get('target_status')not in [None,'unique_printed_folio']],
             'source_unsafe_boundary_intersections':sum(len(d['unsafe_inferred_column_intersections'])for d in results),'legal_semantic_complete':False,
             'claim':'Finite source-exact TOC and revision-cover reconstruction, not a universal table/reading-order/semantic qualification. Full old44failed cells retained.'}
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
