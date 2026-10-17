#!/usr/bin/env python3
"""Build every publication's original-scope acceptance gaps; no publisher requests.

The prior representative matrix is evidence, never a substitute for target proof.
New exact publication receipts can be supplied explicitly with --receipts.
"""
import argparse,hashlib,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'collectors/registry'))
from catalog import load_catalog
from dispatch import qualified,Unsupported,command
HERE=Path(__file__).resolve().parent
REQUIREMENTS={
 'identity':'Exact government/state/publication/source identity independently bound to raw acquisition',
 'full_inventory':'Entire original selected publication inventory reconstructed from source, not output IDs',
 'owned_text':'Every required source unit parsed once with substantive own content or explicit source-backed exemption',
 'required_nonimage_documents':'All required nonimage documents qualified; unresolved references remain gaps',
 'table_fidelity':'Independent source table cell text/tag/rowspan/colspan reconciliation for actual publication tables',
 'image_policy':'No separate image bytes; ordered literal [IMAGE], inert HTML and payload-free metadata',
 'closing_consistency':'Pinned immutable source or publication/item closing consistency witnesses',
 'resume_integrity':'Actual interrupted/resumed publication run matches uninterrupted source-bound result',
 'fresh_setup_cli':'Fresh supported setup and exact publication launcher collect/verify entrypoints tested',
 'legal_structure':'Required legal hierarchy/section/list/note/link fidelity qualified for actual source format',
}
def read(p):return json.loads(Path(p).read_text())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--receipts',type=Path);ap.add_argument('--project',type=Path,default=ROOT.parents[1]);ap.add_argument('--access-stops',type=Path);a=ap.parse_args()
 stop_receipts=read(a.access_stops).get('stops',[]) if a.access_stops else []
 for stop in stop_receipts:
  evidence=stop['evidence'];source=a.project/evidence['path']
  if not source.is_file() or digest(source)!=evidence['sha256']:raise ValueError('Access stop receipt missing/corrupt')
 cat=load_catalog();tb={t['id']:t for t in cat['targets']};old=read(HERE/'validation-matrix.json');proofs=old['selected_live_or_retained_proofs'];receipts=read(a.receipts).get('receipts',[]) if a.receipts else [];rows=[]
 for pub in cat['publications']:
  target=tb[pub['target_id']];evidence=[p for p in proofs if pub['id'] in p['publication_ids']];checks={k:{'status':'not_established','requirement':v,'evidence':[]} for k,v in REQUIREMENTS.items()}
  for p in evidence:
   ref={'path':'outputs/full-publication-validation-2026-10-17/'+p['evidence_run']+'/coverage.json','sha256':p['coverage_sha256'],'proof_scope':p['scope_class'],'kind':'retained_prior_stage_report_not_new_readiness_acceptance'}
   checks['identity']['status']='prior_evidence';checks['identity']['evidence'].append(ref)
   for key,field in [('owned_text','publication_text_complete'),('required_nonimage_documents','attachments_complete'),('closing_consistency','edition_complete')]:
    checks[key]['evidence'].append(ref);checks[key]['status']='prior_evidence' if p[field] else 'gap'
   # Native-page outcomes cannot qualify section/table equivalence.
   if p.get('native_files_or_pages_complete'):checks['legal_structure']['status']='gap';checks['legal_structure']['reason']='Native file/page extraction does not establish legal section/table equivalence'
  actual=[r for r in receipts if r.get('publication_id')==pub['id']]
  for receipt in actual:
   for key,check in receipt.get('requirements',{}).items():
    if key not in checks:raise ValueError('Unknown requirement '+key)
    if check['status'] not in ('pass','gap','not_applicable','not_established'):raise ValueError('Invalid receipt status')
    if check['status'] in ('pass','not_applicable') and not check.get('evidence'):raise ValueError('Positive requirement needs exact evidence')
    for evidence in check.get('evidence',[]):
     if 'path' not in evidence or 'sha256' not in evidence:raise ValueError('Readiness receipt needs exact path+SHA256')
     source=a.project/evidence['path']
     if not source.is_file() or digest(source)!=evidence['sha256']:raise ValueError('Readiness evidence missing/corrupt: '+evidence['path'])
    checks[key]=dict(check,requirement=REQUIREMENTS[key])
  try:q=qualified(pub,target);dispatchable=True;unsupported=None;plan=command(pub,target,'{OUT}')
  except Unsupported as exc:dispatchable=False;unsupported=str(exc);plan=None
  applicable_stops=[s for s in stop_receipts if s['family'] in (pub['source_family'],pub['publisher'])]
  blocked=pub['source_family'] in ('ecode360','municipal.codes') or bool(applicable_stops)
  gaps=[]
  if not dispatchable:gaps.append({'kind':'configuration','reason':unsupported})
  if blocked:gaps.append({'kind':'access_stop','reason':'Existing publisher403/429 stop; new requests prohibited. Offline reparse does not establish fresh current-source completion. See exact access_stop_evidence.'})
  for key,check in checks.items():
   if check['status'] not in ('pass','not_applicable'):gaps.append({'kind':key,'reason':check.get('reason',REQUIREMENTS[key]),'status':check['status']})
  if pub.get('scope_kind')=='publication_candidate':gaps.append({'kind':'scope_discovery','reason':'Original candidate has not yet been qualified as independently published required/current law; do not substitute a narrower chapter or generic landing.'})
  for dependency in pub.get('required_publication_dependencies',[]):gaps.append({'kind':'required_publication_dependency','publication_id':dependency,'reason':'Whole separate dependency requires its own qualified collection and verification; a cover/chapter or hyperlink is not dependency closure'})
  rows.append({'publication_id':pub['id'],'target_id':pub['target_id'],'cohort':target.get('cohort','expansion'),'jurisdiction':target['jurisdiction'],'state':target['state'],'title':pub['title'],'original_source_url':pub.get('original_source_url',pub['source_url']),'active_source_url':pub['source_url'],'original_scope_kind':pub['scope_kind'],'role':pub['role'],'required_for_jurisdiction':pub['required_for_jurisdiction'],'jurisdiction_scope':pub.get('jurisdiction_scope'),'edition_scope':pub.get('edition_scope'),'configuration_alias_of':pub.get('configuration_alias_of'),'required_publication_dependencies':pub.get('required_publication_dependencies',[]),'publisher':pub['publisher'],'source_family':pub['source_family'],'expected_identity':pub['expected_identity'],'source_evidence_paths':pub['evidence_paths'],'dispatchable_config':dispatchable,'operational_access_prohibited':blocked,'access_stop_evidence':applicable_stops,'dispatch_plan':plan,'prior_exact_proofs':evidence,'new_readiness_receipts':actual,'requirements':checks,'readiness_verified':not gaps,'gaps':gaps,'jurisdiction_complete':False})
 unresolved=[]
 for t in cat['targets']:
  for x in t.get('known_publications',[])+t.get('unresolved_required_scope',[]):
   if x.get('required_for_jurisdiction',True) and x.get('relationship') not in ('embedded_primary','publication_control') and not x.get('publication_id') and not x.get('covered_by_publication_id') and not x.get('runnable_via'):
    unresolved.append({'target_id':t['id'],'scope':x,'status':'unresolved_scope_not_a_concrete_publication_config'})
 report={'schema_version':1,'stage':'collection-readiness-2026-10-17','purpose':'Original-scope per-publication requirement ledger across expansion100 and original30; family tests never qualify another publication','source_inputs':{'access_stops_sha256':digest(a.access_stops) if a.access_stops else None,'active_catalog_sha256':hashlib.sha256(json.dumps(cat,sort_keys=True).encode()).hexdigest(),'readiness_overrides_sha256':digest(ROOT/'collectors/registry/readiness-overrides.json'),'readiness_qualified_sha256':digest(ROOT/'collectors/registry/readiness-qualified-configs.json'),'readiness_additional_sha256':digest(ROOT/'collectors/registry/readiness-additional-publications.json'),'prior_matrix_sha256':digest(HERE/'validation-matrix.json'),'targets_sha256':digest(ROOT/'collectors/registry/targets.json'),'publications_sha256':digest(ROOT/'collectors/registry/publications.json'),'original_targets_sha256':digest(ROOT/'collectors/registry/original-targets.json'),'original_publications_sha256':digest(ROOT/'collectors/registry/original-publications.json')},'summary':{'targets':len(cat['targets']),'publication_entries':len(rows),'primary':sum(r['role']=='primary' for r in rows),'secondary':sum(r['role']=='secondary' for r in rows),'dispatchable':sum(r['dispatchable_config'] for r in rows),'unqualified':sum(not r['dispatchable_config'] for r in rows),'access_prohibited':sum(r['operational_access_prohibited'] for r in rows),'readiness_verified':sum(r['readiness_verified'] for r in rows),'new_exact_requirements_passed':{key:sum(r['requirements'][key]['status']=='pass' for r in rows) for key in REQUIREMENTS},'unresolved_scope_items':len(unresolved),'by_publisher':dict(Counter(r['publisher'] for r in rows))},'publications':rows,'unresolved_jurisdiction_scope':unresolved,'operational_controls':{'durable_stop_recovery':'Implemented and independently fault-tested with isolated STATE_ROOT: publisher stops survive lost tmp files and new outputs; external stops remain host-scoped. This synthetic operational check does not confer a target publication pass.','dependency_proofs':'Explicit catalog-bound --dependency PUB=OUT is independently reverified offline; missing/mismatched/incomplete proofs remain gaps.','image_policy':'Literal [IMAGE] in normalized text/HTML/notes; no separate image acquisition, no inline pixel payload in normalized metadata.'},'operational_gaps':[{'id':'all-target-live-readiness','reason':'Per-publication original-scope acquisition/verification/resume and legal-structure acceptance remain explicitly measured below. A unified runtime/family test is not inherited by every publication.'}],'jurisdiction_complete':False}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary']))
if __name__=='__main__':main()
