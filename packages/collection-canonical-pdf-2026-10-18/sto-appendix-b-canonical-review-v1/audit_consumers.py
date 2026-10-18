from pathlib import Path
import csv,gzip,hashlib,json,sys
from collections import Counter
c=Path(sys.argv[1]);o=Path(sys.argv[2]);fix=c/'candidate/collectors/encodeplus/fixtures/sto-appendix-b'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rs=[json.loads(s) for s in (c/'derived/records.jsonl').read_text().splitlines()]
base=[json.loads(s) for s in gzip.decompress((c/'source/composed-base-636.jsonl.gz').read_bytes()).decode().splitlines()]
regions=json.loads(gzip.decompress((fix/'reconstructed.json.gz').read_bytes()))['regions']
original=[json.loads(s) for s in (fix/'baseline-seven-pages.jsonl').read_text().splitlines()]
assert sha(fix/'source.pdf')=='594128464bdc6c0dd1336aa00acb93c1ecbfdc5980e4265e63d6e134df98f127'
fields=['tables','ordered_blocks','text','ordering','pdf_qualification'];counts=Counter();changed=[];raw_duplicates=[]
for old,r in zip(base,rs):
 assert r['id']==old['id']
 if r.get('canonical_structure_selection',{}).get('profile')!='sto_appendix_b':assert r==old;counts['unchanged_records']+=1;continue
 changed.append(r['id']);reg=next(x for x in regions if x['physical_page']==r['physical_page']);source={x['id']:x for x in reg['cells']}
 assert r['superseded_detector_diagnostics']['original_record_fields']=={k:old[k] for k in fields}
 assert r['superseded_detector_diagnostics']['raw_ref']==old['raw_ref'] and r['raw_ref']==old['raw_ref'] and r['raw_sha256']==old['raw_sha256']
 assert r['canonical_structure_selection']['authoritative_fields']==fields and r['canonical_structure_selection']['canonical_table_ids']==[r['tables'][0]['id']]
 assert len(r['tables'])==1;table=r['tables'][0];lines=[x for x in reg['physical_lines'] if x['kind']in ['header_top','header_bottom','printed_data_line']]
 assert table['header_rows']==([0,1]if r['physical_page']==198 else[1,2])
 assert len(table['cells'])==3*len(lines)
 for row,ln in enumerate(lines):
  for col,cid in enumerate(ln['cell_ids']):
   sc=source[cid];cc=table['cells'][3*row+col]
   for k,v in {'id':cid,'row':row,'column':col,'rowspan':1,'colspan':1,'text':sc['text'],'extraction_bbox':sc['extraction_bbox'],'word_ids':sc['source_word_ids'],'source_glyph_ids':sc['source_glyph_ids'],'independent_pdfium_text':sc['independent_native_text'],'qualified_pdfium_text':sc['independent_native_text'],'source_physical_line':sc['source_physical_line']}.items():assert cc[k]==v,(r['id'],cid,k)
   assert cc['logical_rowspan_generated'] is False and cc['independent_character_agreement']is True
   assert ' '.join(sc['text'].split())==' '.join(sc['independent_native_text'].split());counts['canonical_table_cells']+=1
 blocks=r['ordered_blocks'];logical=[]
 for ln in reg['physical_lines']:
  if ln['kind']in ['header_top','header_bottom','printed_data_line']:
   if not any(b['kind']=='table'for b in logical):logical.append({'kind':'table','text':'\n'.join('\t'.join(source[x]['text']for x in z['cell_ids'])for z in lines)})
  else:logical.append({'kind':'text','text':source[ln['cell_ids'][0]]['text']});counts[ln['kind']]+=1
 assert [(x['kind'],x['text'])for x in blocks]==[(x['kind'],x['text'])for x in logical]
 assert r['text']=='\n'.join(x['text']for x in logical)
 assert Counter(w for x in blocks for w in x['word_ids'])==Counter(w['id']for w in reg['source_words'])
 assert Counter(g for x in blocks for g in x['source_glyph_ids'])==Counter(g['id']for g in reg['source_glyphs'])
 counts['source_words']+=len(reg['source_words']);counts['source_glyphs']+=len(reg['source_glyphs'])
 if r['physical_page']!=198:assert table['cells'][0]['kind']=='printed_data_line'
 if r['physical_page']==198:assert 'reference only and is not a legal description.'in r['text'] and r['ordered_blocks'][-1]['text']=='187'
 if r['physical_page']==199:
  assert [z['text']for z in table['cells'][:3]]==['','','clearance'];assert r['text'].startswith('\t\tclearance\nSTO')
  assert not r['source_appendix_b_schedules'][0]['cross_page_continuation_witness']['canonical_text_filled_or_merged']
  vals=[[source[x]['text']for x in ln['cell_ids']]for ln in lines];raw_duplicates=[v for v in vals if v[0]=='62'];assert len(raw_duplicates)==2
 assert r['pdf_qualification']['detected_table_count']==1 and r['pdf_qualification']['detected_table_cells']==len(table['cells'])
 assert r['pdf_qualification']['source_physical_logical_semantics_complete']is False
 counts['superseded_false_cells']+=sum(not z['independent_character_agreement']for t in old['tables']for z in t['cells'])
assert len(changed)==6 and counts['unchanged_records']==630 and counts['canonical_table_cells']==723 and counts['printed_context_line']==9 and counts['printed_folio']==6 and counts['source_words']==1318 and counts['source_glyphs']==7515 and counts['superseded_false_cells']==274
with(c/'derived/records.csv').open(newline='')as f:cr=list(csv.DictReader(f))
assert len(cr)==len(rs)==636
for a,b in zip(cr,rs):assert a['id']==b['id'] and a['text']==b['text']
oldimages=[(r['id'],r['image_placeholder_count'],[b for b in r['ordered_blocks']if b['kind']=='image_placeholder'])for r in base];newimages=[(r['id'],r['image_placeholder_count'],[b for b in r['ordered_blocks']if b['kind']=='image_placeholder'])for r in rs];assert oldimages==newimages and sum(x[1]for x in newimages)==201
alloldfalse=sum(not cc['independent_character_agreement']for r in base for t in r['tables']for cc in t['cells'])
newfalse=sum(not cc['independent_character_agreement']for r in rs for t in r['tables']for cc in t['cells'])
assert alloldfalse-newfalse==274
report={'passed':True,'no_normalizer_or_parser_imports':True,'no_pdf_parse':True,'counts':dict(counts),'changed_records':changed,'canonical_CSV_uses_exact_corrected_text':True,'original_five_fields_exact_diagnostics':True,'all_old_false_cells_in_composed_base':alloldfalse,'remaining_canonical_false_cells':newfalse,'superseded_from_this_delta':274,'source_two_distinct_section62_values':raw_duplicates,'preheader_order_and_physical_blanks_preserved':True,'crosspage42_witness_without_text_merge':True,'reference_only_caveat_preserved':True,'source_word_and_glyph_ownership_exact_once':True,'image_markers_positions_ownership_identical':201,'network_image_decode_render_extract_OCR_calls':0,'derived_JSONL_sha256':sha(c/'derived/records.jsonl'),'derived_CSV_sha256':sha(c/'derived/records.csv'),'auditor_sha256':sha(Path(__file__))}
(o/'independent-consumer-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
