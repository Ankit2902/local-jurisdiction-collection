"""Preserve native API label strings/order and glyph geometry; never map pixels."""
import hashlib,re
import pypdfium2


def native_label_runs(textpage, qualified_text, raw_text, height, ident):
    if len(qualified_text)!=len(raw_text):
        raise ValueError('Native label offset projection requires one-for-one source glyph qualification')
    if textpage.get_text_range()!=raw_text:
        raise ValueError('Native label source stream changed')
    glyphs=[];runs=[];offset=0;utf16_offset=0
    for line in raw_text.splitlines(keepends=True):
        body=line.rstrip('\r\n');qualified_body=qualified_text[offset:offset+len(body)];ids=[]
        for relative,char in enumerate(line):
            ci=pypdfium2.raw.FPDFText_GetCharIndexFromTextIndex(textpage,utf16_offset)
            utf16_offset+=len(char.encode('utf-16-le'))//2
            if char.isspace():continue
            if ci<0:raise ValueError('Native nonspace label glyph lacks source character index')
            unicode=pypdfium2.raw.FPDFText_GetUnicode(textpage,ci)
            if unicode!=ord(char) and not (char in '\ufffe\uffff\ufffd' and unicode==2 and pypdfium2.raw.FPDFText_IsHyphen(textpage,ci)==1):
                raise ValueError('Native label source character/index mapping disagrees')
            x0,y0,x1,y1=textpage.get_charbox(ci);gid=ident+'::glyph:'+str(ci)
            glyphs.append({'id':gid,'native_character_index':ci,'source_text_index':offset+relative,'source_codepoint':ord(char),'qualified_text':qualified_text[offset+relative],'native_unicode':unicode,'native_is_generated':bool(pypdfium2.raw.FPDFText_IsGenerated(textpage,ci)),'bbox':[x0,float(height)-y1,x1,float(height)-y0]});ids.append(gid)
        if body:
            runs.append({'id':ident+'::native-label-run:'+str(len(runs)+1),'text':qualified_body,'source_text_start':offset,'source_text_end':offset+len(body),'native_glyph_ids':ids,'order_scope':'Exact native text API stream order; not inferred geographic/map reading order'})
        offset+=len(line)
    if ''.join(g['qualified_text'] for g in glyphs)!= ''.join(c for c in qualified_text if not c.isspace()):
        raise ValueError('Native label glyph projection lost/reordered source characters')
    return runs,glyphs


def project_record(record, textpage=None):
    # Work on caller-owned output only; source generic serialization is retained
    # as a historical/auxiliary view, never passed off as full parcel labels.
    q=record['attachment_native_text_qualification'];raw=record['pdfium_stream_text'];qualified=record['pdfium_qualified_comparison_text']
    record['source_word_serialization_text']=record['text']
    record['source_word_geometry_units']=record.pop('native_label_units')
    if q['source_no_glyph_NA_qualified']:
        if q['pdfminer_original_glyph_count'] or q['pdfminer_deduplicated_glyph_count'] or q['pdfium_native_character_count'] or raw.strip() or qualified.strip():
            raise ValueError('No-glyph applicability exemption has actual native text')
        runs=[];glyphs=[]
    else:
        if textpage is None:
            raise ValueError('Available native labels require exact source text page')
        runs,glyphs=native_label_runs(textpage,qualified,raw,record['height'],record['id'])
    owner_map=any(re.search(r'\bmap\b',(o.get('reference_context') or '')+' '+(o.get('reference_label') or ''),re.I) for o in record['required_by'])
    filename_map=bool(re.search(r'(?:^|[-_/])map\.pdf$',record['source_url'].split('#')[0],re.I))
    explicit_map=owner_map or filename_map
    # This is a declared source map plus complex native drawing curves, not a
    # generic table border/any vector path treated as an image.
    vector_map=explicit_map and record['pdf_qualification']['vector_curve_count']>20
    markers=[b for b in record['ordered_blocks'] if b['kind']=='image_placeholder']
    has_whole_vector=any(b['id'].endswith(('::vector-illustration','::source-explicit-map')) for b in markers)
    if vector_map and not has_whole_vector:
        marker={'id':record['id']+'::source-explicit-map','kind':'image_placeholder','text':'[IMAGE]','bbox':[0,0,record['width'],record['height']],'word_ids':[],'source_vector_curve_count':record['pdf_qualification']['vector_curve_count'],'qualification':'Source reference or publisher filename explicitly identifies map and native metadata has more than20drawing curves. No generic table-border classification or visual interpretation.','pixel_extraction':False}
        markers.append(marker);record['ordered_blocks'].append(marker)
    if not vector_map and any(b['id'].endswith('::source-explicit-map') for b in markers):
        raise ValueError('Earlier vector placeholder lacks explicit complex-map source qualification')
    record['native_label_runs']=runs;record['native_label_glyph_geometry']=glyphs
    record['native_label_text']=qualified
    record['text']='\n'.join(([qualified.rstrip('\r\n')] if qualified else [])+['[IMAGE]' for _ in markers])
    record['image_placeholder_count']=len(markers)
    record['text_serialization']={'method':'Native qualified text API stream preserved, followed by explicitly unordered image-policy placeholders','native_text_sha256':hashlib.sha256(qualified.encode()).hexdigest(),'native_order_and_glyph_geometry_preserved':True,'inferred_map_reading_order':False,'image_placeholder_positions':'Source metadata retained in ordered_blocks; final plain text does not infer a geographic/visual serial order','source_word_geometry_view':'Retained separately; font-size/rotation word fragmentation is not used as canonical label strings'}
    record['requested_scope_qualification']={'available_native_labels_preserved':not q['source_no_glyph_NA_qualified'],'source_proven_no_glyph_text_NA':q['source_no_glyph_NA_qualified'],'native_label_projection_complete':True,'independent_native_text_engines_agree':q['independent_native_text_engines_agree'],'attachment_text_normalization_qualified':q['source_no_glyph_NA_qualified'] or q['independent_native_text_engines_agree'],'remaining_native_text_qualification_gap':None if q['source_no_glyph_NA_qualified'] or q['independent_native_text_engines_agree'] else 'Exact native API labels/glyphs retained, but independent engine character multiplicity differs on overprinted source; no equality waiver','source_graphic_map_qualification':{'source_owner_mentions_map':owner_map,'publisher_filename_mentions_map':filename_map,'native_vector_curve_count':record['pdf_qualification']['vector_curve_count'],'whole_map_graphic_placeholder_qualified':vector_map},'graphical_content_deliberately_excluded_by_image_policy':True,'graphic_or_map_transcription_required':False,'image_policy_placeholder':'[IMAGE]','pixel_operations':0,'scope_note':'Visual/graphic/map interpretation is deliberately excluded by user instruction, not an unresolved obligation to transcribe images. Native labels are preserved independently of that exclusion.'}
    return record
