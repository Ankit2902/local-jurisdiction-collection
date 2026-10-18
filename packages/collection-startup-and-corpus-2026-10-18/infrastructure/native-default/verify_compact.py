#!/usr/bin/env python3
"""Compact terminal copy replay; omitted historical raw fault trees get no replay credit."""
import csv,hashlib,json,pathlib,re
P=pathlib.Path(__file__).resolve().parent
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=lambda p:json.loads(p.read_text())
selection=r(P/'COPY-SELECTION.json')
assert h(P/'SOURCE-PACKET-MANIFEST.json')==selection['source_packet_manifest_sha256']=='3ba4d3c7f1428108bdd2e7893b08416f56b7f8456ce7bcdc047d0387518e4a34'
original=r(P/'SOURCE-PACKET-MANIFEST.json')
for item in selection['included']:assert original[item['source']]==item['sha256']==h(P/item['destination'])
assert all(item['source'].startswith('retained-default-workflow/') for item in selection['omitted'])
assert {item['source'] for item in selection['included']} | {item['source'] for item in selection['omitted']} == set(original)
m=r(P/'MANIFEST.json')
for name,sha in m.items():
 q=pathlib.Path(name);assert not q.is_absolute() and '..'not in q.parts;assert h(P/q)==sha,name
sources=r(P/'FINAL-SOURCE-HASHES.json')
for item in selection['included_source_snapshot_only']:assert item['sha256']==sources[item['source'][len('candidate/'):]]==h(P/item['destination'])
for name,sha in sources.items():assert h(P/'candidate'/name)==sha
receipt=r(P/'final-default-receipt.json');assert receipt['runtime_source_hashes']==sources and receipt['exit_code']==0 and receipt['error'] is None and receipt['forbidden_calls']==[] and receipt['current_network_requests']==receipt['image_api_accesses']==0
assert receipt['driver_sha256']==h(P/'retained_native_default.py')
assert receipt['source_checkpoint_sha256']==h(P/'source-origin-checkpoint.json')
R=P/'final-default-native';state=r(R/'checkpoint.json');cov=r(R/'coverage.json');cfg=state['config'];sha='915fe1fdf8ff5da33acfce7d08637808cb57886fbbc7f157b2b81bfcf970827c';assert cfg['id']=='82-0c6b3dc40877'and cfg['expected_sha256']==sha and cfg['expected_pages']==62 and state['phase']=='finished'
for key in ['start','end']:
 e=state[key];raw=R/e['path'];meta=r(raw.with_name(raw.name+'.receipt.json'));assert h(raw)==e['sha256']==meta['sha256']==sha and e['url']==cfg['url']==meta['url']and meta['http_status']==200 and not meta['challenge']
for name,version in state['code_hashes'].items():assert h(R/'script-versions'/(version+pathlib.Path(name).suffix))==version
rows=[json.loads(x)for x in (R/'records.jsonl').read_text().splitlines()];assert len(rows)==len({x['id']for x in rows})==172
assert [x['unit_type']for x in rows[:2]]==['frontmatter','table-of-contents'] and sum(x['unit_type']=='printed-heading-unit'for x in rows)==170
assert all(x['unit']=='pdf_source_printed_unit'and 'physical_page'not in x and x['page_count']==62 and x['raw_sha256']==sha for x in rows)
old=rows[0]['superseded_detector_diagnostics']['original_page_records'];assert len(old)==62 and [x['physical_page']for x in old]==list(range(1,63))
a=[(p['physical_page'],i,b['text'],b.get('word_ids',[]))for p in old for i,b in enumerate(p['ordered_blocks'])];b=[(f['page'],f['block_index'],f['block']['text'],f['block'].get('word_ids',[]))for x in rows for f in x['source_fragments']];assert a==b and len(a)==1776
words=[w for x in rows for b in x['ordered_blocks']for w in b.get('word_ids',[])];assert len(words)==len(set(words))==18662
assert sum(f['page_control']for x in rows for f in x['source_fragments'])==142 and sum(len(x['source_pages'])>1 for x in rows)==40
assert sum(len(x['tables'])for x in rows)==5 and sum(len(t['cells'])for x in rows for t in x['tables'])==79
assert sum(p['pdf_qualification']['detected_table_cells']for p in old)==149
qs=[p['superseded_detector_diagnostics']['original_record_fields']['pdf_qualification']for p in old if p.get('superseded_detector_diagnostics')];assert sum(q['detected_table_cells']for q in qs)==467 and sum(q['detected_table_cells']-q['independent_table_cells_agree']for q in qs)==44
cs=list(csv.DictReader((R/'records.csv').open()));assert len(cs)==172
for x,c in zip(rows,cs):assert c['id']==x['id']and c['text']==x['text']and json.loads(c['source_pages'])==x['source_pages']and c['physical_page']==''
assert sum(x['text'].count('[IMAGE]')for x in rows)==5
assert not re.search(r'data\s*:\s*image\s*/',(R/'records.jsonl').read_text(),re.I)
assert cov==receipt['coverage'] and cov['native_document_complete']and cov['physical_pages']==62 and cov['normalized_record_count']==172
for key in ['publication_text_complete','source_logical_structure_qualified','required_external_legal_dependencies_complete','publication_complete','attachments_complete','edition_complete','jurisdiction_complete']:assert cov[key] is False
assert cov['pdf_details']['source_extractable_characters_conserved'] and cov['pdf_details']['source_flat_printed_units_qualified'] and cov['pdf_details']['metadata']==rows[0]['source_document_evidence']['native_metadata']
assert sum(len(p['links'])for p in old)==194 and sum(bool(l.get('uri'))for p in old for l in p['links'])==22
assert (R/'infrastructure-source-page-diagnostics.jsonl').read_bytes()==b''.join((json.dumps(x,sort_keys=True,ensure_ascii=False)+'\n').encode()for x in old)
assert 'Ran 130 tests' in (P/'final-family-tests.stderr').read_text()and (P/'final-family-tests.stderr').read_text().rstrip().endswith('OK')
assert 'Ran 11 tests' in (P/'final-focused.stderr').read_text()and (P/'final-focused.stderr').read_text().rstrip().endswith('OK')
mix=r(P/'mixed828-differential.json');assert mix['passed']and mix['after_records']==828 and mix['other_record_noops']==656 and mix['source_images_total']==201 and mix['other_image_ids_blocks_unchanged']==196 and len(mix['explicit_asset_to_catalog_image_namespace_aliases'])==5
for name,sha in mix['output_sha256'].items():assert h(P/'mixed828-native-exports'/name)==sha
assert r(P/'retained-default-workflow.json')['passed']and r(P/'retained-default-workflow.json')['forbidden_calls']==[]
accept=r(P/'common-pure-acceptance.json')['acceptance'];assert accept['native_capture_verified']and not accept['publication_coverage_accepted']
for f in r(P/'FINAL-PROMOTION-PLAN.json')['files']:assert h(P/f['source'])==f['after_sha256']
print(json.dumps({'passed':True,'files':len(m),'source_files':len(sources),'normal_native_workflow':True,'actual_default_exit':0,'physical_pages':62,'normalized_units':172,'cover':1,'toc':1,'other_printed_units':170,'words_once':18662,'controls':142,'source_grids_cells':[5,79],'diagnostic_cells':616,'diagnostic_failures':44,'image_placeholders':5,'mixed828_noops':656,'mixed_images':201,'explicit_image_namespace_aliases':5,'current_family_tests':130,'focused_tests':11,'publication_accepted':False,'mode':'Read-only stdlib proof replay; no native parsing/network/image APIs'}))
