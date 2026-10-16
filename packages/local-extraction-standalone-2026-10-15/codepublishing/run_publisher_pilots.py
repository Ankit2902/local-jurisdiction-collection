#!/usr/bin/env python3
"""Run five bounded local publisher-HTML intake jobs; no browser/network dependency."""
import argparse,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--out',required=True);a.add_argument('--jobs',default=str(HERE/'operator-pilot-jobs.json'));args=a.parse_args();out=Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):raise ValueError('Immutable pilot output exists; use fresh --out')
    out.mkdir(parents=True,exist_ok=True);logs=[];results=[]
    for job in json.loads(Path(args.jobs).read_text()):
        command=[sys.executable,str(HERE/'import_publisher_export.py'),'--receipt',str(HERE/job['receipt']),'--out',str(out/job['slug']),'--expected-currency',job['expected_currency']]
        for ch in job['chapters']:command+=['--chapter',ch]
        p=subprocess.run(command,capture_output=True,text=True);logs.append({'slug':job['slug'],'argv':command,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr});(out/'executed-commands.json').write_text(json.dumps(logs,indent=2)+'\n')
        if p.returncode:raise ValueError('Bounded pilot failed '+job['slug']+': '+p.stderr[-1000:])
        results.append(json.loads(p.stdout))
    (out/'pilot-results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps([{'slug':r['slug'],'records':r['audit']['records'],'tables':r['audit']['structure_counts']['table'],'status':r['status']} for r in results],indent=2))
