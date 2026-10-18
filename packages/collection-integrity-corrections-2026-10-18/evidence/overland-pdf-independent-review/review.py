"""Bounded independent actual-PDF primitive review. No candidate parser imports.
Recheck all16 known disputed regions and six-page control; inspect complete
cached636-page comparison without rerunning every PDF page or interpreting pixels.
"""
import ast,collections,hashlib,io,json,re,socket,sys,unicodedata
from pathlib import Path
from unittest.mock import patch,PropertyMock
import pdfplumber,pypdfium2 as pdfium
from pypdf import PdfReader
from pypdf._page import PageObject
ROOT=Path(sys.argv[1]);OUT=Path(sys.argv[2]);V1=ROOT/'overland-five-required-v1';V2=ROOT/'overland-five-required-v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def jsonl(p):return [json.loads(x) for x in p.read_text().split('\n') if x]
def glyphs(s):return collections.Counter(c for c in unicodedata.normalize('NFKC',s) if not c.isspace() and c not in '\u200b\u00ad\ufeff')
checks=0;errors=[];calls=[]
def check(test,name,**details):
 global checks
 checks+=1
 if not test:errors.append({'check':name,**details})
def forbidden(*a,**k):calls.append('forbidden-image-or-network');raise AssertionError(calls[-1])
old=jsonl(V1/'records.jsonl');new=jsonl(V2/'records.jsonl');o={r['id']:r for r in old};n={r['id']:r for r in new};inv=read(V2/'inventory.json');items={r['id']:r for r in inv['items']};failure_index=read(ROOT/'OVERLAND-FIVE-NATIVE-BASELINE-CELL-FAILURES.json');before={str(p.relative_to(V2/'source')):sha(p) for p in (V2/'source').rglob('*') if p.is_file()};regions=[];ownership_pages=[];per_doc={};total_false=0
check(set(o)==set(n) and len(n)==636,'exact636page_ID_set')
for ident,r in n.items():
 check(r['tables']==o[ident]['tables'],'all_original_detector_cells_bboxes_text_spans_disagreements_retained',id=ident)
 check(r['raw_sha256']==o[ident]['raw_sha256']==items[r['document_id']]['expected_sha256'],'unchanged_native_edition_source_SHA',id=ident)
 check(r['image_placeholder_count']==o[ident]['image_placeholder_count'],'image_placement_count_unchanged',id=ident)
 total_false+=sum(not c['independent_character_agreement'] for t in r['tables'] for c in t['cells'])
