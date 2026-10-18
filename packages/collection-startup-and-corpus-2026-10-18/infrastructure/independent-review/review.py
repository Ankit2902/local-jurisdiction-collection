#!/usr/bin/env python3
"""Read-only retained Infrastructure outputs/receipts review; no native parser APIs."""
import ast,csv,hashlib,json,pathlib,subprocess,sys
P=pathlib.Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'github/local-jurisdiction-collection').is_dir())
S=ROOT/'outputs/collection-readiness-post1997ee1-2026-10-17/official/infrastructure-full62-operational-proof-v1'
REPO=ROOT/'github/local-jurisdiction-collection'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=lambda p:json.loads(p.read_text())
def inventory(p):return {str(f.relative_to(p)):h(f) for f in sorted(p.rglob('*')) if f.is_file()}
before=inventory(S)
assert h(S/'MANIFEST.sha256')=='481fce6648a4863f3182151af2ed1546a4990a2077e3e00c3bd542db63f698e8'
assert h(S/'MANIFEST.json')=='f211d7927b8b8e528310bce71ddea269e7692785df25348e32001dc32e2534a7'
quick=subprocess.run([sys.executable,'-B',str(S/'verify_proof.py')],capture_output=True,text=True)
(P/'portable-verifier.stdout').write_text(quick.stdout);(P/'portable-verifier.stderr').write_text(quick.stderr)
assert quick.returncode==0,quick.stderr
rows=[json.loads(s) for s in (S/'run/records.jsonl').read_text().splitlines() if s]
assert len(rows)==len({x['id'] for x in rows})==62
csvrows=list(csv.DictReader((S/'run/records.csv').open()))
assert len(csvrows)==62 and all(all(c[k]==str(x[k]) for k in c) for c,x in zip(csvrows,rows))
source='915fe1fdf8ff5da33acfce7d08637808cb57886fbbc7f157b2b81bfcf970827c'
baseline=ROOT/'outputs/collection-readiness-post1997ee1-2026-10-17/official/infrastructure-canonical-candidate-v2/derivative-current/records.jsonl'
assert h(baseline)=='95e28ea3fa4a60f30cf6b55a33d12f49ca04c3b6895ceca85bfe43af3355d58a'
prior={x['physical_page']:x for x in map(json.loads,baseline.read_text().splitlines()) if x.get('raw_sha256')==source}
assert len(prior)==62
def namespace(v):
 if isinstance(v,str) and v.startswith('overland-required-0768ee8be4a8::'):return '82-0c6b3dc40877::'+v.split('::',1)[1]
 if isinstance(v,list):return [namespace(x) for x in v]
 if isinstance(v,dict):return {k:namespace(x) for k,x in v.items()}
 return v
selected=[x for x in rows if x.get('canonical_structure_selection')]
assert [x['physical_page'] for x in selected]==[2,3,6,46]
for x in rows:
 old=prior[x['physical_page']]
 assert x['text']==old['text']
 assert x['ordered_blocks']==namespace(old['ordered_blocks'])
 assert x['tables']==namespace(old['tables'])
 if x.get('superseded_detector_diagnostics'):
  assert x['superseded_detector_diagnostics']['original_record_fields']==namespace(old['superseded_detector_diagnostics']['original_record_fields'])
