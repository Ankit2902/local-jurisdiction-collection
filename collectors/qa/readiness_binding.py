"""Fail closed when proof dimensions do not belong to the active publication revision.

Candidate results and historical live acquisitions remain useful evidence. They
cannot compose a release pass across different source, config, or record bytes.
"""
import hashlib,json
from pathlib import Path

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def implementation_family(publication):
 return publication.get('adapter_family',publication['publisher']) if isinstance(publication,dict) else publication
def current_components(repo,publisher):
 publisher=implementation_family(publisher)
 repo=Path(repo);family=repo/'collectors'/publisher;registry=repo/'collectors/registry';ops=repo/'collectors/ops'
 files=[registry/name for name in ('collect.py','dispatch.py','catalog.py') if (registry/name).is_file()]
 if (repo/'collect.py').is_file():files += [repo/'collect.py']
 files += [ops/name for name in ('launcher.py','browser_check.cjs','requirements.txt') if (ops/name).is_file()]
 files += [p for p in family.glob('*') if p.suffix in ('.py','.cjs')]
 files += [p for folder in ('configs','policies') for p in (family/folder).rglob('*.json')]
 if publisher=='encodeplus':files += [family/'targets.json',family/'infrastructure-multiline-native-geometry.json']
 if publisher=='originals':
  files += list(family.glob('*.json'))+list((family/'profiles').rglob('*.json'))
 files += [p for p in registry.glob('*.json') if p.name not in ('source-evidence-manifest.json','original-source-evidence-manifest.json','readiness-source-evidence-manifest.json')]
 return {str(p.relative_to(repo)):sha(p) for p in sorted(set(files))}
def selected_configuration(repo,pub,target,plan):
 config_path=plan.get('qualified_config_path');named_path=plan.get('named_config_path');config=None;file_sha=None
 if named_path:
  if config_path or (Path(repo)/named_path).resolve()!=(Path(repo)/'collectors/encodeplus/targets.json').resolve():raise ValueError('Unexpected or ambiguous named enCodePlus configuration source')
  config_path=named_path
 if config_path:
  path=(Path(repo)/config_path).resolve()
  if not path.is_relative_to(Path(repo).resolve()) or not path.is_file():raise ValueError('Selected configuration file missing/outside repo')
  config=json.loads(path.read_text());file_sha=sha(path)
  if named_path:
   key=plan.get('named_config_key')
   if not isinstance(config,dict) or key not in config or not isinstance(config[key],dict):raise ValueError('Selected named enCodePlus configuration is missing')
   config=config[key]
 else:config=plan.get('staged_config')
 value={'publication':pub,'target_expected_identity':target.get('expected_identity'),'command_plan':plan,'qualified_config':config,'qualified_config_file_sha256':file_sha}
 return {'sha256':canonical(value),'descriptor':value}

def gate_qa_sources(repo,publisher,key):
 publisher=implementation_family(publisher)
 names={'normalized_image_audit':['audit_normalized_images.py'],'acquired_bytes_image_audit':['audit_images.py'],'image_transport_regression':['test_image_policy.py','test_all_family_image_metadata.py']}[key]
 if key=='image_transport_regression':
  if publisher=='originals':return {'collectors/qa/test_originals_image_transport.py':sha(Path(repo)/'collectors/qa/test_originals_image_transport.py')}
  family_test={'american-legal':'test_american_image_transport.py','official':'test_official_image_transport.py'}.get(publisher)
  if family_test:names=names+[family_test]
 return {str(Path('collectors/qa')/name):sha(Path(repo)/'collectors/qa'/name) for name in names}

def assess(row,repo,project,current_sources,config_sha256):
 errors=[]
 if row.get('observed_access_advisories'):errors.append('observed_access_stop')
 if not row.get('configuration_qualified'):errors.append('unqualified_configuration')
 for key,value in row['requirements'].items():
  if value.get('status')!='pass':errors.append('requirement_not_active_pass:'+key)
 proof=row.get('active_runtime_proof')
 if not isinstance(proof,dict):return {'accepted':False,'errors':errors+['missing_active_runtime_proof'],'scope_coherent':False}
 scope={key:proof.get(key) for key in ('publication_id','source_url','config_sha256','component_sources','artifact_manifest_sha256','verification_receipt_sha256','runtime_receipt_sha256')}
 scope_id=canonical(scope)
 if proof.get('scope_id')!=scope_id:errors.append('proof_scope_digest_mismatch')
 if proof.get('publication_id')!=row['publication_id'] or proof.get('source_url')!=row['active_source_url']:errors.append('wrong_publication_scope')
 if not current_sources or proof.get('component_sources')!=current_sources:errors.append('active_component_revision_mismatch')
 if not config_sha256 or proof.get('config_sha256')!=config_sha256:errors.append('active_configuration_mismatch')
 def bound_file(path,expected):
  p=(Path(project)/path).resolve()
  if not p.is_relative_to(Path(project).resolve()) or not p.is_file() or sha(p)!=expected:raise ValueError('missing_or_changed_evidence:'+str(path))
  return p
 try:
  runtime=bound_file(proof['runtime_receipt'],proof['runtime_receipt_sha256'])
  receipt=json.loads(bound_file(proof['verification_receipt'],proof['verification_receipt_sha256']).read_text())
  if receipt.get('publication_accepted') is not True or receipt.get('read_only') is not True:errors.append('verification_not_accepted_readonly')
  for key in ('publication_id','source_url','config_sha256','component_sources','artifact_manifest_sha256','runtime_receipt_sha256'):
   if receipt.get(key)!=proof.get(key):errors.append('verification_binding_mismatch:'+key)
  if receipt.get('source_before')!=current_sources or receipt.get('source_after')!=current_sources:errors.append('verification_source_drift')
  manifest=json.loads(bound_file(proof['artifact_manifest'],proof['artifact_manifest_sha256']).read_text())
  if not manifest.get('files'):errors.append('empty_artifact_manifest')
  for item in manifest.get('files',[]):bound_file(item['path'],item['sha256'])
 except (KeyError,ValueError,OSError,json.JSONDecodeError) as exc:errors.append(str(exc))
 for key,value in row['requirements'].items():
  if value.get('proof_scope_id')!=scope_id:errors.append('unbound_requirement:'+key)
 for key in ('image_transport_regression','normalized_image_audit','acquired_bytes_image_audit'):
  audit=proof.get(key,{})
  try:
   report=json.loads(bound_file(audit['path'],audit['sha256']).read_text())
   if report.get('passed') is not True or report.get('component_sources')!=current_sources or report.get('proof_scope_id')!=scope_id:errors.append('unbound_or_failed_image_gate:'+key)
   if report.get('executed_qa_sources')!=gate_qa_sources(repo,row,key):errors.append('current_qa_revision_mismatch:'+key)
  except (KeyError,ValueError,OSError,json.JSONDecodeError) as exc:errors.append(key+':'+str(exc))
 return {'accepted':not errors,'errors':errors,'scope_coherent':not errors,'proof_scope_id':scope_id}
