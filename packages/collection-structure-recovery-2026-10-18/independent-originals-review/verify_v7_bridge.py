import json,hashlib,collections,sys
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlsplit,unquote
b,o=map(Path,sys.argv[1:]);v6=b/'note-resume-candidate-v6';v7=b/'note-resume-candidate-v7'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
manifest=load(v7/'review-bundle-manifest.json');bad=[];total=0
for rel,expected in manifest['files'].items():
 p=v7/rel;total+=p.stat().st_size
 if sha(p)!=expected:bad.append(rel)
records=load(o/'target-ID-retention.json');state=load(v7/'collection/source/checkpoint.json');art={a['source_url']:a for a in state['artifacts'] if a['role']=='content'}
duplicates=[]
for event in records['ambiguous_normalized_target_links']:
 u=urlsplit(event['url']);url=u._replace(fragment='').geturl();frag=unquote(u.fragment);a=art[url];p=v7/'collection/source'/a['path'];assert sha(p)==a['sha256'];root=BeautifulSoup(p.read_bytes(),'html.parser').select_one('#mainContent');matches=[e for e in root.find_all(True) if e.get('id')==frag or e.get('name')==frag]
 duplicates.append({'url':event['url'],'referencing_owner':event['owner_record_id'],'source_matching_elements':len(matches),'source_elements':[str(e)[:700] for e in matches],'normalized_owner_count':len(event['normalized_owner_ids']),'source_already_duplicate':len(matches)>1})
r7=v7/'collection/normalized/records.jsonl';r6=v6/'collection/normalized/records.jsonl';old=b/'flagstaff-operational-v4/normalized/records.jsonl'
oldr=[json.loads(x) for x in old.read_text().split('\n') if x];newr=[json.loads(x) for x in r7.read_text().split('\n') if x];assert len(oldr)==len(newr)==2661
allowed={'semantic_html','notes','links','source_list_groups'};unexpected=[];diffcounts=collections.Counter()
for x,y in zip(oldr,newr):
 assert x['record_id']==y['record_id']
 changed={k for k in x.keys()|y.keys() if x.get(k)!=y.get(k)}
 diffcounts.update(changed)
 if changed-allowed:unexpected.append({'id':x['record_id'],'fields':sorted(changed-allowed)})
source_diff=[p.name for p in (v7/'source').iterdir() if p.is_file() and p.suffix in ['.py','.json','.txt'] and (v6/'source'/p.name).exists() and sha(p)!=sha(v6/'source'/p.name)]
report={'schema':'independent-v7-frozen-bundle-source-and-record-bridge-1','manifest_sha256':sha(v7/'review-bundle-manifest.json'),'manifest_files':len(manifest['files']),'manifest_bytes':total,'manifest_mismatches':bad,'v6_v7_source_changed_files':source_diff,'v6_records_sha256':sha(r6),'v7_records_sha256':sha(r7),'v6_v7_records_byte_equal':r6.read_bytes()==r7.read_bytes(),'old_v4_records_sha256':sha(old),'actual2661_unexpected_field_changes':unexpected,'actual2661_changed_field_counts':dict(diffcounts),'all_full_text_tables_block_indices_and_other_nonmetadata_fields_exact':not unexpected,'referenced_source_duplicate_occurrences':len(duplicates),'all_31_ambiguities_already_present_in_original_source':all(x['source_already_duplicate'] for x in duplicates),'duplicate_source_events':duplicates,'source_ID_name_attribute_counters_exact':records['source_target_occurrences']==records['normalized_target_occurrences']==4962 and not records['errors'],'source_present_normalized_missing':len(records['source_present_but_normalized_missing_links']),'publisher_missing_target_occurrences':len(records['original_legal_target_missing_links']),'no_unique_target_resolution_claim_for_source_duplicates':True,'network_requests':0,'no_image_download_decode_render_extract_OCR':True,'auditor_sha256':sha(Path(__file__))}
report['passed']=not bad and not unexpected and report['v6_v7_records_byte_equal'] and report['all_31_ambiguities_already_present_in_original_source'] and source_diff==['flagstaff_html_normalize.py']
(o/'v7-independent-bridge.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='duplicate_source_events'}));sys.exit(0 if report['passed'] else 2)
