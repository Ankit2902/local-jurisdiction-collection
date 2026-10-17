"""Bind terminal offline candidate proof; does not alter runtime/source inputs."""
from pathlib import Path
import json,hashlib
base=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((base/'FINAL-SOURCE-MANIFEST.json').read_text())
assert all(sha(base/name)==value for name,value in manifest.items())
replay=json.loads((base/'full-source-replay-summary.json').read_text())
assert len(replay['results'])==2 and replay['network_requests']==0
assert all(r['source_files_unchanged'] and r['canonical_legal_html_preserved'] and r['source_id_ownership_order_and_hashes_preserved'] and r['raw_source_list_metadata_checks_passed'] and r['raw_native_start_end_consistent'] and r['normalized_image_payload_audit_passed'] and not r['complete'] for r in replay['results'])
log=(base/'candidate-v2-final-tests.log').read_text()
assert 'Ran 62 tests' in log and log.rstrip().endswith('OK')
summary={'schema_version':1,'candidate':'isolated Gridics source-first/list v2','status':'offline_candidate_qualified_with_explicit_source_gaps','production_promoted':False,'new_acquisition_loop_live_qualified':False,'network_requests':0,'access_stop_reset_or_retried':False,'runtime_sources':replay['implementation'],'final_runtime_test_count':62,'final_test_log':'candidate-v2-final-tests.log','source_manifest':'FINAL-SOURCE-MANIFEST.json','v1_lineage':'V1-LINEAGE.json','final_replay_summary':'full-source-replay-summary.json','raw_source_list_inventory':'raw-source-list-inventory.json','relative_patch':'V2-OVER-V1.diff','production_patch':'CANDIDATE-PATCH.diff','image_policy':{'separate_image_downloads':0,'normalized_placeholder':'[IMAGE]','embedded_image_payloads_in_normalized_records':False,'known_image_mime_rejected_before_body_read':True,'mislabeled_image_prefix_not_persisted':True,'css_original_source_only':True,'css_secondary_resources_imported':0},'books':[],'remaining_gaps':['Persistent publisher workflow stop prevents new acquisition-loop live qualification and full49-root Miami Comprehensive acquisition','Custom marker stylesheet bodies/rules unavailable in retained source: classes/counters preserved, punctuation unqualified','Existing unexplained empty source bodies and unresolved required/external-reference scope remain incomplete'],'historical_attempts':[{'path':'attempts/unicode-jsonl-reader','cause':'Comparison helper splitlines() treated embedded Unicode separators as record boundaries; helper corrected to literal LF; collector and original sources unchanged'}],'scope_note':'Native inventory capture/currentness checks are separate from legal/format/asset completeness. No jurisdiction completeness or full publication promotion.'}
for r in replay['results']:
 summary['books'].append({k:v for k,v in r.items() if k!='text_projection_changes'})
 summary['books'][-1]['text_projection_change_count']=len(r['text_projection_changes'])
(base/'validation-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
files={str(p.relative_to(base)):sha(p) for p in sorted(base.rglob('*')) if p.is_file() and p.name!='PACKAGE-MANIFEST.json' and '__pycache__' not in p.parts}
(base/'PACKAGE-MANIFEST.json').write_text(json.dumps({'schema_version':1,'files':files},indent=2)+'\n')
print(json.dumps({'status':summary['status'],'files':len(files),'source_manifest_sha256':sha(base/'FINAL-SOURCE-MANIFEST.json'),'books':[{k:b[k] for k in ['source','records','raw_source_lists','classed_lists','list_marker_qualification_gaps','complete']} for b in summary['books']]},indent=2))
