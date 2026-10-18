"""Independent four-PDFium-page actual-coordinate query audit; read-only packet.
No reconstruction import, PDFplumber parse, pixels, render, subprocess or network.
"""
import hashlib,json,sys,contextlib,socket,subprocess,base64,re,unicodedata,collections
from pathlib import Path
from unittest.mock import patch
import pypdfium2
c,o=map(Path,sys.argv[1:]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();raw=(c/'actual-four-page-ir/source.pdf').read_bytes();assert hashlib.sha256(raw).hexdigest()=='915fe1fdf8ff5da33acfce7d08637808cb57886fbbc7f157b2b81bfcf970827c';data=json.loads((c/'actual-four-page-ir/ir.json').read_text());assert [r['physical_page'] for r in data]==[2,3,6,46];calls=[];reports=[];discrepancies=[];count=collections.Counter();norm=lambda s:unicodedata.normalize('NFKC',s);space=lambda s:' '.join(norm(s).split());compact=lambda s:''.join(ch for ch in norm(s) if not ch.isspace() and ch not in '\u200b\u00ad\ufeff')
def forbidden(*a,**kw):calls.append('pixel_render_decode_or_network');raise AssertionError('Noimage/render/decode/network/subprocess')
with contextlib.ExitStack() as guard:
 for obj,names in [(pypdfium2.PdfPage,['render','get_objects']),(pypdfium2.PdfImage,['get_bitmap','extract','get_data']),(socket,['socket']),(subprocess,['run','Popen']),(base64,['b64decode'])]:
  for name in names:
   if hasattr(obj,name):guard.enter_context(patch.object(obj,name,forbidden))
 with pypdfium2.PdfDocument(raw) as doc:
  assert len(doc)==62
  for region in data:
   n=region['physical_page'];page=doc[n-1];tp=page.get_textpage();words={w['id']:w for w in region['words']};owned=[];previous=-1;linechecks=[]
   try:
    assert page.get_width()==region['width'] and page.get_height()==region['height'];assert tp.get_text_range()==region['native_text'];assert tp.count_chars()==len(region['native_glyphs'])
    for ng in region['native_glyphs']:assert tp.get_text_range(ng['index'],1)==ng['text'] and list(tp.get_charbox(ng['index']))==ng['bbox_pdf']
    for i,line in enumerate(region['lines']):
     b=line['bbox'];q=line['native_query_bbox_pdf'];expected=[b[0]-.01,region['height']-b[3]-.01,b[2]+.01,region['height']-b[1]+.01];assert q==expected and line['native_query_padding_points']==.01 and line['native_query_coordinate_system']=='PDF points [left,bottom,right,top]';native=tp.get_text_bounded(left=q[0],bottom=q[1],right=q[2],top=q[3]);assert native==line['native_query_result']==line['native_bounded_text'];assert compact(native)==compact(line['text']);ws=[words[k] for k in line['word_ids']];assert ws==sorted(ws,key=lambda w:w['x0']);assert line['text']==' '.join(w['text'] for w in ws);assert b[1]>previous;previous=b[1];assert b==[min(w['x0'] for w in ws),min(w['top'] for w in ws),max(w['x1'] for w in ws),max(w['bottom'] for w in ws)];owned+=line['word_ids'];full=space(line['text'])==space(native);assert full==line['native_full_line_spacing_agreement']
     if full:count['full_spacing_agree']+=1
     else:
      pattern=r'^(.*?)(\.{3,})(\s*)((?:A-)?[0-9]+)$';source=re.fullmatch(pattern,space(line['text']));native_parts=re.fullmatch(pattern,space(native));assert source and native_parts;assert source[1]==native_parts[1] and source[2]==native_parts[2] and source[4]==native_parts[4];discrepancies.append({'page':n,'line_index':i,'source_text':line['text'],'native_text':native,'actual_query_bbox_pdf':q,'label':source[1],'exact_literal_leader':source[2],'printed_folio':source[4],'source_leader_folio_gap':source[3],'native_leader_folio_gap':native_parts[3],'full_spacing_qualified':False,'component_spacing_qualified':True})
     count['ordered_nonspace_agree']+=1;count['full_or_component_spacing_agree']+=1;count['queries']+=1;linechecks.append({'line_index':i,'actual_query_bbox_pdf':q,'native_transcript_exact':True,'full_spacing_qualified':full})
    assert collections.Counter(owned)==collections.Counter(words.keys());reports.append({'page':n,'queries':len(linechecks),'source_words_owned_once':len(words),'source_native_glyph_metadata_matches':len(region['native_glyphs']),'lines':linechecks})
   finally:tp.close();page.close()
assert count=={'full_spacing_agree':109,'ordered_nonspace_agree':112,'full_or_component_spacing_agree':112,'queries':112};assert len(discrepancies)==3 and {x['page'] for x in discrepancies}=={6} and [x['printed_folio'] for x in discrepancies]==['A-8','A-9','A-11'];assert not calls
before=json.loads((c/'ir-before-query-correction.json').read_text());after=json.loads(json.dumps(data))
for d in after:
 for line in d['lines']:
  for key in ['native_query_bbox_pdf','native_query_coordinate_system','native_query_padding_points','native_query_result','native_full_line_spacing_agreement']:line.pop(key)
assert before==after
result={'passed':True,'source_sha256':sha(c/'actual-four-page-ir/source.pdf'),'IR_sha256':sha(c/'actual-four-page-ir/ir.json'),'PDFium_pages_opened':[2,3,6,46],'new_pdfplumber_parses':0,'counts':dict(count),'total_source_words':sum(r['source_words_owned_once'] for r in reports),'all_prior_IR_fields_exact_after_strip5metadata':True,'actual_query_coordinates_are_full_precision_expanded_PDF_rectangles':True,'page6_full_line_spacing_complete':False,'explicit_spacing_discrepancies':discrepancies,'per_page_queries':reports,'forbidden_calls':calls,'no_full62_or636_parse':True,'canonical_integration_or_legal_section_identity_qualified':False,'auditor_sha256':sha(Path(__file__))};(o/'independent-source-query-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['per_page_queries','explicit_spacing_discrepancies']}))
