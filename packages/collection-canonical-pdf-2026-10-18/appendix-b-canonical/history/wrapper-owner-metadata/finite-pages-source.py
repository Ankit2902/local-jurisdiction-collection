def pages(data,item,config):
 if not data.startswith(b'%PDF-') or b'%%EOF' not in data[-1024:]:raise ValueError('Native PDF envelope incomplete')
 stream=pypdfium2.PdfDocument(data);pdf=pdfplumber.open(io.BytesIO(data));digest=hashlib.sha256(data).hexdigest();output=[]
 try:
  if not len(stream) or len(stream)!=len(pdf.pages):raise ValueError('Independent PDF page counts disagree or empty')
  for n,original in ((n,pdf.pages[n]) for n in range(197,203)):
   page=original.dedupe_chars(tolerance=.5);native=stream[n];tp=native.get_textpage();native_text=tp.get_text_range();comparable_text,decoder_resolutions=invalid_decoder_resolutions(native_text,tp,original);ident=item['id']+'::page:'+str(n+1);review=[]
   words=page.extract_words(x_tolerance=1.5,y_tolerance=3,extra_attrs=['fontname','size'])
   for i,w in enumerate(words):w['id']=ident+'::word:'+str(i+1)
   candidates,flags=table_candidates(page,words);review+=flags;tables=[];objects=[];owned=set()
   for ti,(table,method) in enumerate(candidates):
    tid=ident+'::table:'+str(ti+1);matrix=table.extract(x_tolerance=1.5,y_tolerance=3);values={}
    for ri,row in enumerate(table.rows):
     for ci,b in enumerate(row.cells):
      if b is not None and b not in values:values[b]=(matrix[ri][ci] or '')
    xs=sorted({round(v,3) for b in table.cells if b for v in [b[0],b[2]]});ys=sorted({round(v,3) for b in table.cells if b for v in [b[1],b[3]]});cells=[]
    for ci,(b,text) in enumerate(sorted(values.items(),key=lambda p:(p[0][1],p[0][0]))):
     bounded=tp.get_text_bounded(b[0],float(page.height)-b[3],b[2],float(page.height)-b[1]);ids=[w['id'] for w in words if inside(w,b) and w['id'] not in owned];owned.update(ids);qualified_bounded=bounded
     for recovery in decoder_resolutions:
      b0=recovery['glyph_bbox_pdfium'];center=((b0[0]+b0[2])/2,(b0[1]+b0[3])/2)
      if b[0]<=center[0]<=b[2] and b[1]<=center[1]<=b[3]:qualified_bounded=qualified_bounded.replace(chr(recovery['pdfium_codepoint']),recovery['pdfminer_unicode'],1)
     qualified_bounded,bounded_alias_proof=bounded_decoder_aliases(qualified_bounded,b,decoder_resolutions,tp,original,native_text)
     agree=chars(text)==chars(qualified_bounded);x0,x1=xs.index(round(b[0],3)),xs.index(round(b[2],3));y0,y1=ys.index(round(b[1],3)),ys.index(round(b[3],3));cells.append({'id':tid+'::cell:'+str(ci+1),'bbox':[round(v,3) for v in b],'extraction_bbox':[float(v) for v in b],'row':y0,'column':x0,'rowspan':y1-y0,'colspan':x1-x0,'text':text,'word_ids':ids,'independent_pdfium_text':bounded,'qualified_pdfium_text':qualified_bounded,'bounded_decoder_alias_resolutions':bounded_alias_proof,'independent_character_agreement':agree})
    if any(not c['independent_character_agreement'] for c in cells):review.append(tid+':independent_cell_text_disagreement')
    tabletext='\n'.join('\t'.join(c['text'] for c in cells if c['row']==r) for r in range(max((c['row'] for c in cells),default=-1)+1));tables.append({'id':tid,'bbox':[round(v,3) for v in table.bbox],'detection':method,'row_boundaries':ys,'column_boundaries':xs,'cells':cells});
    new_ids=[i for c in cells for i in c['word_ids']]
    if new_ids:
     word_by_id={w['id']:w for w in words};canonical_text='\n'.join(' '.join(line['text'] for line in lines([word_by_id[w] for w in c['word_ids']])) for c in cells if c['word_ids']);tables[-1]['page_text_serialization']='Each whole source word is emitted once by its unique geometry owner. Original detector cell text, bboxes and independent disagreements remain unchanged; no cell-boundary/table semantic qualification inferred.';objects.append({'kind':'table','id':tid,'bbox':[round(v,3) for v in table.bbox],'text':canonical_text,'word_ids':new_ids})
    elif tabletext.strip():tables[-1]['page_text_disposition']='Nested/overlapping detected region has no newly owned source words; cells retained as structure, its glyphs already appear in canonical parent/earlier table, not emitted twice.'
   images=[]
   for i,im in enumerate(page.images):
    b=box(im);image={'id':ident+'::image:'+str(i+1),'kind':'image_placeholder','bbox':b,'text':'[IMAGE]','word_ids':[],'source_name':image_source_name(im),'pixel_extraction':False};images.append(image);objects.append(image)
   vector_count=len(page.curves)+len(page.lines)+len(page.rects)
   if vector_count and (not words or re.search(r'\b(?:map|plan|street.?sections?)\b',item.get('heading',''),re.I) and len(page.curves)>20):
    figure={'id':ident+'::vector-illustration','kind':'image_placeholder','bbox':[0,0,float(page.width),float(page.height)],'text':'[IMAGE]','word_ids':[],'source_vector_object_count':vector_count,'pixel_extraction':False};images.append(figure);objects.append(figure)
   non_table=[w for w in words if w['id'] not in owned];blocks,ordering=order(non_table,objects,float(page.width));assigned=[i for b in blocks for i in b['word_ids']];counts=collections.Counter(assigned);missing=[w['id'] for w in words if counts[w['id']]!=1];text='\n'.join(b['text'] for b in blocks);source_words=''.join(w['text'] for w in words);normalized=text.replace('[IMAGE]','');raw_char_agree=chars(native_text)==chars(''.join(c['text'] for c in original.chars));char_agree=chars(comparable_text)==chars(''.join(c['text'] for c in original.chars));owned_agree=chars(normalized)==chars(source_words);source_glyph_agree=chars(source_words)==chars(''.join(c['text'] for c in page.chars));cid_literals=sorted(set(re.findall(r'\(cid:\d+\)',source_words)))
   if missing:review.append('missing_or_duplicate_source_word_ownership')
   if not char_agree:review.append('independent_pdfium_pdfminer_character_disagreement')
   if not owned_agree:review.append('normalized_text_source_word_character_disagreement')
   if not source_glyph_agree:review.append('source_words_do_not_cover_deduplicated_glyph_characters')
   if cid_literals:review.append('undecoded_source_CID_literals')
   bad=sorted({ord(c) for c in source_words if c=='\ufffd' or 0xe000<=ord(c)<=0xf8ff or ord(c)<32 and not c.isspace()})
   if bad:review.append('unmapped_or_private_use_glyphs')
   if not clean(source_words):review.append('image_only_or_no_extractable_legal_text')
   if len(page.curves):review.append('vector_illustration_interpretation_not_established')
   output.append({'id':ident,'document_id':item['id'],'unit':'pdf_page','heading':item['heading'],'path':[config['publication'],item['heading']],'source_url':item['url']+'#page='+str(n+1),'text':text,'pdfium_stream_text':native_text,'pdfium_qualified_comparison_text':comparable_text,'ordered_blocks':blocks,'ordering':ordering,'physical_page':n+1,'page_count':len(pdf.pages),'width':float(page.width),'height':float(page.height),'tables':tables,'links':[{k:a.get(k) for k in ['uri','title','contents','x0','top','x1','bottom'] if a.get(k) is not None} for a in page.annots or []],'assets':[],'image_placeholder_count':len(images),'image_policy':'Metadata-only raster bboxes and detected map/blank vector-page placeholders; no image pixels, rendering or OCR. General vector illustration classification and legal interpretation remain explicit review.','raw_ref':item['raw_ref'],'raw_sha256':digest,'jurisdiction':config['jurisdiction'],'state':config['state'],'publication':config['publication'],'semantic_review_required':True,'pdf_qualification':{'source_word_count':len(words),'source_words_cover_deduplicated_glyph_characters':source_glyph_agree,'undecoded_cid_literals':cid_literals,'deduplicated_overprint_character_count':len(original.chars)-len(page.chars),'source_word_ownership_complete':not missing,'word_ownership_failures':missing,'normalized_source_word_characters_agree':owned_agree,'independent_text_engine_characters_agree':char_agree,'raw_independent_text_engine_characters_agree':raw_char_agree,'invalid_decoder_glyph_resolutions':decoder_resolutions,'unmapped_or_private_use_codepoints':bad,'detected_table_count':len(tables),'detected_table_cells':sum(len(t['cells']) for t in tables),'independent_table_cells_agree':sum(c['independent_character_agreement'] for t in tables for c in t['cells']),'vector_curve_count':len(page.curves),'review_conditions':review,'table_scope':'Ruled grids and qualifying aligned numeric/use-code schedules; arbitrary borderless/non-numeric layouts and all legal semantics are not universally established.'}})
   attach_source_physical_schedule(output[-1],original,tp,item,digest)
   attach_source_printed_index(output[-1],original,tp,item,digest)
   attach_source_appendix_b(output[-1],original,tp,item,digest)
   tp.close();native.close();page.close();original.close()
 finally:pdf.close();stream.close()
 return redact_metadata(output),[]
