"""Source-proven PDFium bounded-text hyphen alias reconciliation; no pixels."""
import pypdfium2


def bounded_decoder_aliases(text, cell_bbox, resolutions, textpage, source_page, full_range_text):
    """U+0002 is accepted only as the same explicitly marked native hyphen.

    Original bounded and detector text are never changed. The caller may store
    this qualified comparison plus this exact proof, independently of semantic
    table-boundary qualification.
    """
    candidates=[]
    for recovery in resolutions:
        if recovery.get('pdfium_codepoint') not in {0xfffe,0xffff,0xfffd} or recovery.get('pdfminer_unicode') not in {'-','\u00ad','\u2010'}:
            continue
        index=recovery['pdfium_character_index']
        if index>=len(full_range_text) or ord(full_range_text[index])!=recovery['pdfium_codepoint']:
            continue
        # The native char list and range string can differ. Translate rather
        # than assume a Python string offset is an internal PDF character ID.
        utf16_index=len(full_range_text[:index].encode('utf-16-le'))//2
        native_index=pypdfium2.raw.FPDFText_GetCharIndexFromTextIndex(textpage,utf16_index)
        if native_index<0 or pypdfium2.raw.FPDFText_GetUnicode(textpage,native_index)!=2 or pypdfium2.raw.FPDFText_IsHyphen(textpage,native_index)!=1 or pypdfium2.raw.FPDFText_IsGenerated(textpage,native_index)!=0:
            continue
        x0,y0,x1,y1=textpage.get_charbox(native_index)
        b=[x0,float(source_page.height)-y1,x1,float(source_page.height)-y0]
        if any(abs(a-z)>.01 for a,z in zip(b,recovery['glyph_bbox_pdfium'])):
            continue
        if not (cell_bbox[0]<=b[0]<=b[2]<=cell_bbox[2] and cell_bbox[1]<=b[1]<=b[3]<=cell_bbox[3]):
            continue
        cx=(b[0]+b[2])/2;cy=(b[1]+b[3])/2
        same=[c for c in source_page.chars if c['x0']-.5<=cx<=c['x1']+.5 and c['top']-.5<=cy<=c['bottom']+.5]
        if len(same)!=1 or same[0]['text']!=recovery['pdfminer_unicode']:
            continue
        candidates.append({'native_character_index':native_index,'range_text_index':index,'range_codepoint':recovery['pdfium_codepoint'],'bounded_codepoint':2,'native_unicode':2,'native_is_hyphen':True,'native_is_generated':False,'pdfminer_unicode':same[0]['text'],'glyph_bbox_pdfium':b,'glyph_bbox_pdfminer':[same[0][k] for k in ['x0','top','x1','bottom']],'fontname':same[0]['fontname'],'qualification':'Same native glyph explicitly flagged as a hyphen, range noncharacter recovery and unique independent source glyph at matching physical location; bounded alias only, no general control-character substitution.'})
    # Do not guess which marker is which if the entire bounded occurrence set
    # is not accounted for by eligible source glyphs.
    if not candidates or text.count('\x02')!=len(candidates):
        return text,[]
    result=text
    for proof in sorted(candidates,key=lambda row:row['native_character_index']):
        result=result.replace('\x02',proof['pdfminer_unicode'],1)
    return result,candidates
