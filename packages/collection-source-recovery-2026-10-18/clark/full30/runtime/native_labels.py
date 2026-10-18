"""Source-bound native PDF label projection. No network, pixels, rendering or OCR.

Only explicitly configured required attachments are eligible. Map reading order
and cross-engine equivalence are never inferred from glyph availability.
"""
import copy,hashlib,re
from urllib.parse import urldefrag
import pypdfium2


def native_label_runs(textpage,qualified_text,raw_text,height,ident):
 if len(qualified_text)!=len(raw_text):raise ValueError('Native label offset projection requires one-for-one source glyph qualification')
 if textpage.get_text_range()!=raw_text:raise ValueError('Native label source stream changed')
 glyphs=[];runs=[];offset=0;utf16_offset=0
 for line in raw_text.splitlines(keepends=True):
  body=line.rstrip('\r\n');qualified_body=qualified_text[offset:offset+len(body)];ids=[]
  for relative,char in enumerate(line):
   ci=pypdfium2.raw.FPDFText_GetCharIndexFromTextIndex(textpage,utf16_offset);utf16_offset+=len(char.encode('utf-16-le'))//2
   if char.isspace():continue
   if ci<0:raise ValueError('Native nonspace label glyph lacks source character index')
   unicode=pypdfium2.raw.FPDFText_GetUnicode(textpage,ci)
   if unicode!=ord(char) and not(char in '\ufffe\uffff\ufffd' and unicode==2 and pypdfium2.raw.FPDFText_IsHyphen(textpage,ci)==1):raise ValueError('Native label source character/index mapping disagrees')
   x0,y0,x1,y1=textpage.get_charbox(ci);gid=ident+'::glyph:'+str(ci)
   glyphs.append({'id':gid,'native_character_index':ci,'source_text_index':offset+relative,'source_codepoint':ord(char),'qualified_text':qualified_text[offset+relative],'native_unicode':unicode,'native_is_generated':bool(pypdfium2.raw.FPDFText_IsGenerated(textpage,ci)),'bbox':[x0,float(height)-y1,x1,float(height)-y0]});ids.append(gid)
  if body:runs.append({'id':ident+'::native-label-run:'+str(len(runs)+1),'text':qualified_body,'source_text_start':offset,'source_text_end':offset+len(body),'native_glyph_ids':ids,'order_scope':'Exact native text API stream order; not inferred geographic/map reading order'})
  offset+=len(line)
 if ''.join(g['qualified_text'] for g in glyphs)!=''.join(c for c in qualified_text if not c.isspace()):raise ValueError('Native label glyph projection lost/reordered source characters')
 return runs,glyphs


