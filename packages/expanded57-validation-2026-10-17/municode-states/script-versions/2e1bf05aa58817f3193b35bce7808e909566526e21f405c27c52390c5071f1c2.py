#!/usr/bin/env python3
"""Run relocated standalone browser collector sequentially; set PLAYWRIGHT_MODULE_ROOT only for existing install."""
import argparse,json,pathlib,subprocess,sys,datetime,os
ROOT=pathlib.Path(__file__).resolve().parents[1]
SLUGS={'Huntsville':'huntsville','Des Moines':'des_moines','Little Rock':'little_rock','Providence':'providence','Charleston':'charleston','Bridgeport':'bridgeport','Jackson':'jackson','Fargo':'fargo','Billings':'billings','Wilmington':'wilmington','Cheyenne':'cheyenne'}
p=argparse.ArgumentParser();p.add_argument('--sequence',type=int);p.add_argument('--node',default='node');p.add_argument('--sample-count',type=int,default=3);a=p.parse_args()
for row in json.loads((ROOT/'assignment.json').read_text()):
 if a.sequence and row['sequence']!=a.sequence:continue
 slug=SLUGS[row['jurisdiction']]+'-'+row['state'].lower();dest=ROOT/'live'/slug
 if (dest/'receipt.json').exists():continue
 url='https://library.municode.com/'+row['state'].lower()+'/'+SLUGS[row['jurisdiction']]+'/codes/code_of_ordinances'
 cmd=[a.node,str(ROOT/'scripts/collect_browser.cjs'),url,str(dest),str(a.sample_count)]
 env=dict(os.environ);env.setdefault('PYTHON',sys.executable)
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();print(slug,flush=True)
 cp=subprocess.run(cmd,env=env,text=True,capture_output=True)
 dest.mkdir(parents=True,exist_ok=True);(dest/'command.json').write_text(json.dumps({'command':cmd,'returncode':cp.returncode,'started_at':start,'stdout':cp.stdout,'stderr':cp.stderr},indent=2));print(cp.stdout[-1000:],cp.stderr[-500:],flush=True)
