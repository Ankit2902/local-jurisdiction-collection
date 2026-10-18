"""Run actual common offline verification and bind its tuple without granting dimensions.

This emits incomplete proofs too. It never changes requirement statuses; a
publication can pass only after independent dimensions share this exact scope.
"""
import argparse,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];PROJECT=ROOT.parents[1]
sys.path.insert(0,str(ROOT/'collectors/registry'))
from catalog import load_catalog
from dispatch import command
from readiness_binding import canonical,current_components,selected_configuration,sha,implementation_family

def load_ops():
 spec=importlib.util.spec_from_file_location('qa_current_ops',ROOT/'collectors/ops/launcher.py');mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod

def emit(runtime,target_id,publication_id,run,out):
 if out.exists():raise ValueError('Fresh proof directory required')
 catalog=load_catalog();pub=next(p for p in catalog['publications'] if p['id']==publication_id);target=next(t for t in catalog['targets'] if t['id']==str(target_id));assert pub['target_id']==target['id'];ops=load_ops();sources=current_components(ROOT,pub);assert sources==ops.code_binding(implementation_family(pub))
 plan=command(pub,target,'{OUT}');selection=selected_configuration(ROOT,pub,target,plan)
 code,receipt=ops.execute_job(runtime,target['id'],pub['id'],run,verify_only=True)
 if receipt['publication_id']!=pub['id'] or receipt['publication']!=pub or receipt['selected_config']!=selection['descriptor']['qualified_config']:raise ValueError('Common verify publication/config identity mismatch')
 if receipt['collector_sources_before']!=sources or receipt['collector_sources_after']!=sources or current_components(ROOT,pub)!=sources:raise ValueError('Current code changed while verifying')
 if receipt.get('evidence_read_only') is not True or receipt['evidence_sha256_before']!=receipt['evidence_sha256_after']:raise ValueError('Retained source changed during offline verification')
 if receipt['verification_exit'] not in (0,2):raise ValueError('Family evidence verification invalid, not an incomplete accepted input')
 out.mkdir(parents=True);project=PROJECT.resolve()
 def relative(path):
  p=Path(path).resolve()
  if not p.is_relative_to(project):raise ValueError('Portable project-local proof required')
  return str(p.relative_to(project))
 manifest={'files':[{'path':relative(Path(run)/name),'sha256':digest} for name,digest in receipt['evidence_sha256_after'].items()]};(out/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 runtime_path=Path(receipt['runtime_receipt_path']);(out/'runtime.json').write_bytes(runtime_path.read_bytes())
 verified={'publication_id':pub['id'],'source_url':pub['source_url'],'config_sha256':selection['sha256'],'component_sources':sources,'artifact_manifest_sha256':sha(out/'artifact-manifest.json'),'runtime_receipt_sha256':sha(out/'runtime.json'),'source_before':receipt['collector_sources_before'],'source_after':receipt['collector_sources_after'],'publication_accepted':receipt['acceptance']['publication_accepted'],'read_only':receipt['evidence_read_only'],'actual_common_receipt':receipt,'overall_exit':code};(out/'verification.json').write_text(json.dumps(verified,indent=2)+'\n')
 proof={k:verified[k] for k in ('publication_id','source_url','config_sha256','component_sources','artifact_manifest_sha256','runtime_receipt_sha256')};proof.update(artifact_manifest=relative(out/'artifact-manifest.json'),runtime_receipt=relative(out/'runtime.json'),verification_receipt=relative(out/'verification.json'),verification_receipt_sha256=sha(out/'verification.json'))
 proof['scope_id']=canonical({k:proof[k] for k in ('publication_id','source_url','config_sha256','component_sources','artifact_manifest_sha256','verification_receipt_sha256','runtime_receipt_sha256')});proof['selected_configuration']=selection['descriptor'];proof['requirements_not_promoted']=True;proof['publication_accepted']=verified['publication_accepted'];proof['notes']='Actual common verification tuple only; independent body/table/resume/image dimension receipts remain required and are not manufactured by this importer.'
 (out/'active-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'overall_exit':code,'publication_accepted':proof['publication_accepted'],'proof':str(out/'active-proof.json'),'scope_id':proof['scope_id']}));return 0 if code==0 else 2
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--runtime',type=Path,required=True);ap.add_argument('--target',required=True);ap.add_argument('--publication',required=True);ap.add_argument('--run',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();raise SystemExit(emit(a.runtime,a.target,a.publication,a.run,a.out))