def project(data,item,config,required_by=(),base_records=None):
 """Return (owned native-label page records, limited qualification).

 `base_records` optionally reuses exact source-bound coordinate rows; it is not a
 substitute for acquisition provenance. Callers retain its parser/hash receipt.
 """
 import pdf_structure
 digest=hashlib.sha256(data).hexdigest();url=urldefrag(item['url'])[0]
 rules=[r for r in config.get('native_label_attachment_rules',[]) if r.get('url')==url]
 if len(rules)!=1 or rules[0].get('source_kind') not in ('map','image-document'):raise ValueError('Native label attachment lacks exact source-qualified selection rule')
 rule=rules[0]
 if rule.get('sha256') not in (None,digest):raise ValueError('Native label attachment source SHA mismatch')
 if not required_by:raise ValueError('Required native attachment has no source-owned references')
 for owner in required_by:
  if not owner.get('owner_record_id') or not owner.get('owner_document_id') or not re.fullmatch('[0-9a-f]{64}',owner.get('owner_source_sha256','')) or urldefrag(owner.get('reference_url',''))[0]!=url:raise ValueError('Required native attachment ownership/source binding incomplete')
 if base_records is None:base_records,_=pdf_structure.pages(data,item,config)
 records=copy.deepcopy(base_records);doc=pypdfium2.PdfDocument(data)
 try:
  if not len(doc) or len(doc)!=len(records):raise ValueError('Native label page inventory incomplete')
  for number,record in enumerate(records,1):
   if record.get('raw_sha256')!=digest or record.get('document_id')!=item['id'] or record.get('physical_page')!=number or record.get('page_count')!=len(doc) or urldefrag(record.get('source_url',''))[0]!=url:raise ValueError('Native label coordinate record source/page binding mismatch')
   page=doc[number-1];tp=page.get_textpage()
   try:
    if abs(page.get_width()-record.get('width',-1))>.001 or abs(page.get_height()-record.get('height',-1))>.001:raise ValueError('Native label page geometry/source binding mismatch')
    raw=record['pdfium_stream_text'];qualified=record['pdfium_qualified_comparison_text'];q=record['pdf_qualification']
    if tp.get_text_range()!=raw:raise ValueError('Native label base record does not match actual text stream')
    counts=[q.get('source_original_glyph_count'),q.get('source_deduplicated_glyph_count')]
    if any(not isinstance(c,int) or c<0 for c in counts):raise ValueError('Native label independent source glyph counts unavailable')
    no_glyph=tp.count_chars()==0 and counts==[0,0] and not raw and not qualified
    if not no_glyph and not raw.strip():raise ValueError('Native glyphs exist but no label stream; not image-policy N/A')
    runs,glyphs=([],[]) if no_glyph else native_label_runs(tp,qualified,raw,record['height'],record['id'])
    vector_map=rule['source_kind']=='map' and q.get('vector_curve_count',0)>20
    markers=[b for b in record['ordered_blocks'] if b['kind']=='image_placeholder']
    if vector_map and not any(b['id'].endswith(('::vector-illustration','::source-explicit-map')) for b in markers):
     marker={'id':record['id']+'::source-explicit-map','kind':'image_placeholder','text':'[IMAGE]','bbox':[0,0,record['width'],record['height']],'word_ids':[],'source_vector_curve_count':q['vector_curve_count'],'qualification':'Exact source-qualified map attachment rule plus complex native drawing curves; not general table-border classification.','pixel_extraction':False};markers.append(marker);record['ordered_blocks'].append(marker)
    record['source_word_serialization_text']=record['text'];record['text']='\n'.join(([qualified.rstrip('\r\n')] if qualified else [])+['[IMAGE]' for _ in markers]);record['native_label_text']=qualified;record['native_label_runs']=runs;record['native_label_glyph_geometry']=glyphs;record['required_by']=list(required_by);record['image_placeholder_count']=len(markers)
    engine_agree=q['independent_text_engine_characters_agree'];record['native_label_qualification']={'native_label_projection_complete':True,'source_proven_no_glyph_text_NA':no_glyph,'independent_native_text_engines_agree':engine_agree,'attachment_text_normalization_qualified':no_glyph or engine_agree,'remaining_native_text_qualification_gap':None if no_glyph or engine_agree else 'Native API labels retained exactly; independent engine character multiplicity differs. No equality waiver.','native_order_and_glyph_geometry_preserved':True,'inferred_map_reading_order':False,'source_kind':rule['source_kind'],'whole_vector_map_placeholder_qualified':vector_map,'graphic_transcription_required':False,'image_policy':'[IMAGE]','pixel_operations':0,'source_word_qualification_scope':'Existing pdf_qualification ownership/conservation describes separately retained source_word_serialization_text, not a claim that native API overprints equal deduplicated word text.','semantic_complete':False}
   finally:tp.close();page.close()
 finally:doc.close()
 qualification={'format':'PDF-native-labels','source_url':url,'source_sha256':digest,'pages':len(records),'required_by':list(required_by),'native_label_pages':sum(bool(r['native_label_runs']) for r in records),'source_proven_no_glyph_pages':sum(r['native_label_qualification']['source_proven_no_glyph_text_NA'] for r in records),'native_label_projection_complete':all(r['native_label_qualification']['native_label_projection_complete'] for r in records),'attachment_text_normalization_qualified':all(r['native_label_qualification']['attachment_text_normalization_qualified'] for r in records),'semantic_complete':False,'image_pixels_or_OCR':False,'source_rule':rule}
 return pdf_structure.redact_metadata(records),pdf_structure.redact_metadata(qualification)
