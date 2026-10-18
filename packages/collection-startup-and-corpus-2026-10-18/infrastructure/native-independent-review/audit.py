"""Independent stdlib consumer/source binding; imports no candidate/parser."""
import csv,hashlib,json,pathlib,sys,datetime
P=pathlib.Path(sys.argv[1]).resolve();B=pathlib.Path(sys.argv[2]).resolve();O=pathlib.Path(sys.argv[3])
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=lambda p:json.loads(p.read_text())
rows=lambda p:[json.loads(s)for s in p.read_text().splitlines()]
assert h(P/'MANIFEST.json')=='3ba4d3c7f1428108bdd2e7893b08416f56b7f8456ce7bcdc047d0387518e4a34'
assert h(B/'MANIFEST.json')=='b04944f17131c82d5108fabd53e3c154185a7d436d33f409bd6a58375aecccdf'
before={k:h(P/k)for k in r(P/'MANIFEST.json')}
assert before==r(P/'MANIFEST.json')
a=rows(P/'final-default-native/records.jsonl');b=rows(B/'current-retained-derivative-v4/records.jsonl');assert len(a)==len(b)==172
for x,y in zip(a,b):
 for k,v in y.items():assert x.get(k)==v if k!='unit'else x['source_unit_kind']==v,(x['id'],k)
 assert x['unit']=='pdf_source_printed_unit'and 'physical_page'not in x and x['page_count']==62
 assert x['physical_page_start']==min(x['source_pages'])and x['physical_page_end']==max(x['source_pages'])
 assert x['source_url'].endswith('#page='+str(min(x['source_pages'])))
assert [x['unit_type']for x in a[:2]]==['frontmatter','table-of-contents']and all(x['unit_type']=='printed-heading-unit'for x in a[2:])
old=a[0]['superseded_detector_diagnostics']['original_page_records'];assert len(old)==62
frags=[f for x in a for f in x['source_fragments']];assert len(frags)==1776
assert [(p['physical_page'],i,b['text'],b.get('word_ids',[]))for p in old for i,b in enumerate(p['ordered_blocks'])]==[(f['page'],f['block_index'],f['block']['text'],f['block'].get('word_ids',[]))for f in frags]
assert sum(f['page_control']for f in frags)==142
words=[w for x in a for z in x['ordered_blocks']for w in z.get('word_ids',[])];assert len(words)==len(set(words))==18662
assert sum(len(x['tables'])for x in a)==5 and sum(len(t['cells'])for x in a for t in x['tables'])==79
assert sum(x['text'].count('[IMAGE]')for x in a)==5
cs=list(csv.DictReader((P/'final-default-native/records.csv').open()));assert len(cs)==172
for x,c in zip(a,cs):assert x['id']==c['id']and x['text']==c['text']and x['source_pages']==json.loads(c['source_pages'])and c['physical_page']==''and c['unit_type']==x['unit_type']
rec=r(P/'final-default-receipt.json');assert rec['exit_code']==0 and rec['error']is None and not rec['forbidden_calls']and rec['current_network_requests']==rec['image_api_accesses']==0
assert rec['driver_sha256']==h(P/'retained_native_default.py')and rec['source_checkpoint_sha256']==h(P/'source-origin-checkpoint.json')
for name,sha in rec['runtime_source_hashes'].items():assert h(P/'candidate'/name)==sha
cp=r(P/'final-default-native/checkpoint.json')
for k in ['start','end']:
 e=cp[k];q=P/'final-default-native'/e['path'];m=r(q.with_name(q.name+'.receipt.json'));assert h(q)==e['sha256']==m['sha256']==cp['config']['expected_sha256'];assert e['url']==m['url']==cp['config']['url']and m['http_status']==200 and not m['challenge']
for name,sha in cp['code_hashes'].items():assert h(P/'candidate/collectors/encodeplus'/name)==sha and h(P/'final-default-native/script-versions'/(sha+pathlib.Path(name).suffix))==sha
cov=r(P/'final-default-native/coverage.json');assert cov['native_document_complete']and cov['source_page_traversal_complete']and cov['normalized_record_count']==172 and cov['physical_pages']==62
for k in ['publication_text_complete','source_logical_structure_qualified','required_external_legal_dependencies_complete','publication_complete','attachments_complete','edition_complete','jurisdiction_complete']:assert cov[k]is False
assert cov==rec['coverage']
assert sum(len(p['links'])for p in old)==194 and sum(bool(l.get('uri'))for p in old for l in p['links'])==22
assert (P/'final-default-native/infrastructure-source-page-diagnostics.jsonl').read_bytes()==b''.join((json.dumps(x,sort_keys=True,ensure_ascii=False)+'\n').encode()for x in old)
mix=r(P/'mixed828-differential.json');assert mix['passed']and mix['after_records']==828 and mix['other_record_noops']==656 and mix['source_images_total']==201 and mix['other_image_ids_blocks_unchanged']==196 and len(mix['explicit_asset_to_catalog_image_namespace_aliases'])==5
mixed=rows(P/'mixed828-native-exports/records.jsonl');assert len(mixed)==828
selected=[x for x in mixed if x.get('unit')=='pdf_source_printed_unit'];assert len(selected)==172
for i,(x,y)in enumerate(zip(selected,a)):
 assert {k:v for k,v in x.items()if k!='mixed_source_diagnostic_lineage'}==y
 assert ('mixed_source_diagnostic_lineage'in x)==(i==0)
mc=list(csv.DictReader((P/'mixed828-native-exports/records.csv').open()));assert len(mc)==828
for x,c in zip(mixed,mc):assert x['id']==c['id']and x['text']==c['text']
assert before=={k:h(P/k)for k in before}
report={'passed':True,'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_manifest_sha256':h(P/'MANIFEST.json'),'source_projection_manifest_sha256':h(B/'MANIFEST.json'),'normal_runtime':r(P/'SUMMARY.json')['native_runtime_sha256'],'candidate_files_unchanged':len(before),'source_fields_equal_prior_independently_reviewed_projection':172,'physical_pages':62,'unit_types':{'frontmatter':1,'table_of_contents':1,'printed_heading_units':170},'source_blocks_exact':1776,'words_once':18662,'controls':142,'grids':5,'cells':79,'images':5,'source_page_links':194,'uri_refs':22,'mixed_records':828,'mixed_other_noops':656,'mixed_images':201,'unchanged_other_image_ids':196,'explicit_selected_image_aliases':5,'native_page_text_parse':False,'network_or_image_apis':False,'scope':'Normal workflow/identity/serializer/diagnostic binding. Full legal/nested order/required dependencies/edition remain false. Actual native extraction credit belongs to captured final default execution, not this read-only consumer.'}
O.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