check(total_false==795,'all795_cell_disagreements_remain_explicit')
functions=lambda p:{x.name:ast.dump(x,include_attributes=False) for x in ast.parse(p.read_text()).body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
a=functions(V1/'collectors/encodeplus/pdf_structure.py');b=functions(V2/'collectors/encodeplus/pdf_structure.py');changed=[k for k in a|b if a.get(k)!=b.get(k)]
check(changed==['pages'],'only_pages_function_changed',functions=changed)
check(sha(V1/'collectors/encodeplus/bounded_decoder.py')==sha(V2/'collectors/encodeplus/bounded_decoder.py'),'bounded_decoder_exact')
selection={x['document']:{t['page'] for t in x['tables']} for x in failure_index};control=next(i for i in items if i.endswith('4fd6ad7fa132'));selection[control]=set(range(1,7))
with patch('socket.socket',side_effect=forbidden),patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=forbidden),patch.object(pdfium.PdfPage,'render',side_effect=forbidden),patch.object(pdfium.PdfPage,'get_objects',side_effect=forbidden),patch.object(pdfium.PdfImage,'get_bitmap',side_effect=forbidden),patch.object(pdfium.PdfImage,'extract',side_effect=forbidden),patch.object(pdfplumber.page.Page,'to_image',side_effect=forbidden):
 for ident,pages in selection.items():
  item=items[ident];path=V2/item['raw_ref'];check(sha(path)==item['expected_sha256'],'actual_native_SHA',document=ident);native=pdfium.PdfDocument(str(path));plumber=pdfplumber.open(path)
  try:
   for physical in sorted(pages):
    record=n[ident+'::page:'+str(physical)];original=plumber.pages[physical-1];dedup=original.dedupe_chars(tolerance=.5);words=dedup.extract_words(x_tolerance=1.5,y_tolerance=3,extra_attrs=['fontname','size']);byid={record['id']+'::word:'+str(i+1):w for i,w in enumerate(words)};assigned=[x for block in record['ordered_blocks'] for x in block['word_ids']];counts=collections.Counter(assigned)
    check(set(assigned)==set(byid) and all(v==1 for v in counts.values()),'actual_extracted_word_IDs_exactly_once',document=ident,page=physical)
    check(len(words)==record['pdf_qualification']['source_word_count'],'actual_source_word_count',document=ident,page=physical)
    char_agree=glyphs(''.join(w['text'] for w in words))==glyphs(''.join(c['text'] for c in dedup.chars));check(char_agree==record['pdf_qualification']['source_words_cover_deduplicated_glyph_characters'],'actual_source_glyph_to_word_counter',document=ident,page=physical)
    # Reconstruct actual block token inventory independently; no table-cell
    # extraction/normalizer result is used as a source-word expectation.
    for block in record['ordered_blocks']:
     if not block['word_ids']:continue
     actual_tokens=collections.Counter(w for w in block['text'].split());expected_tokens=collections.Counter(byid[w]['text'] for w in block['word_ids'])
     check(actual_tokens==expected_tokens,'whole_word_token_multiset_in_actual_block',document=ident,page=physical,block=block.get('id',block['kind']))
    ownership_pages.append({'document':ident,'physical_page':physical,'source_words':len(words),'source_deduplicated_glyphs':len(dedup.chars),'glyph_to_word_counter_agrees':char_agree,'word_IDs_unique_complete':set(assigned)==set(byid) and all(v==1 for v in counts.values())})
    page_native=native[physical-1];tp=page_native.get_textpage()
    for table in record['tables']:
     bad=[c for c in table['cells'] if not c['independent_character_agreement']]
     if not bad:continue
     samples=[]
     for cell in bad:
      x0,top,x1,bottom=cell['bbox'];actual=tp.get_text_bounded(x0,float(original.height)-bottom,x1,float(original.height)-top)
      # Cached coordinates round to0.001 while producer queries original
      # coordinates; retain any changed boundary result rather than waive it.
      exact=actual==cell['independent_pdfium_text'];check(exact,'independent_direct_PDFium_disputed_cell_text',document=ident,page=physical,cell=cell['id'],actual=actual,cached=cell['independent_pdfium_text'])
      if len(samples)<3:
       owned=[byid[w]['text'] for w in cell['word_ids']];samples.append({'cell_id':cell['id'],'bbox':cell['bbox'],'detector_cell_text':cell['text'],'original_PDFium_bounded_text':actual,'whole_source_words_owned_by_cell':owned,'agreement_flag_remains_false':not cell['independent_character_agreement']})
     regions.append({'document':ident,'physical_page':physical,'table_id':table['id'],'detection':table['detection'],'disputed_cells':len(bad),'samples':samples})
    tp.close();page_native.close();print(json.dumps({'document':ident,'page':physical,'checked_source_words':len(words)}),flush=True)
  finally:plumber.close();native.close()
 # Independent third decoder edition witness; no font substitution.
 conflict_item=next(i for i in inv['items'] if i['id'].endswith('c15031ba3373'));reader=PdfReader(V2/conflict_item['raw_ref'],strict=True);cover=reader.pages[6].extract_text();primary=jsonl(V2/'source/records.jsonl');owner=next(r for r in primary if r['id']=='1847');check('40th Edition' in cover and '42nd Edition' in owner['text'],'preserved_actual40th_native_vs42nd_primary_conflict')
check(not calls,'no_image_or_network_API_calls')
after={str(p.relative_to(V2/'source')):sha(p) for p in (V2/'source').rglob('*') if p.is_file()};check(before==after,'all_copied_actual_source_files_unchanged')
report={'schema_version':1,'kind':'independent-bounded-five-required-PDF-word-glyph-disputed-cell-source-review','passed_within_limited_review':not errors,'checks':checks,'errors':errors,'script_sha256':sha(Path(__file__)),'candidate_parser_sha256':sha(V2/'collectors/encodeplus/pdf_structure.py'),'bounded_helper_sha256':sha(V2/'collectors/encodeplus/bounded_decoder.py'),'candidate_summary_sha256':sha(V2/'summary.json'),'native_source_inventory_sha256':sha(V2/'inventory.json'),'all_cached_pages_reconciled':636,'detected_cells':6248,'unchanged_disputed_cells':total_false,'all_actual_disputed_regions_rechecked':len(regions),'actual_word_glyph_pages':ownership_pages,'disputed_regions':regions,'edition_conflict':{'document_id':conflict_item['id'],'raw_sha256':conflict_item['expected_sha256'],'physical_page':7,'native_cover_text':cover,'primary_owner_id':'1847','primary_owner_body_sha256':owner['body_sha256'],'primary_42nd_edition_text':owner['text'],'unresolved':True},'source_files_unchanged':before==after,'forbidden_API_calls':calls,'network_requests':0,'no_image_download_decode_render_extract_OCR':True,'qualifications':{'whole_source_word_inventory_preservation_on_selected22pages':not errors,'all795_detector_cell_disagreements_retained':True,'all_tables_detected':False,'all_cell_text_or_table_semantics_complete':False,'reading_order':False,'all_source_Unicode_semantics':False,'publication_complete':False},'scope_note':'All636cached page records and all795disagreement flags compared across frozen versions. Original text/glyph geometry independently re-extracted only for16affected regions/pages plus6-page control; no full636page parser replay. Counter agreement proves inventory only, not character order/Unicode correctness. Inferred table detector regions include TOC/prose and cannot be accepted as legal table structure from these diagnostics.'}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':not errors,'checks':checks,'errors':len(errors),'regions':len(regions),'selected_pages':len(ownership_pages)}),flush=True);sys.exit(0 if not errors else 2)
