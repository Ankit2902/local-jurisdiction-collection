#!/usr/bin/env python3
"""Independent no-publisher-network acceptance over current source; reports to fresh output."""
import argparse,hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent

def source_hashes():
 return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'collectors').rglob('*')) if p.is_file() and p.suffix in ('.py','.cjs') and not any(x in p.parts for x in ('.venv','__pycache__','fixtures','executed-sources','executed-source','script-versions'))}
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--skip-family-suite',action='store_true',help='Diagnostic only; does not qualify the combined current family suite');a=p.parse_args();a.out=a.out.resolve()
 if a.out.exists() and any(a.out.iterdir()):raise ValueError('Fresh logs directory required')
 a.out.mkdir(parents=True,exist_ok=True);before=source_hashes();commands=[('union-catalog',[sys.executable,'-B','collectors/registry/verify_catalog.py']),('catalog-cli-faults',[sys.executable,'-B','collectors/qa/test_readiness_catalog.py']),('ops-acceptance',[sys.executable,'-B','collectors/qa/test_ops_acceptance.py']),('ops-dependency-proofs',[sys.executable,'-B','collectors/qa/test_ops_dependencies.py']),('six-family-images',[sys.executable,'-B','collectors/qa/test_all_family_image_metadata.py']),('notes-source-fields',[sys.executable,'-B','collectors/qa/test_municode_notes.py']),('gridics-source-binding',[sys.executable,'-B','-m','unittest','collectors.qa.test_gridics_acceptance']),('opaque-image-receipts',[sys.executable,'-B','collectors/qa/test_image_audit.py'])]
 if not a.skip_family_suite:commands.append(('all-family-offline',[sys.executable,'-B','collectors/qa/run_offline.py','--out',str(a.out/'family-suite')]))
 results=[]
 for name,argv in commands:
  start=time.monotonic();result=subprocess.run(argv,cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True);(a.out/(name+'.stdout')).write_text(result.stdout);(a.out/(name+'.stderr')).write_text(result.stderr);row={'name':name,'argv':argv,'exit_code':result.returncode,'elapsed_seconds':round(time.monotonic()-start,3),'stdout_sha256':hashlib.sha256(result.stdout.encode()).hexdigest(),'stderr_sha256':hashlib.sha256(result.stderr.encode()).hexdigest()};results.append(row);print(json.dumps({'name':name,'exit_code':result.returncode}),flush=True)
 after=source_hashes();changes={k:{'before':before.get(k),'after':after.get(k)} for k in sorted(set(before)|set(after)) if before.get(k)!=after.get(k)};report={'schema_version':1,'passed':not changes and all(x['exit_code']==0 for x in results),'full_family_suite_included':not a.skip_family_suite,'network_requests_sent':0,'runtime':{'python':sys.version,'executable':sys.executable,'platform':platform.platform()},'commands':results,'source_before':before,'source_after':after,'source_changed_during_suite':changes,'scope_note':'Production entrypoint/fault and source-bundle tests only. Actual full-publication source acquisition and independent raw table audits are separate; no all-target live pass is implied.'};(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'source_changes':len(changes)}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
