"""Maintain post-checkpoint scope without rewriting the sealed requirement ledger."""
import argparse,collections,copy,hashlib,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];PROJECT=ROOT.parents[1];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'collectors/registry'))
from catalog import load_catalog
from dispatch import command,Unsupported
from readiness_binding import assess,current_components,canonical,selected_configuration,implementation_family

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def refresh_catalog_operational_state(row,pub,prior_ledger):
 """Current dispatch/access fields come only from catalog; no readiness credit.

 Prior copied fields remain explicitly historical, never mixed with current
 advisories or mistaken for current configuration qualification.
 """
 prior_fields={key:copy.deepcopy(row[key]) for key in ('dispatchable_config','operational_access_prohibited','access_stop_evidence') if key in row}
 if prior_fields:
  row['historical_operational_state']={'source_ledger':copy.deepcopy(prior_ledger),'scope':'Copied prior checkpoint fields; not current dispatch/access authority','values':prior_fields}
 advisories=copy.deepcopy(pub.get('observed_access_advisories',[]))
 row.update(dispatchable_config=pub['runnable'],configuration_qualified=pub['runnable'],operational_access_prohibited=bool(advisories),access_stop_evidence=copy.deepcopy(advisories),observed_access_advisories=advisories)
 return row

def build(proof_paths=(),source_scope_paths=()):
 priorpath=HERE/'readiness-requirements.json';prior=json.loads(priorpath.read_text());old={p['publication_id']:p for p in prior['publications']};catalog=load_catalog();targets={t['id']:t for t in catalog['targets']};rows=[];out=PROJECT/'outputs/collection-readiness-followup-2026-10-17/qa';descriptions={k:v['requirement'] for k,v in prior['publications'][0]['requirements'].items()};components={implementation_family(p):current_components(ROOT,p) for p in catalog['publications']}
 active_proofs={}
 for path in proof_paths:
  value=json.loads(Path(path).read_text());ident=value['publication_id']
  if ident in active_proofs:raise ValueError('Duplicate active proof publication')
  active_proofs[ident]=value
 scoped={}
 for path in source_scope_paths:
  from bind_flagstaff_source_scope import bind
  saved=json.loads(Path(path).read_text());proof_path=PROJECT/saved['active_proof_path']
  if sha(proof_path)!=saved['active_proof_sha256']:raise ValueError('Changed source-scope active proof')
  with tempfile.TemporaryDirectory() as td:
   current=bind(proof_path,Path(path).parent,Path(td)/'revalidated.json')
  if current!=saved:raise ValueError('Changed source-scope/current revision evidence')
  ident=current['publication_id']
  if ident in scoped:raise ValueError('Duplicate source dimensions')
  scoped[ident]=current
  actual=json.loads(proof_path.read_text())
  if ident in active_proofs and active_proofs[ident]!=actual:raise ValueError('Conflicting actual proof')
  active_proofs[ident]=actual
 def evidence(name):
  p=out/name;return {'path':str(p.relative_to(PROJECT)),'sha256':sha(p)}
 def requirement(row,key,status,reason,names):row['requirements'][key]={'status':status,'requirement':descriptions[key],'reason':reason,'evidence':[evidence(n) for n in names]}
 for pub in catalog['publications']:
  ident=pub['id'];target=targets[pub['target_id']]
  row=copy.deepcopy(old.get(ident,{'publication_id':ident,'target_id':pub['target_id'],'cohort':'original' if pub['target_id'].startswith('original-') else 'expansion','jurisdiction':target['jurisdiction'],'state':target['state'],'requirements':{k:{'status':'not_established','requirement':v,'evidence':[]} for k,v in descriptions.items()},'jurisdiction_complete':False}))
  row.update(title=pub['title'],role=pub['role'],required_for_jurisdiction=pub['required_for_jurisdiction'],active_source_url=pub['source_url'],publisher=pub['publisher'],adapter_family=implementation_family(pub),source_family=pub['source_family'],configuration_qualified=pub['runnable'],unsupported_reason=pub.get('unsupported_reason'),expected_identity=pub.get('expected_identity'),required_publication_dependencies=pub.get('required_publication_dependencies',[]),observed_access_advisories=pub.get('observed_access_advisories',[]),followup_qualification=pub.get('qualification_evidence'),image_policy=pub['image_policy'])
  refresh_catalog_operational_state(row,pub,{'path':str(priorpath.relative_to(ROOT)),'sha256':sha(priorpath)})
  row.setdefault('original_source_url',pub.get('original_source_url',pub['source_url']));row.setdefault('original_scope_kind',pub['scope_kind']);row['scope_narrowed_for_pass']=False
  try:row['dispatch_plan']=command(pub,target,'{OUT}')
  except Unsupported as error:row['dispatch_plan']={'runnable':False,'unsupported_reason':str(error)}
  if ident=='20-primary':
   requirement(row,'full_inventory','pass','All10853original archive files reconstruct the independently retained Git commit root; all8445canonical source pages reconcile to records or explicit dispositions. This does not establish correctness of the exclusions.',['baltimore-git-source-binding.json'])
   requirement(row,'owned_text','gap','Actual raw-source audit finds15noncanonical legal headings across5attachment pages removed and their pages wrongly excluded; original source is retained, corrected exact-source derivatives are retained separately; no current-runtime acceptance inferred.',['baltimore-raw-dom.json'])
   requirement(row,'table_fidelity','gap','Independent original browser DOM checks172tables/12119cells:73celltext mismatches from inline separator insertion. Tags/spans/nesting agree.',['baltimore-raw-dom.json'])
   requirement(row,'closing_consistency','pass','Original archive matches independently captured immutable commit tree, including names/modes/bytes of every member; closing commit was retained by owner. Required external document closing is a separate remaining audit.',['baltimore-git-source-binding.json'])
   requirement(row,'legal_structure','gap','Lost embedded attachment bodies and210source-heading-only inherited model-code units prohibit full legal-semantic acceptance.',['baltimore-git-source-binding.json','baltimore-raw-dom.json'])
   candidate='baltimore-candidate-v2-inert-dom.json'
   if (out/candidate).exists() and json.loads((out/candidate).read_text())['passed']:
    requirement(row,'table_fidelity','candidate_pass','Candidate retained-source replay: all 172 tables/12,119 cells match independent original browser DOM. The original failed 73-cell result stays retained. This receipt binds candidate b66b80e3; later producer/current-redactor revisions require their own exact bindings.',['baltimore-raw-dom.json',candidate])
    requirement(row,'owned_text','gap','Candidate retains all 15 embedded headings and five omitted attachment bodies, but 210 inherited source-heading-only units and whole-body legal qualification remain open. Later fresh producer model2c/current guarded redactor are separate revisions.',['baltimore-raw-dom.json',candidate])
    requirement(row,'legal_structure','gap','Embedded body and inline-cell defects are closed in the candidate retained replay. Inherited model-code bodies/edition applicability and full legal structure remain qualified; later production promotion does not automatically inherit this candidate proof scope.',['baltimore-git-source-binding.json',candidate])
    row['candidate_embedded_body_correction']={'status':'candidate_pass','model_sha256':'b66b80e36623f46a0846ee07385c058dfe1146ca36666d73c1afb06e221860f3','records_sha256':'58edaf7a60fff25317bec8e2ab91aca49e001c26f3611e0c52e21ace6127f285','scope':'All 15 embedded source headings and five original exclusive attachment body texts retained exactly; candidate source replay only, not new production/live qualification.','evidence':evidence(candidate)}
   row['followup_image_dimensions']=[evidence('baltimore-normalized-images.json'),evidence('actual-no-image-bytes.json')]
   row['followup_status_note']='Fresh final-live-v3 owner acquisition/closing completed with6994records under model2c; guarded14699e62 current source has explicit actual-input applicability scans. Historical and candidate receipts remain version-specific; inherited model-code legal qualification is unresolved.'
  if ident=='59-primary':
   graph='cleveland-raw-inventory-and-ownership-v2.json'
   if (out/graph).exists() and json.loads((out/graph).read_text())['passed']:
    requirement(row,'full_inventory','pass','Independent start/end overview+459branch sweeps each reconstruct6140source IDs; all43676native rich blocks owned exactlyonce,5virtual source-backed grouping branches checked.',['cleveland-raw-inventory-and-ownership-v2.json'])
    requirement(row,'closing_consistency','pass','Independent source graph and version match across distinct closing459branch responses acquired after same-job native export.',['cleveland-raw-inventory-and-ownership-v2.json'])
   requirement(row,'owned_text','gap','Full native block presence/ID ownership is established, but serialized source cell text has31inline separator differences; exact whole body and required PDF semantics not yet qualified.',['cleveland-raw-dom-tables.json'])
   requirement(row,'table_fidelity','gap','Original independent browser DOM:322tables/7738cells,31celltext mismatches. Original same-separator auditor passed; candidate correction awaiting independent recheck.',['cleveland-original-table-audit.json','cleveland-raw-dom-tables.json'])
   requirement(row,'required_nonimage_documents','capture_only','Owner retains all5required original PDFs and5physical page records. Byte capture is separate from required PDF table/legal-structure qualification; current family semantic flags remain false.',['cleveland-raw-dom-tables.json'])
   requirement(row,'legal_structure','gap','31HTMLtable cell serialization differences plus required-PDF semantic/table flags false prevent full legal-publication acceptance, even though family publication_complete is true.',['cleveland-raw-dom-tables.json'])
   final_table='cleveland-final-v6-inert-dom-tables.json';final_pdf='cleveland-final-v6-independent-pdf-v2.json'
   if all((out/name).exists() and json.loads((out/name).read_text())['passed'] for name in [final_table,final_pdf]):
    requirement(row,'table_fidelity','candidate_pass','Final immutable v6 retained-source replay: all322originalHTMLtables/7738cells match inert-before-attachment browser; required native closed grid18cells/glyphs/borders also match. Active-runtime coherence remains separate.',[final_table,final_pdf])
    requirement(row,'required_nonimage_documents','candidate_pass','Five exact requiredPDF originals independentlychecked:4source-no-glyph pages are policy N/A with[IMAGE]; fifth18cellgrid/2201nonwhitespaceglyphs/188border-path edges/9markers matches. No imagesdecoded; current source/config/runtime qualification remains separate.',[final_pdf])
    row['candidate_corrected_source_fidelity']={'status':'candidate_pass','records_sha256':'8901a412094e0009e7a19c811e75cc8eaf9126619c952ea8ceb5df982dbac738','pdf_pages_sha256':'2bb228fb04c9996bbb6916a7c12815c974f1c0b2ff352f29d0e97d6af55a0dd2','evidence':[evidence(final_table),evidence(final_pdf)]}
   row['followup_image_dimensions']=[evidence('cleveland-normalized-images.json'),evidence('actual-no-image-bytes.json')]
   row['followup_status_note']='Terminal full live v3 HTML/native graph proof; not a full legal-semantic publication pass. Original v3 remains failed on31inlinecell differences. Final immutable v6 candidate tables/nativePDF dimensions pass independent checks; active-runtime binding and wholepublication acceptance remain separate.'
  if pub.get('adapter_mode')=='native_document':
   row['native_configuration_evidence']=evidence('native-config-current-anchor-qualified.json');row['native_capture_is_not_publication_acceptance']=True;row['followup_status_note']='Current literal publisher link plus exact native file SHA/pages qualifies dispatch only; fresh common-launcher proof pending. Original publication requirements remain.'
   if ident=='82-4b983dc51ab6' and (out/'solid-waste-common-readonly-verify.json').exists():
    proof=json.loads((out/'solid-waste-common-readonly-verify.json').read_text())
    row['native_capture_proof']={'status':'verified-native-capture-only','physical_pages':6,'family_verification_exit':proof['verification_exit'],'native_capture_verified':proof['acceptance']['native_capture_verified'],'publication_accepted':proof['acceptance']['publication_accepted'],'source_changed_during_run':proof['source_changed_during_run'],'evidence':evidence('solid-waste-common-readonly-verify.json')}
    row['followup_status_note']='Actual fresh common runtime acquisition and independent read-only verification pass native capture/pages; overall exit2 preserves explicit text/document/semantic/edition gaps. No strict publication readiness inferred.'

  if pub['publisher']=='encodeplus' and pub['runnable'] and 'collectors.encodeplus.collect' in row['dispatch_plan'].get('argv',[]) and not row['dispatch_plan'].get('qualified_config_path') and not row['dispatch_plan'].get('staged_config') and not row['dispatch_plan'].get('named_config_path'):
   row['operational_input_binding_gap']={'status':'gap','input':'collectors/encodeplus/targets.json','reason':'Named enCodePlus config is captured in the family checkpoint but not in shared component/selected-config hashes. Actual frozen input has not changed; no proof invalidation or routing change inferred. Input-hash coverage fix deferred until active frozen jobs finish.','evidence_path':'outputs/collection-readiness-post-91f6c59-2026-10-17/qa/ep-named-config-binding-omission.json'}
   row['requirements']['fresh_setup_cli']={'status':'gap','requirement':descriptions['fresh_setup_cli'],'reason':row['operational_input_binding_gap']['reason'],'evidence':[]}
  if ident in scoped:
   row['scoped_source_qualification']=scoped[ident]
   row['followup_status_note']='Current common readonly verification accepts the retained Flagstaff primary under exact source/config/runtime/artifact tuple; six independently tested source/image dimensions bind that same tuple. Actual interrupted-resume, fresh live workflow and additional legal-structure/document dimensions are not inferred. Handbook is separate unresolved scope.'
   for key,qualification in scoped[ident]['requirements'].items():
    row['requirements'][key]={**qualification,'requirement':descriptions[key]}
  if ident in active_proofs:row['active_runtime_proof']=active_proofs[ident]
  row['selected_configuration_sha256']=selected_configuration(ROOT,pub,target,row['dispatch_plan'])['sha256']
  row['active_readiness_binding']=assess(row,ROOT,PROJECT,components[implementation_family(pub)],row['selected_configuration_sha256'])
  row['readiness_verified']=row['active_readiness_binding']['accepted']
  discovery=HERE/'followup-proof-receipts/overland-discovery-context.json'
  if pub['target_id']=='82' and discovery.exists():
   found=next((v for v in json.loads(discovery.read_text())['entries'] if v['publication_id']==ident),None)
   if found:row['discovery_candidate_classification']={**found,'requirements_preserved':True,'evidence':{'path':str(discovery.relative_to(ROOT)),'sha256':sha(discovery)}}
  row['evidence_applicability']='Historical and candidate dimensions remain retained; active readiness additionally requires one current component/config/record scope with bound current image transport and artifact audits.'
  row['gaps']=[{'kind':'access_stop','reason':a['reason'],'evidence':a.get('raw_refusal_witness')} for a in row['observed_access_advisories']]+[{'kind':k,'status':v['status'],'reason':v.get('reason',v['requirement'])} for k,v in row['requirements'].items() if v['status']!='pass']
  if not row['active_readiness_binding']['accepted']:row['gaps'].append({'kind':'active_revision_coherence','reason':row['active_readiness_binding']['errors']})
  rows.append(row)
 summary={'targets':len(targets),'publication_entries':len(rows),'primary':sum(r['role']=='primary' for r in rows),'secondary':sum(r['role']=='secondary' for r in rows),'dispatchable':sum(r['configuration_qualified'] for r in rows),'unqualified':sum(not r['configuration_qualified'] for r in rows),'access_prohibited':sum(bool(r['observed_access_advisories']) for r in rows),'readiness_verified':sum(r['readiness_verified'] for r in rows),'requirements_candidate_passed':{key:sum(r['requirements'][key]['status']=='candidate_pass' for r in rows) for key in descriptions},'active_bound_requirement_passes':{key:sum(r['requirements'][key]['status']=='pass' and r['requirements'][key].get('proof_scope_id')==r.get('active_runtime_proof',{}).get('scope_id') and bool(r.get('scoped_source_qualification')) for r in rows) for key in descriptions},'historical_or_unbound_requirement_passes':{key:sum(r['requirements'][key]['status']=='pass' and not (r['requirements'][key].get('proof_scope_id')==r.get('active_runtime_proof',{}).get('scope_id') and bool(r.get('scoped_source_qualification'))) for r in rows) for key in descriptions},'by_publisher':dict(collections.Counter(r['publisher'] for r in rows))}
 return {'schema_version':2,'stage':'post-91f6c59-operational-source-validation','purpose':'All original130governments and every current known publication/candidate; exact scope retained. Native capture/family tests/config qualification never confer another publication pass.','sealed_checkpoint_ledger':{'path':str(priorpath.relative_to(ROOT)),'sha256':sha(priorpath),'summary':prior['summary']},'active_catalog_sha256':hashlib.sha256(json.dumps(catalog,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'summary':summary,'publications':rows,'unresolved_jurisdiction_scope':prior['unresolved_jurisdiction_scope'],'additional_publication_discoveries':[{'target_id':'original-flagstaff-az','publication':'Employee Handbook','source_url':'https://www.codepublishing.com/AZ/Flagstaff/html/FlagstaffEmployeeHandbookNT.html','status':'separate_unqualified_discovery_outside_frozen225_catalog','required_scope_unresolved':True,'evidence_path':'outputs/collection-readiness-post-91f6c59-2026-10-17/qa/flagstaff-handbook-source-discovery-v1.json'}],'operational_gaps':([{'kind':'named-config-input-hash-coverage','reason':'One or more named configurations still lack an explicit shared selected-file binding; see per-publication gaps.'}] if any(row.get('operational_input_binding_gap') for row in rows) else [])+[{'kind':'known-access-stops','reason':'Municode/eCode360/municipal.codes/Gridics/American Legal observed workflow stops prohibit new acquisition until explicit operator review; no retry/reset. Exact event scope retained; no claim every public route is unavailable.'},{'kind':'actual-all-publication-proof','reason':'Most targets remain unverified at full source/body/structural/closing/resume scope; new terminal owner flags are independently audited before promotion.'}],'image_policy':{'literal':'[IMAGE]','no_separate_image_acquisition':True,'intentional_image_omission_is_not_completeness_failure':True,'native_originals_may_embed_images':True},'jurisdiction_complete':False,'sealed':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--active-proof',type=Path,action='append',default=[]);p.add_argument('--source-scope',type=Path,action='append',default=[]);a=p.parse_args()
 if a.out.resolve()==(HERE/'readiness-requirements.json').resolve():raise SystemExit('Cannot rewrite sealed checkpoint ledger')
 data=build(a.active_proof,a.source_scope);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data['summary'],indent=2))
