#!/usr/bin/env python3
"""Read-only compact terminal receipt replay; no native parse/network/image APIs."""
import argparse,hashlib,json,pathlib
P=pathlib.Path(__file__).resolve().parent;p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--source',type=pathlib.Path);g.add_argument('--receipts-only',action='store_true');a=p.parse_args();read=lambda q:json.loads(q.read_text());h=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
for name,sha in read(P/'MANIFEST.json').items():assert (P/name).is_file()and h(P/name)==sha,'Missing/corrupt packet file: '+name
before=read(P/'source-before.json');after=read(P/'source-after.json');assert before==after and len(before)==60
r=read(P/'evidence/milwaukee-original-exact-readonly.json');t=read(P/'evidence/milwaukee-original-exact-readonly-terminal.json');c=r['result'];assert r['status']=='terminal_recomputed'and r['requested_complete']and t['terminal_tool_exit_code']==0 and t['all_source_files_unchanged'];assert (c['expected_document_count'],c['acquired_document_count'],c['parsed_record_count'],c['table_count'],c['image_placeholder_count'])==(6,6,2300,1171,7);assert c['publication_file_coverage_complete']and c['pdf_page_extraction_complete']and c['source_consistency_complete'];assert not c['legal_semantic_coverage_complete']and c['manual_review_required']
for name,sha in r['executed_scripts'].items():assert h(P/'executed'/name)==sha==before['executed/'+name]
provenance=read(P/'evidence/EXECUTED-VERIFIER-PROVENANCE.json');assert h(P/'executed/verify.py')==before['executed/verify.py']==provenance['sha256']
assert r['executed_scripts']['pdf_structure.py']=='8341b33f36dbc52a20a229f04816d21d358a9f25a2399cab5a4a4c1e28e49251'
ledger=read(P/'evidence/milwaukee-original-qualification-ledger.json');assert ledger['independent_cells_disagree']==3745 and ledger['qualification_counts']['normalized_source_word_characters_agree']['False']==74 and ledger['qualification_counts']['source_words_cover_deduplicated_glyph_characters']['missing']==2300
if a.source:
 actual={q.relative_to(a.source).as_posix():h(q)for q in sorted(a.source.rglob('*'))if q.is_file()};assert actual==before,'Full source tree closure/hash mismatch'
print(json.dumps({'status':'passed','scope':'Exact original8341 terminal+readonly receipt replay','source_bytes_checked':bool(a.source),'source_files':60,'native_files':6,'physical_pages':2300,'historical_image_placeholders':7,'semantic_complete':False,'current80_parser_qualification_claimed':False,'instrumented_image_api_zero_claimed':False,'native_reparse_performed':False,'requests':0,'limits':'74oldcharacterconservationfalse/3745oldcellmismatches retained; missingnewglyphfield not inferredcomplete'},indent=2))
