from pathlib import Path
import hashlib,json,sys
b=Path(sys.argv[1]);o=Path(sys.argv[2]);d=b/'outputs/collection-readiness-next-2026-10-17/originals-integration';c=d/'v9-current-common-terminal-handoff-v1';production=b/'github/local-jurisdiction-collection'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_text())
assert sha(c/'promotion-and-validation.json')=='d6de4e2da1c60fdef65b0be2682396962f0a19246608838fdac86cc75b4b0075'
assert sha(c/'ARTIFACT-MANIFEST.json')=='e66607ac772a3a18cc40865c4c7fd53c3504982b27e4cfb0568e11e0463d6b7a'
manifest=load(c/'ARTIFACT-MANIFEST.json');assert manifest['base']=='..'
for n,v in manifest['files'].items():assert sha(d/n)==v['sha256']and(d/n).stat().st_size==v['bytes'],n
plan=load(c/'promotion-and-validation.json');mp=(c/plan['common_root_manifest']).resolve();assert sha(mp)==plan['common_root_manifest_sha256']=='f99c7b8f17d05401b57b0718c570adae5d6d3e69085f3cf4f0dbfaae00ce2afd';rm=load(mp);root=Path(rm['root']);candidate=Path(rm['candidate_origin']);common=[];family=[]
for n,v in rm['files'].items():
 q=root/n;h=v['sha256'];assert sha(q)==h,n
 if n.startswith('collectors/originals/'):
  local=n.removeprefix('collectors/originals/');assert sha(candidate/local)==h,n;family.append(n)
 else:assert sha(production/n)==h,n;common.append(n)
receipt_path=(c/plan['common_receipt']).resolve();assert sha(receipt_path)==plan['common_receipt_sha256']=='50d602cd55dd9873f6f2ddb687288a401fc4e65bcf6aad1933a0962453a2a883';r=load(receipt_path);out=Path(r['output']);source=d/'flagstaff-common-live-recovery-v1/source';assert out==d/'v9-current-live-source-replay-v1'
assert r['status']=='verified_publication'and r['verification_exit']==0 and r['family_verifier_passed']is True and r['evidence_read_only']is True and r['publisher_requests']==0 and r['runtime_changed_during_run']is False and r['source_changed_during_run']is False
assert r['collector_sources_before']==r['collector_sources_after']
for n,h in r['collector_sources_after'].items():assert sha(root/n)==h,n
assert r['evidence_sha256_before']==r['evidence_sha256_after']
for n,h in r['evidence_sha256_after'].items():assert sha(out/n)==h,n
runtime=Path(r['runtime_receipt_path']);assert runtime==production/'.collection-runtime/runtime.json';assert sha(runtime)==r['runtime_receipt_sha256'];py=production/'.collection-runtime/venv/bin/python';assert plan['executed_commands']['replay'][0]==plan['executed_commands']['current_common_verify'][0]==str(py)
assert plan['executed_commands']['current_common_verify'][2]==str(root/'collect.py')
assert r['verification_argv']==[str(py),'-B',str(root/'collectors/registry/collect.py'),'verify','--target','original-flagstaff-az','--publication','original-flagstaff-az-primary','--out',str(out),'--python',str(py)]
assert r['selected_plan']['argv'][0]==str(root/'collectors/originals/cli.py')or r['selected_plan']['argv'][0]==str(py)
cfg=load(root/'collectors/originals/configs/flagstaff.json');start=load(out/'collection-start.json');checkpoint=load(out/'checkpoint.json');assert cfg==r['selected_config']==start['publication_config']==checkpoint['config']
assert r['publication_id']=='original-flagstaff-az-primary'and r['publication']['adapter_family']=='originals'and r['publication']['source_url']==cfg['source_url']and r['publication']['role']=='primary'
assert r['publication']['full_live_verified']is False and r['publication']['validation_level']=='mapped_only'
sourcehash=sha(source/'checkpoint.json');assert checkpoint['origin']['html_checkpoint_sha256']==plan['results']['origin']['html_checkpoint_sha256']==sourcehash=='6e3d638702f24570470554817ad27e301010ccea35058b4c41e4dd845d7e4d8f'
assert start['acquisition_mode']==checkpoint['acquisition_mode']=='retained_source_replay';assert checkpoint['origin']['word_checkpoint_sha256']is None
original_files={p.relative_to(source).as_posix():sha(p)for p in source.rglob('*')if p.is_file()};replayed_files={p.relative_to(out/'source').as_posix():sha(p)for p in(out/'source').rglob('*')if p.is_file()};assert original_files==replayed_files
for n,h in checkpoint['code_fingerprint'].items():assert sha(root/'collectors/originals'/n)==h,n
assert sha(out/'normalized/records.jsonl')=='1344484a99e9dce522f72d2254b713e9b725d552bb28d174c3fb66884a7fae5b'
nav=load(out/'normalized/source-target-coverage.json');assert nav['literal_browser_fragment_complete']is False and nav['source_target_coverage_complete']is True and len(nav['resolutions'])==3
cov=load(out/'coverage.json');assert cov['publication_accepted']is True and cov['whole_jurisdiction_complete']is False and cov['external_adopted_legal_dependency_closure_complete']is False and cov['independent_final_review_complete']is False
assert r['acceptance']['publication_accepted']is True and r['acceptance']['jurisdiction_complete']is False and r['acceptance']['edition_complete']is None and r['acceptance']['native_capture_verified']is False and r['acceptance']['coverage_sha256']==sha(out/'coverage.json')
replay=load(out/'replay-verification.json');assert replay['full_raw_replay_equal']is True and replay['input_files_modified']is False and replay['source_route_ledger_verified']is True and replay['opening_body_closing_chronology_verified']is True
assert sha(Path(r['log']))==sha(c/'actual-current-common-family-verify.log')
result={'passed':True,'handoff_manifest_files':len(manifest['files']),'handoff_manifest_bytes':sum(x['bytes']for x in manifest['files'].values()),'copied_current_common_files_exact':len(common),'copied_frozen_candidate_family_files_exact':len(family),'actual_common_source_components_unchanged':len(r['collector_sources_after']),'actual_evidence_before_after_and_current_equal':len(r['evidence_sha256_after']),'actual_source_tree_files_byte_identical':len(original_files),'exact_current_runtime_receipt_sha256':r['runtime_receipt_sha256'],'exact_actual_terminal_v7_source_checkpoint':sourcehash,'explicit_new_retained_source_replay':True,'typed_config_current_common_and_collection_equal':True,'status':r['status'],'verification_exit':r['verification_exit'],'family_verifier_passed':True,'readonly':True,'publisher_requests':0,'literal_browser_fragment_complete':False,'finite_source_target_coverage_complete':True,'whole_jurisdiction_complete':False,'native_capture_or_edition_credit_added':False,'new_live_or_resume_acquisition_credit_added':False,'prior_v9_review_sha256':'3b437b5a6933694d8cdeef7b6d2a0a2a0f2871ace4d84184535374cab8e66135','no_new_replay_browser_network_or_image_operation':True,'auditor_sha256':sha(Path(__file__))}
(o/'independent-binding-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
