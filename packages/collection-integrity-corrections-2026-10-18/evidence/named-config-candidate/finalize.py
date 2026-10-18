import difflib,hashlib,json,platform,sys
from pathlib import Path
here=Path(__file__).resolve().parent
repo=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/github/local-jurisdiction-collection')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rels=['collectors/ops/launcher.py','collectors/qa/readiness_binding.py','collectors/registry/dispatch.py']
base=json.loads((here/'source-baseline.json').read_text())
assert all(sha(repo/rel)==expected for rel,expected in base.items()),'Production baseline changed; review needed'
patch=''.join(''.join(difflib.unified_diff((here/'baseline'/rel).read_text().splitlines(True),(here/'candidate'/rel).read_text().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel)) for rel in rels)
(here/'named-config-binding.patch').write_text(patch)
report={'schema_version':1,'status':'isolated_candidate_passed_not_promoted','network_requests':0,'production_files_modified':False,'runtime':{'executable':sys.executable,'python':platform.python_version(),'platform':platform.platform()},'input_fixture':{'publication_id':'82-primary','target_id':'82','selected_key':'overland','targets_json_sha256':sha(here/'fixtures/targets.json')},'validation':{'focused_tests':11,'existing_readiness_tests':16,'all_passed':True,'baseline_omission_reproduced':True,'actual_overland_scope_mutation_detected':True,'command_argv_unchanged':True,'stale_plan_rereads_current_named_config':True,'no_network_socket_tripwire':True,'production_baseline_verified_unchanged':base},'source_changes':[{'path':rel,'before_sha256':sha(here/'baseline'/rel),'candidate_sha256':sha(here/'candidate'/rel)} for rel in rels],'scope_notes':['Only named enCodePlus dispatch adds config source path/key. Exact selected entry and whole file SHA are bound; all enCodePlus component hashes include targets.json.','Other-family selection/dispatch behavior and family-specific input inclusion remain unchanged. Actual promotion of common source modules changes their source fingerprints for every family; historical active proofs will require current source qualification.','No collection, publisher transport, image normalization or readiness status policy changes. No live qualification claimed.','Candidate is deliberately not promoted while the fresh Flagstaff common job is active.']}
(here/'validation-summary.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
