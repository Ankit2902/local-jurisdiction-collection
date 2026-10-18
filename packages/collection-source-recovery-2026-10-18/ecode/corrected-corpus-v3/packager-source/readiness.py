"""Scoped publication-export evidence. No legal-review or jurisdiction inference."""
import hashlib,json,re

SCHEMA='flagstaff-selected-publication-readiness-evidence-1'
CONTRACT='flagstaff-bound-common-publication-acceptance-1'
PUBLICATION='original-flagstaff-az-primary'
GATES=['standard_verification_passed','source_read_only_unchanged','source_code_runtime_unchanged','publication_identity_bound','coverage_report_bound','family_raw_replay_passed','publication_text_complete','required_nonimage_documents_complete','legal_structure_qualified','source_consistency_complete','primary_publication_accepted','required_publication_dependencies_qualified']
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def common_publication_evidence(proof,family,config,version,coverage,coverage_raw_sha256):
    """Called only by a reader that validates this exact common/family contract.

    Input/code/config/raw bindings are still mandatory reader/writer checks. The
    explicit standard common acceptance supplies structure/dependency scope; an
    arbitrary family success or serialized HTML alone is not that acceptance.
    """
    a=proof.get('acceptance');a=a if isinstance(a,dict) else {}
    before=proof.get('evidence_sha256_before');sources=proof.get('collector_sources_before')
    gates={
      'standard_verification_passed':proof.get('status')=='verified_publication' and proof.get('verification_exit')==0 and not isinstance(proof.get('verification_exit'),bool) and proof.get('family_verifier_passed') is True,
      'source_read_only_unchanged':proof.get('evidence_read_only') is True and proof.get('publisher_requests')==0 and not isinstance(proof.get('publisher_requests'),bool) and isinstance(before,dict) and bool(before) and before==proof.get('evidence_sha256_after'),
      'source_code_runtime_unchanged':proof.get('source_changed_during_run') is False and proof.get('runtime_changed_during_run') is False and isinstance(sources,dict) and bool(sources) and sources==proof.get('collector_sources_after'),
      'publication_identity_bound':proof.get('selected_config')==config==family.get('publication_config')==coverage.get('config'),
      'coverage_report_bound':a.get('coverage_sha256')==coverage_raw_sha256,
      'family_raw_replay_passed':family.get('full_raw_replay_equal') is True and family.get('input_files_modified') is False and family.get('source_route_ledger_verified') is True and family.get('opening_body_closing_chronology_verified') is True,
      'publication_text_complete':a.get('publication_text_complete') is True and coverage.get('publication_text_complete') is True and coverage.get('publication_bodies_acquired_and_owned') is True,
      'required_nonimage_documents_complete':a.get('required_nonimage_documents_complete') is True and coverage.get('attachments_complete') is True,
      'legal_structure_qualified':a.get('legal_structure_qualified') is True and coverage.get('legal_structure_qualified') is True,
      'source_consistency_complete':coverage.get('source_consistency_complete') is True,
      'primary_publication_accepted':a.get('publication_coverage_accepted') is True and a.get('publication_accepted') is True and a.get('acceptance_gaps')==[] and coverage.get('publication_accepted') is True and coverage.get('complete') is True,
      'required_publication_dependencies_qualified':a.get('unresolved_required_publication_dependencies')==[],
    }
    return {'schema':SCHEMA,'contract':CONTRACT,'publication_id':proof.get('publication_id'),'binding':{'configuration_sha256':digest(config),'source_version_sha256':digest(version),'inherited_coverage_sha256':digest(coverage),'common_receipt_canonical_sha256':digest(proof),'family_report_canonical_sha256':digest(family),'source_input_inventory_sha256':digest(before),'coverage_raw_sha256':coverage_raw_sha256},'gates':gates,'scope':'Only selected codified publication and its explicitly required nonimage/separate-publication dependencies; external independent legal layers and jurisdiction discovery are not inferred.','independent_legal_review_inferred':False}

def evaluate(evidence,publication_id,config,version,coverage,dispositions):
    result={'schema_version':1,'scope':'selected_publication_export','ready':False,'independent_legal_review_inferred':False,'jurisdiction_readiness_inferred':False,'reasons':[],'gates':{}}
    if not isinstance(evidence,dict):
        result['reasons']=['reader_has_no_qualified_readiness_evidence'];return result
    if evidence.get('schema')!=SCHEMA or evidence.get('contract')!=CONTRACT:
        result['reasons']=['unsupported_readiness_evidence_contract'];return result
    result['evidence']=evidence
    if publication_id!=PUBLICATION or config.get('target_id')!='original-flagstaff-az' or config.get('profile')!='flagstaff_html':
        result['reasons'].append('reader_publication_not_independently_qualified')
    if evidence.get('publication_id')!=publication_id:result['reasons'].append('readiness_publication_identity_mismatch')
    binding=evidence.get('binding');binding=binding if isinstance(binding,dict) else {}
    for name,value in [('configuration_sha256',config),('source_version_sha256',version),('inherited_coverage_sha256',coverage)]:
        if binding.get(name)!=digest(value):result['reasons'].append('readiness_'+name+'_mismatch')
    for name in ['common_receipt_canonical_sha256','family_report_canonical_sha256','source_input_inventory_sha256','coverage_raw_sha256']:
        if not isinstance(binding.get(name),str) or not re.fullmatch('[0-9a-f]{64}',binding[name]):result['reasons'].append('readiness_'+name+'_unbound')
    gates=evidence.get('gates');gates=gates if isinstance(gates,dict) else {}
    for key in GATES:
        result['gates'][key]=gates.get(key) is True
        if gates.get(key) is not True:result['reasons'].append('missing_or_unqualified_'+key)
    result['gates']['no_unresolved_source_dispositions']=not any(d.get('disposition')=='unresolved' for d in dispositions)
    if not result['gates']['no_unresolved_source_dispositions']:result['reasons'].append('unresolved_source_dispositions')
    if evidence.get('independent_legal_review_inferred') is not False:result['reasons'].append('readiness_must_not_infer_legal_review')
    result['ready']=not result['reasons'];return result
