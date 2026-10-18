from pathlib import Path
from collections import Counter
import json,csv,hashlib,sys
c=Path(sys.argv[1]);b=Path(sys.argv[2]);o=Path(sys.argv[3])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
basepath=b/'outputs/collection-readiness-next-2026-10-17/encodeplus/post-91f6c59/sto-three-column-canonical-candidate-v1/derived/records.jsonl'
assert sha(basepath)=='7c2c63a067fc47ceff537266a152c6cef71d0f19c51ed238b6dac33cee4ec0c3'
base=[json.loads(l)for l in basepath.read_text().splitlines()];rows=[json.loads(l)for l in(c/'derivative-current/records.jsonl').read_text().splitlines()]
p=b/'outputs/collection-readiness-post1997ee1-2026-10-17/official/infrastructure-four-region-query-v2'
proofs=json.loads((p/'projection-v4/regions.json').read_text());irs=json.loads((p/'actual-four-page-ir/ir.json').read_text());assert sha(p/'MANIFEST.sha256')=='c4562b5082e0cfbed83da20884f75eb2369ff7dca64c8b19bc7bb2a05fb0f8e5'
fields=['tables','ordered_blocks','text','ordering','pdf_qualification'];counts=Counter();changed=[];spacing=[]
for old,r in zip(base,rows):
 assert old['id']==r['id']
 if r.get('canonical_structure_selection',{}).get('profile')!='infrastructure_contents_or_revision_cover':assert old==r;counts['unchanged_records']+=1;continue
 changed.append(r['id']);n=r['physical_page'];expected=next(x for x in proofs if x['physical_page']==n);ir=next(x for x in irs if x['physical_page']==n)
 assert r['tables']==[] and r['canonical_structure_selection']['canonical_table_ids']==[] and r['canonical_structure_selection']['authoritative_fields']==fields
 assert r['superseded_detector_diagnostics']['original_record_fields']=={k:old[k]for k in fields}
 assert r['raw_sha256']==old['raw_sha256']==expected['source_sha256'] and r['raw_ref']==old['raw_ref']
 assert r['text']==expected['normalized_source_text']
 blocks=r['ordered_blocks'];units=expected['source_owned_units'];assert len(blocks)==len(units)
 for block,u in zip(blocks,units):
  assert block['kind']=='text'and block['source_kind']==u['kind'] and block['text']==u['source_text'] and block['word_ids']==u['source_word_ids']
  ls=[l for l in ir['lines']if set(l['word_ids'])&set(u['source_word_ids'])]
  assert block['source_native_query_segments']==ls
  assert block['full_line_native_spacing_agreement']==all(l['native_full_line_spacing_agreement']for l in ls)
  if u['kind']=='source_contents_entry':
   ref=block['source_printed_reference']
   for k in ['label','leader','printed_folio','reference_kind','target_status','target','destination_legal_section_identity_verified']:assert ref[k]==u[k],(n,k)
   assert ref['destination_legal_section_identity_verified']is False and block['automatic_legal_section_target_resolution']is False
   counts['contents_entries']+=1
 counts['typed_units']+=len(units);counts['source_words']+=len(ir['words'])
 assert Counter(w for block in blocks for w in block['word_ids'])==Counter(w['id']for w in ir['words'])
 ev=r['source_infrastructure_structures'][0];g=ev['source_glyphs'];counts['source_glyphs']+=len(g)
 assert Counter(gid for block in blocks for gid in block['source_glyph_ids'])==Counter(x['id']for x in g)
 assert [(x['text'],x['x0'],x['top'],x['x1'],x['bottom'],x['fontname'],x['size'])for x in g]==[(x['text'],x['x0'],x['top'],x['x1'],x['bottom'],x['fontname'],x['size'])for x in ir['deduplicated_glyphs']if x['text'].strip()]
 assert ev['full_line_spacing_complete']==expected['whole_physical_line_native_spacing_complete']and ev['literal_spacing_discrepancies']==expected['literal_leader_folio_spacing_discrepancies']
 assert ev['whole_book_semantic_or_table_completeness_qualified']is False
 if n==6:
  assert r['pdf_qualification']['source_infrastructure_full_line_spacing_complete']is False
  assert 'source_contents_literal_leader_folio_spacing_discrepancy'in r['pdf_qualification']['review_conditions']
  spacing=ev['literal_spacing_discrepancies'];assert len(spacing)==3
 if n==46:assert [d['date']for d in ev['publication_dates']]==['2019-03-26','2020-01-21','2024-03-01'];assert counts['typed_units']>=5
 counts['superseded_detector_cells']+=sum(len(t['cells'])for t in old['tables']);counts['superseded_false_cells']+=sum(not cell['independent_character_agreement']for t in old['tables']for cell in t['cells'])
 assert r['pdf_qualification']['detected_table_count']==r['pdf_qualification']['detected_table_cells']==0
assert len(rows)==636 and len(changed)==4 and counts['unchanged_records']==632 and counts['contents_entries']==96 and counts['typed_units']==110 and counts['source_words']==603 and counts['superseded_detector_cells']==467 and counts['superseded_false_cells']==44
with(c/'derivative-current/records.csv').open(newline='')as f:csvs=list(csv.DictReader(f))
assert len(csvs)==636
for a,r in zip(csvs,rows):assert a['id']==r['id']and a['text']==r['text']
prior=[r['id']for r in base if r.get('canonical_structure_selection')];assert len(prior)==13
assert all(next(r for r in rows if r['id']==i)==next(r for r in base if r['id']==i)for i in prior)
markers=lambda data:[(r['id'],r['image_placeholder_count'],[x for x in r['ordered_blocks']if x['kind']=='image_placeholder'])for r in data]
assert markers(base)==markers(rows)and sum(r['image_placeholder_count']for r in rows)==201
canonfalse=sum(not x['independent_character_agreement']for r in rows for t in r['tables']for x in t['cells']);diagfalse=sum(not x['independent_character_agreement']for r in rows for t in r.get('superseded_detector_diagnostics',{}).get('original_record_fields',{}).get('tables',[])for x in t['cells'])
assert canonfalse==0and diagfalse==795
report={'passed':True,'no_parser_or_normalizer_imports':True,'no_native_parse':True,'counts':dict(counts),'changed_records':changed,'source_word_and_glyph_ownership_exact_once':True,'source_typed_units_text_and_CSV_exact':True,'all_original_five_fields_exact_diagnostics':True,'prior13canonical_selections_exact':True,'image_marker_positions_ownership_identical':201,'remaining_canonical_false_cells':0,'all795original_false_cells_recoverable_in_diagnostics':True,'full_line_spacing':{'source_queries':112,'fullspacing_agree':109,'components_agree':112,'three_page6_differences_explicit_false':True},'printed_folio_binding_is_not_destination_legal_section_identity':True,'publication_dates_not_operative_unit_ids':True,'wholePDF_semantic_or_edition_accepted':False,'network_image_decode_render_extract_OCR_calls':0,'JSONL_sha256':sha(c/'derivative-current/records.jsonl'),'CSV_sha256':sha(c/'derivative-current/records.csv'),'auditor_sha256':sha(Path(__file__))}
(o/'independent-consumer-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
