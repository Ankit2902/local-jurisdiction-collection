#!/usr/bin/env python3
"""Independent raw source table audit of explicitly indexed completed Municode jobs."""
import argparse,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--status',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--runtime',type=Path,default=ROOT/'.collection-runtime');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 spec=importlib.util.spec_from_file_location('qa_ops_runtime',ROOT/'collectors/ops/launcher.py');ops=importlib.util.module_from_spec(spec);spec.loader.exec_module(ops);python,node,env=ops.runtime_env(a.runtime);status=json.loads(a.status.read_text());reports=[];script=HERE/'municode_raw_tables.cjs'
 for ident,job in status['jobs'].items():
  if job['status']!='complete':continue
  run=(a.status.parent/job['run_path']).resolve();cp=run/'checkpoint.json';out=a.out/(ident+'-'+sha(cp)[:12]+'-'+sha(script)[:12]+'.json')
  if not out.exists():
   result=subprocess.run([str(node),str(script),str(run),str(out)],env=env,capture_output=True,text=True);print(json.dumps({'publication_id':ident,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr}),flush=True)
   if not out.exists():raise ValueError('No independent audit report '+ident)
  report=json.loads(out.read_text());reports.append({'publication_id':ident,'run_path':job['run_path'],'report':out.name,'report_sha256':sha(out),'passed':report['passed'],'records_checked':report['records_checked'],'tables':report['tables'],'rows':report['rows'],'cells':report['cells'],'mismatches':len(report['mismatches'])})
 data={'schema_version':1,'network_requests_sent':0,'status_sha256':sha(a.status),'script_sha256':sha(script),'reports':reports,'all_audited_completed_jobs_passed':all(x['passed'] for x in reports)};(a.out/'index.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({'audited':len(reports),'passed':data['all_audited_completed_jobs_passed']}));return 0 if data['all_audited_completed_jobs_passed'] else 2
if __name__=='__main__':raise SystemExit(main())
