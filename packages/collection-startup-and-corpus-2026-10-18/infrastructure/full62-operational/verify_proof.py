#!/usr/bin/env python3
"""Read-only stdlib proof replay. No PDF/image/network APIs or output writes."""
import csv,hashlib,json,pathlib,re
P=pathlib.Path(__file__).resolve().parent
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
manifest=read(P/'MANIFEST.json')
for name,sha in manifest.items():
 p=P/name
 assert not pathlib.Path(name).is_absolute()and '..'not in pathlib.Path(name).parts,'Unsafe manifest path'
 assert p.is_file()and h(p)==sha,'Missing/corrupt proof file: '+name
run=P/'run';state=read(run/'checkpoint.json');cfg=state['config'];expected='915fe1fdf8ff5da33acfce7d08637808cb57886fbbc7f157b2b81bfcf970827c'
assert cfg['id']=='82-0c6b3dc40877'and cfg['expected_sha256']==expected and cfg['expected_pages']==62
for key in ['start','end']:
 e=state[key];assert e['path']=='raw/'+key+'.pdf';raw=run/e['path'];m=read(raw.with_name(raw.name+'.receipt.json'));assert h(raw)==e['sha256']==m['sha256']==expected and e['url']==cfg['url']==m['url']and m['http_status']==200 and not m['challenge'];assert raw.read_bytes().startswith(b'%PDF-')
for name,sha in state['code_hashes'].items():assert h(run/'script-versions'/(sha+pathlib.Path(name).suffix))==sha
rows=[json.loads(l)for l in (run/'records.jsonl').open()if l.strip()];assert len(rows)==62 and [r['physical_page']for r in rows]==list(range(1,63));assert all(r['raw_ref']=='raw/start.pdf'and r['raw_sha256']==expected for r in rows)
old=read(P/'evidence/prior-source-page-texts.json');assert all(r['text']==old['texts'][str(r['physical_page'])]for r in rows);assert sum(r['text'].count('[IMAGE]')for r in rows)==5
for name in ['records.jsonl','records.csv']:assert not re.search(r'data\s*:\s*image\s*/',(run/name).read_text(),re.I),'Image payload metadata leak'
c=list(csv.DictReader((run/'records.csv').open()));assert len(c)==62
for a,b in zip(c,rows):assert all(a[k]==str(b[k])for k in a),'CSV/JSON mismatch'
selected=[r for r in rows if r.get('canonical_structure_selection')];assert [r['physical_page']for r in selected]==[2,3,6,46];assert all(r['tables']==[]for r in selected)
oldq=[r['superseded_detector_diagnostics']['original_record_fields']['pdf_qualification']for r in selected];assert sum(q['detected_table_cells']for q in oldq)==467;assert sum(q['detected_table_cells']-q['independent_table_cells_agree']for q in oldq)==44
for r in selected:assert set(r['superseded_detector_diagnostics']['original_record_fields'])=={'tables','ordered_blocks','text','ordering','pdf_qualification'}
for r in rows:
 q=r['pdf_qualification'];assert all(q[k]is True for k in ['source_word_ownership_complete','normalized_source_word_characters_agree','independent_text_engine_characters_agree','source_words_cover_deduplicated_glyph_characters'])
assert sum(r['pdf_qualification']['detected_table_cells']for r in rows)==149
assert sum(r['pdf_qualification']['independent_table_cells_agree']for r in rows)==149
coverage=read(run/'coverage.json');dimensions=coverage['pdf_details']['source_infrastructure_dimensions'];assert dimensions['contents_entries']==96 and dimensions['source_words']==603 and dimensions['source_printed_units']==110 and dimensions['original_failed_detector_cells_retained']==44 and dimensions['literal_leader_folio_spacing_discrepancies']==3 and not dimensions['full_line_spacing_complete'];assert coverage['native_document_complete']and coverage['source_page_traversal_complete']and not coverage['publication_complete']and not coverage['publication_text_complete']
guard=read(P/'evidence/infrastructure-full62-current-final-v3-replay-receipt.json');assert guard['exit_code']==0 and guard['forbidden_calls']==[]and guard['current_network_requests']==0 and guard['image_api_accesses']==0
common=read(P/'evidence/infrastructure-full62-current-final-v3-common-receipt.json');assert common['verification_exit']==0 and common['family_verifier_passed']and common['acceptance']['native_capture_verified']and not common['acceptance']['publication_accepted'];assert common['evidence_read_only']and common['publisher_requests']==0 and not common['source_changed_during_run']and not common['runtime_changed_during_run'];assert common['evidence_sha256_before']==common['evidence_sha256_after']
for name,sha in common['evidence_sha256_after'].items():assert h(run/name)==sha
runtime=read(P/'runtime/SOURCE-HASHES.json')
for name,sha in runtime.items():assert h(P/'runtime'/name)==sha
for name in ['native_document.py','pdf_structure.py','infrastructure_profile.py','infrastructure_contents.py','infrastructure_region_core.py']:
 key='collectors/encodeplus/'+name;assert common['collector_sources_before'][key]==common['collector_sources_after'][key]==runtime[key]
print(json.dumps({'status':'passed','files':len(manifest),'native_file_and_all62_pages_verified':True,'json_csv_rows':62,'guard_forbidden_calls':0,'current_publisher_requests':0,'image_placeholders':5,'canonical_regions':4,'old_failed_cells_retained':44,'spacing_discrepancies_retained':3,'common_family_verifier_exit':0,'common_exit':2,'publication_accepted':False,'mode':'Read-only manifest/output/receipt replay; no native reparse or image/network APIs'},indent=2))