markers=[{'physical_page':x['physical_page'],'ordinal':n,'block':b} for x in rows for n,b in enumerate(x['ordered_blocks']) if b.get('type')=='image']
# The parser's image discriminator is source-owned and may use kind rather than type.
imageblocks=[{'page':x['physical_page'],'ordinal':n,'block':b} for x in rows for n,b in enumerate(x['ordered_blocks']) if b.get('kind')=='image' or b.get('type')=='image']
assert sum(x['text'].count('[IMAGE]') for x in rows)==5
coverage=r(S/'run/coverage.json');dims=coverage['pdf_details']['source_infrastructure_dimensions']
assert sum(x['pdf_qualification']['detected_table_cells'] for x in rows)==149
assert sum(x['pdf_qualification']['independent_table_cells_agree'] for x in rows)==149
assert dims['original_failed_detector_cells_retained']==44 and dims['literal_leader_folio_spacing_discrepancies']==3
assert not dims['full_line_spacing_complete'] and not dims['whole_book_semantic_or_table_completeness_qualified']
common=r(S/'evidence/infrastructure-full62-current-final-v3-common-receipt.json')
guard=r(S/'evidence/infrastructure-full62-current-final-v3-replay-receipt.json')
assert common['verification_exit']==0 and common['family_verifier_passed'] and len(common['evidence_sha256_before'])==52
assert common['evidence_sha256_before']==common['evidence_sha256_after']
assert common['collector_sources_before']==common['collector_sources_after']
current={name:h(REPO/name) for name in common['collector_sources_after']}
assert current==common['collector_sources_after'],'Current source no longer matches executed common tuple'
assert guard['driver_sha256']==h(S/'runtime/retained_native.py')
assert guard['forbidden_calls']==[] and guard['image_api_accesses']==0 and guard['current_network_requests']==0
assert len(guard['retained_transport_calls'])==2
# Inspect actual external adapter: only native.cached is substituted; source parser/verification stays real.
tree=ast.parse((S/'runtime/retained_native.py').read_text())
nativepatches=[n.args[1].value for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='object' and len(n.args)>1 and isinstance(n.args[0],ast.Name) and n.args[0].id=='native' and isinstance(n.args[1],ast.Constant)]
assert nativepatches==['cached'],nativepatches
native=(S/'runtime/collectors/encodeplus/native_document.py').read_text()
assert 'report=verify(out);' in native and 'records,details=page_records(bodies[0]' in native
sys.path.insert(0,str(REPO));sys.dont_write_bytecode=True
from collectors.ops.launcher import publication_acceptance
acceptance=publication_acceptance(common['publication'],S/'run')
expected=dict(common['acceptance']);expected.pop('publication_accepted')
assert acceptance==expected,'Current common acceptance no longer matches actual receipt'
assert acceptance['native_capture_verified'] and not any(acceptance[k] for k in ['publication_coverage_accepted','publication_text_complete','required_nonimage_documents_complete','legal_structure_qualified','edition_complete','jurisdiction_complete'])
rt=r(S/'runtime/runtime-info.json')
assert rt['python'].startswith('3.12.14')
assert rt['packages']['pypdf']=='6.21.1' and rt['packages']['pdfminer.six']=='20251107'
assert inventory(S)==before,'Reviewed source packet changed'
report={'status':'passed','source_packet':str(S.relative_to(ROOT)),'source_manifest_sha256':h(S/'MANIFEST.json'),'source_files_before_after_equal':True,'source_files':len(before),'portable_verifier_exit':quick.returncode,'independent_checks':{'records_json_csv':62,'all62_text_blocks_tables_equal_prior_source_proof_modulo_explicit_document_namespace':True,'four_regions':[2,3,6,46],'exact_old_detector_fields_retained':True,'canonical_cells_qualified':149,'old_failed_cells_retained':44,'spacing_discrepancies_retained':3,'image_placeholders':5,'output_files_common_readonly':52,'current_common_sources_exact':len(current),'current_common_acceptance_recomputed':True,'native_adapter_only_substitutes_cached_transport':True},'native_workflow':{'standard_collect_including_strictverify':True,'final_success':'v3','exit':0,'retained_source':True,'fresh_live_or_currentness_credit':False,'network_and_image_calls_reported':0},'acceptance':acceptance,'review_runtime':sys.version,'review_limits':['Read-only outputs/source/receipt review, not a repeated62-page native parse or independent table-cell geometry query','Actual full native parsing and common CLI execution are supplied by frozen finalV3 receipts; v1/v2 unsuccessful adapter histories remain historical','Wholebook legal/table/order/adopted-edition/external-dependency qualification remains false'],'no_production_or_packet_writes':True}
(P/'review.json').write_text(json.dumps(report,indent=2)+'\n')
(P/'source-before-after.json').write_text(json.dumps({'before':before,'after':inventory(S)},indent=2)+'\n')
print(json.dumps({'status':'passed','source_files':len(before),'current_sources':len(current),'rows':62,'image_placeholders':5,'common_acceptance':False}))
