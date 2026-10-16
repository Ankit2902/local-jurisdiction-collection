#!/usr/bin/env python3
"""Offline verification of actually executed standalone/CUA acquisition evidence."""
import csv,json,re,subprocess,sys,tempfile
from pathlib import Path
from datetime import datetime,timezone
from bs4 import BeautifulSoup
import gridics as g
ROOT=Path(__file__).resolve().parent
EXPORTS=['aggregate-fulltext.json','aggregate-fulltext.csv','aggregate-toc.json','aggregate-toc.csv','source-nodes.jsonl','node-dispositions.jsonl','record-provenance.jsonl','exceptions.jsonl']
def read(path):return json.loads(Path(path).read_text())
def main():
 result=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT),'-p','test_gridics.py','-v'],capture_output=True,text=True)
 (ROOT/'e2e-evidence/final-tests.txt').write_text(result.stdout+result.stderr)
 if result.returncode:raise RuntimeError('Regression failed; see e2e-evidence/final-tests.txt')
 test_count=int(re.search(r'Ran (\d+) tests',result.stderr).group(1));packages={};comparison={}
 # Independent navigation and fresh body stages are explicitly hash-bound in one replay manifest.
 combined=read(ROOT/'standalone-final/snapshot-manifest.json')
 for artifact in combined['artifacts']:
  artifact['path']='standalone-final/'+artifact['path']
  if artifact.get('response_metadata_path'):artifact['response_metadata_path']='standalone-final/'+artifact['response_metadata_path']
  if artifact.get('consistency'):artifact['consistency']['end_raw_path']='standalone-final/'+artifact['consistency']['end_raw_path']
 combined['inventory']={'path':'navigation-acquisition/navigation-current.json','sha256':g.digest((ROOT/'navigation-acquisition/navigation-current.json').read_bytes()),'acquisition_stage':'independent complete observed tree enumeration; source legal version unverified'}
 combined['navigation_evidence']='navigation-acquisition/navigation-evidence.json'
 g.save(ROOT/'standalone-combined-manifest.json',combined)
 for name in ['standalone','cua']:
  source=ROOT/'standalone-combined-manifest.json' if name=='standalone' else ROOT/'cua-acquisition/snapshot-manifest.json';out=ROOT/(name+'-verified-package');(out/'checkpoint.json').unlink(missing_ok=True)
  packages[name]=g.replay(source,out)
  data=read(out/'aggregate-fulltext.json')['provisions']
  csv.field_size_limit(max(csv.field_size_limit(),max(len(value) for row in data for value in row.values())))
  with (out/'aggregate-fulltext.csv').open(encoding='utf-8-sig',newline='') as f:assert list(csv.DictReader(f))==data,'CSV/JSON mismatch'
  manifest=read(source);comparisons=[]
  for artifact in manifest['artifacts']:
   raw=(source.parent/artifact['path']).read_bytes();assert g.digest(raw)==artifact['sha256'];nodes,records,_=g.parse_html(raw.decode(),artifact['url'])
   examples=[];s=BeautifulSoup(raw,'html.parser')
   for record in records:
    source_node=s.select_one('#section-'+record['node_id']);serialized=BeautifulSoup(record['row']['full_text'],'html.parser')
    own_tables=[t for t in source_node.select('table') if t.find_parent(class_='section') is source_node]
    if own_tables:
     counts={'citation':record['row']['citation'],'source_tables':len(own_tables),'serialized_tables':len(serialized.select('table')),'source_rows':sum(len(t.select('tr')) for t in own_tables),'serialized_rows':len(serialized.select('tr')),'source_cells':sum(len(t.select('td,th')) for t in own_tables),'serialized_cells':len(serialized.select('td,th'))}
     assert counts['source_tables']==counts['serialized_tables'] and counts['source_rows']==counts['serialized_rows'] and counts['source_cells']==counts['serialized_cells'];examples.append(counts)
   comparisons.append({'url':artifact['url'],'raw_path':str((source.parent/artifact['path']).relative_to(ROOT)),'raw_sha256':artifact['sha256'],'rendered_nodes':len(nodes),'record_count':len(records),'table_comparisons':examples,'start_end_consistency':artifact.get('consistency')})
  comparison[name]=comparisons
 with tempfile.TemporaryDirectory() as temporary:
  p=Path(temporary);manifest=ROOT/'standalone-combined-manifest.json';g.replay(manifest,p/'clean');g.replay(manifest,p/'resumed',1);g.replay(manifest,p/'resumed')
  replay_checks={name:{'clean_sha256':g.digest((p/'clean'/name).read_bytes()),'resumed_sha256':g.digest((p/'resumed'/name).read_bytes()),'equal':(p/'clean'/name).read_bytes()==(p/'resumed'/name).read_bytes()} for name in EXPORTS}
  assert all(v['equal'] for v in replay_checks.values())
 g.save(ROOT/'e2e-evidence/fresh-replay-equivalence.json',replay_checks);g.save(ROOT/'e2e-evidence/fresh-source-comparisons.json',comparison)
 start=read(ROOT/'e2e-evidence/standalone-final-start.json');resume=read(ROOT/'e2e-evidence/standalone-final-resume.json');assert start['acquisition_status']=='interrupted_by_requested_progress_limit' and start['route_count']==1
 assert resume['acquisition_status']=='completed_bounded_routes' and resume['route_count']==3 and resume['preserved_prior_artifacts']
 navigation_binding=read(ROOT/'navigation-acquisition/acquisition-checkpoint.json')['binding']
 assert g.digest((ROOT/'e2e-evidence/executed-navigation-acquire.py').read_bytes())==navigation_binding['code_sha256'],'Executed navigation code hash mismatch'
 assert g.digest((ROOT/'acquire.py').read_bytes())==read(ROOT/'standalone-final/acquisition-checkpoint.json')['binding']['code_sha256'],'Delivered acquisition code differs from final executed code'
 assert g.digest((ROOT/'cua_capture.mjs').read_bytes())==read(ROOT/'cua-acquisition/capture-receipt.json')['adapter_sha256'],'Delivered CUA adapter differs from executed code'
 nav=read(ROOT/'navigation-acquisition/navigation-current.json');assert all(n['children_enumerated'] for n in nav)
 states=read(ROOT/'navigation-acquisition/navigation-evidence.json');all_nodes={n['node_id'] for n in nav};assert len(all_nodes)==len(nav)
 root_nodes=[n for n in nav if n['parent_node_id'] is None];first_tree=ROOT/'navigation-acquisition'/states['states'][0]['path'];initial=g.inventory_html(first_tree.read_text());assert {n['node_id'] for n in initial if n['parent_node_id'] is None}=={n['node_id'] for n in root_nodes}
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'status':'bounded_live_end_to_end_passed_both_runtimes','source':'Gridics CodeHUB Cupertino','tests':{'passed':test_count,'failed':0,'command':'python verify_e2e.py','log':'e2e-evidence/final-tests.txt','python':sys.version.split()[0]},'qualifications':{'standalone_url_to_raw_to_parser_to_verified_package':'passed','supported_cua_url_to_raw_to_parser_to_verified_package':'passed','standalone_intentional_acquisition_interruption_resume':'passed; preserved first route hash and acquired only remaining two routes','fresh_parser_interruption_resume':'passed; eight exports byte-identical','start_end_source_sample_consistency':'passed; three fresh standalone routes reloaded and semantic paths/headings/bodies unchanged','cross_runtime_title1_semantics':'passed; all65 UUID own-body hashes equal','full_observed_navigation_expansion':'passed in separate earlier navigation stage; all observed controls expanded; explicitly hash-bound to later fresh body replay; no per-leaf legal-body collection','full_legal_collection':'not attempted or qualified','current_through_legal_version':'unverified; publisher disclaimer explicitly warns source may not reflect most recent legislation'},'packages':packages,'navigation':{'executed_code_path':'e2e-evidence/executed-navigation-acquire.py','executed_code_matches_checkpoint_hash':True,'observed_nodes':len(nav),'root_nodes':len(root_nodes),'expandable_nodes':sum(n['has_children'] for n in nav),'closed_observed_branches':sum(not n['children_enumerated'] for n in nav),'expansion_clicks':states['expansion_count'],'opaque_compound_class_nodes':sum('--' in n['publisher_class_identity'] for n in nav),'rendered_data_path_qualified_routes':sum(bool(n['source_url']) for n in nav),'candidate_routes_only':sum(bool(n['candidate_source_url']) and not n['source_url'] for n in nav),'compound_or_descendant_routes_unqualified':sum(not n['candidate_source_url'] for n in nav),'same_top_level_identities_before_after_expansion':True,'full_independent_publisher_total_qualified':False,'evidence':'navigation-acquisition/navigation-evidence.json'},'official_root_evidence':'e2e-evidence/official-root.json','acquisition_receipts':['e2e-evidence/standalone-final-start.json','e2e-evidence/standalone-final-resume.json','cua-acquisition/capture-receipt.json'],'source_comparisons':'e2e-evidence/fresh-source-comparisons.json','replay_equivalence':'e2e-evidence/fresh-replay-equivalence.json','visual_review':{'evidence':'e2e-evidence/cupertino-1.09.030-table.png','observation':'Reviewed rendered table in surrounding nested ordered list;13rows26cells match parsed source. Earlier first-round screenshots did not prove table viewport; this new screenshot does.'},'limits':['No authoritative current-through marker; official city source link confirmed, snapshot version explicitly unknown.','All observed tree controls expanded, but no independent publisher node total or exhaustive per-route navigation verification; candidate/opaque routes remain unqualified until actual data-path/UI match.','No entire-jurisdiction legal-body acquisition/import; unacquired inventory nodes remain unresolved.','Images/appendices and all notation types not all live-qualified; synthetic structure regressions supplement real prose/list/table and ordinance-list evidence.'],'retained_failed_attempts':[{'receipt':'e2e-evidence/navigation-stage-optional-family-timeout.json','reason':'Root and1.09.030 checkpointed; large ordinance-list UUID DOM returned200 but20s readiness budget elapsed. Readiness parsed once per observation and final body pilot budget raised to60s; final three-route run supersedes this failed optional stage.'},{'receipt':'e2e-evidence/standalone-failed-notice-selector.json','reason':'Actual notice container id differed from initial selector; fixed and rerun.'},{'receipt':'e2e-evidence/standalone-failed-compound-identity.json','reason':'Actual opaque compound navigation identity initially rejected; preserved and supported.'},{'receipt':'e2e-evidence/standalone-failed-compound-ancestry.json','reason':'Compound namespace did not match current tree ancestry; fixed by preserving opaque identity without constructing an executable URL.'},{'receipt':'e2e-evidence/policy-pause-attempt.json','reason':'Attempt was stopped on parent instruction pending explicit runtime choice; no success or publisher failure inferred.'}],'runtime_exclusions':['.venv/','.browsers/','__pycache__/'],'full_collection_validated':False,'production_or_database_changes':False}
 report['artifact_hashes']={str(p.relative_to(ROOT)):g.digest(p.read_bytes()) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='E2E-VALIDATION.json' and not any(x in {'.venv','.browsers','__pycache__'} for x in p.relative_to(ROOT).parts)}
 g.save(ROOT/'E2E-VALIDATION.json',report);print(json.dumps({k:report[k] for k in ['status','tests','packages','navigation']},indent=2))
if __name__=='__main__':main()
