#!/usr/bin/env python3
"""Run the same bounded standalone job, deliberately stop after one, then resume.
Usage: python e2e_run.py start | resume
PLAYWRIGHT_BROWSERS_PATH may point to an external official Playwright browser cache.
"""
import argparse,json,os,signal,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
BASE='https://codehub.gridics.com/us/ca/cupertino#/'
TITLE='90d493fe-25f4-4aef-a519-710b1e0055c6'
URLS=[BASE+TITLE,BASE+TITLE+'/88af81d8-f905-4db5-98ae-6c3735fab006/e039b8ec-52e6-4c19-a5e3-a73daccfdeba',BASE+'d2cdbf65-126d-4964-a06c-6ebe7a91da6f']
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['start','resume']);p.add_argument('--process-timeout',type=int,default=600);a=p.parse_args()
 target=ROOT/'standalone-final';evidence=ROOT/'e2e-evidence';evidence.mkdir(exist_ok=True)
 if a.phase=='start' and (target/'acquisition-checkpoint.json').exists():raise ValueError('Start needs fresh output; use resume for existing bound acquisition')
 if a.phase=='resume' and not (target/'acquisition-checkpoint.json').exists():raise ValueError('No interrupted checkpoint to resume')
 cmd=[sys.executable,'-u',str(ROOT/'acquire.py')]
 for url in URLS:cmd+=['--url',url]
 cmd+=['--snapshot-id','gridics-standalone-final-2026-10-15','--source-version','legal-version-unknown:standalone-final-2026-10-15','--out',str(target),'--timeout','60','--verify-end']
 if a.phase=='start':cmd+=['--stop-after','1']
 before=json.loads((target/'acquisition-checkpoint.json').read_text()) if (target/'acquisition-checkpoint.json').exists() else None
 log=evidence/('standalone-final-'+a.phase+'.log');start=datetime.now(timezone.utc).isoformat()
 with log.open('w') as stream:
  child=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
  try:child.wait(timeout=a.process_timeout);status='completed'
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGTERM);child.wait();status='process_timeout'
 receipt={'command':cmd,'portable_command':'python e2e_run.py '+a.phase,'started_at':start,'ended_at':datetime.now(timezone.utc).isoformat(),'returncode':child.returncode,'process_status':status,'log_path':str(log.relative_to(ROOT)),'prior_artifact_hashes':[x['sha256'] for x in before['artifacts']] if before else [],'environment':{'python':sys.version,'PLAYWRIGHT_BROWSERS_PATH':os.environ.get('PLAYWRIGHT_BROWSERS_PATH','default Playwright cache')}}
 if (target/'snapshot-manifest.json').exists():
  m=json.loads((target/'snapshot-manifest.json').read_text());receipt.update(acquisition_status=m.get('acquisition_status'),route_count=len(m['artifacts']),preserved_prior_artifacts=all(x['sha256'] in [v['sha256'] for v in m['artifacts']] for x in before['artifacts']) if before else None)
 (evidence/('standalone-final-'+a.phase+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(receipt,indent=2))
 if child.returncode:sys.exit(child.returncode if child.returncode>0 else 1)
if __name__=='__main__':main()
