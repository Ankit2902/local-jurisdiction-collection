"""Full native source replay of 46/62/1pages; preserves every old disagreement."""
import sys
sys.dont_write_bytecode=True
import json,hashlib,socket,io
from pathlib import Path
from unittest.mock import patch
import pypdfium2
import pdf_structure
base=Path(__file__).resolve().parent;project=base.parents[2]
sha=lambda data:hashlib.sha256(data).hexdigest()
def deny(*a,**k):raise AssertionError('Forbidden network/image operation')
socket.socket.connect=deny;socket.create_connection=deny
ledger_path=project/'outputs/collection-readiness-next-2026-10-17/pdf-concrete-cell-review-ledger.json';ledger=json.loads(ledger_path.read_text())
inputs=[('fire','outputs/collection-readiness-next-2026-10-17/fire-final-retained-driver/source/raw/143515c165dfca752208.bin','outputs/collection-readiness-next-2026-10-17/fire-final-retained-replay-v3/file-1.jsonl'),('infrastructure','outputs/collection-readiness-next-2026-10-17/encodeplus/pdf-candidate-infrastructure-caf641e0/source.pdf','outputs/collection-readiness-next-2026-10-17/encodeplus/pdf-candidate-infrastructure-caf641e0/records.jsonl'),('cleveland','outputs/collection-readiness-next-2026-10-17/official-final-pdf-driver/cleveland-real-cell-study/native.pdf','outputs/collection-readiness-next-2026-10-17/official-final-pdf-driver/cleveland-real-cell-study/records.jsonl')]
implementation={p.name:sha(p.read_bytes()) for p in [base/'pdf_structure.py',base/'bounded_decoder.py']};results=[];case_results=[]
for family,native_path,record_path in inputs:
 source=project/native_path;raw=source.read_bytes();old_path=project/record_path;old=[json.loads(line) for line in old_path.read_text().split('\n') if line];meta=old[0]
 assert sha(raw)==meta['raw_sha256'];old_sha=sha(old_path.read_bytes());item={'id':meta['document_id'],'url':meta['source_url'].split('#')[0],'heading':meta['heading'],'raw_ref':meta['raw_ref']};config={k:meta[k] for k in ['publication','jurisdiction','state']}
 print('Full native replay '+family,flush=True)
 with patch.object(pypdfium2.PdfPage,'render',side_effect=deny),patch.object(pypdfium2.PdfPage,'get_objects',side_effect=deny),patch.object(pypdfium2.PdfImage,'extract',side_effect=deny),patch.object(pypdfium2.PdfImage,'get_bitmap',side_effect=deny):records,links=pdf_structure.pages(raw,item,config)
 assert len(records)==len(old)
 dest=base/'full-native-replays'/family;dest.mkdir(parents=True,exist_ok=True)
 with (dest/'records.jsonl').open('w') as f:
  for row in records:f.write(json.dumps(row,ensure_ascii=False).replace('\u2028','\\u2028').replace('\u2029','\\u2029').replace('\x85','\\u0085')+'\n')
 before={c['id']:c for r in old for t in r['tables'] for c in t['cells']};after={c['id']:c for r in records for t in r['tables'] for c in t['cells']}
 assert before.keys()==after.keys()
 for key,cell in before.items():
  for field in ['bbox','row','column','rowspan','colspan','text','word_ids','independent_pdfium_text']:
   assert cell[field]==after[key][field],(family,key,field)
 for case in ledger['cases']:
  if case['native_sha256']!=sha(raw):continue
  c=after[case['cell_id']];assert case['source_extractable_cell_text']==c.get('source_extractable_text',c['text'])
  case_results.append({'native_sha256':case['native_sha256'],'source_url':case['source_url'],'physical_page':case['physical_page'],'table_id':case['table_id'],'cell_id':case['cell_id'],'bbox':case['bbox'],'historical_detector_text':case['source_extractable_cell_text'],'historical_pdfium_text':case['independent_pdfium_cell_text'],'current_qualified_pdfium_text':c['qualified_pdfium_text'],'current_independent_character_agreement':c['independent_character_agreement'],'bounded_alias_proof':c['bounded_decoder_alias_resolutions'],'disposition':'source-proven-bounded-hyphen-alias' if c['bounded_decoder_alias_resolutions'] and c['independent_character_agreement'] else 'inferred-cell-boundary-unqualified'})
 result={'family':family,'source':native_path,'source_sha256':sha(raw),'historical_records':record_path,'historical_records_sha256':old_sha,'pages':len(records),'tables':sum(len(r['tables']) for r in records),'cells':len(after),'historical_cells_agree':sum(c['independent_character_agreement'] for c in before.values()),'current_cells_agree':sum(c['independent_character_agreement'] for c in after.values()),'source_word_ownership_complete_all_pages':all(r['pdf_qualification']['source_word_ownership_complete'] for r in records),'source_glyph_to_word_conservation_all_pages':all(r['pdf_qualification']['source_words_cover_deduplicated_glyph_characters'] for r in records),'normalized_source_word_conservation_all_pages':all(r['pdf_qualification']['normalized_source_word_characters_agree'] for r in records),'independent_page_text_engines_agree_all_pages':all(r['pdf_qualification']['independent_text_engine_characters_agree'] for r in records),'detector_cell_text_geometry_ownership_raw_pdfium_preserved':True,'new_bounded_alias_proofs':sum(len(c['bounded_decoder_alias_resolutions']) for c in after.values()),'semantic_complete':False,'new_pixels_or_image_operations':0,'source_files_unchanged':sha(source.read_bytes())==sha(raw) and sha(old_path.read_bytes())==old_sha}
 results.append(result);(dest/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
assert len(case_results)==46
assert implementation=={p.name:sha(p.read_bytes()) for p in [base/'pdf_structure.py',base/'bounded_decoder.py']}
report={'schema_version':1,'kind':'isolated full-native replay; no live acquisition or semantic promotion','network_requests':0,'image_operations':0,'ledger_sha256':sha(ledger_path.read_bytes()),'ledger_original_unchanged':True,'implementation':implementation,'documents':results,'historical_46_case_assessment':case_results,'source_proven_alias_cases':sum(c['disposition']=='source-proven-bounded-hyphen-alias' for c in case_results),'unqualified_inferred_boundary_cases':sum(c['disposition']=='inferred-cell-boundary-unqualified' for c in case_results)}
(base/'full-native-replay-summary.json').write_text(json.dumps(report,indent=2)+'\n')
