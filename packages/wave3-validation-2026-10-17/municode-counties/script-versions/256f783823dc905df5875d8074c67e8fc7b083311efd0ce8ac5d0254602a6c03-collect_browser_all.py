"""Serial normal headed public application runs. Stops on any failed target."""
import json,os,subprocess,sys
from pathlib import Path
from collect_all import ROOT,ASSIGNMENT,URLS,slug
for a in ASSIGNMENT:
 d=ROOT/'browser'/slug(a)
 if (d/'receipt.json').exists():
  r=json.loads((d/'receipt.json').read_text())
  if r.get('status')=='acquired': continue
  raise SystemExit('Existing failed receipt: '+str(d))
 env=os.environ.copy()
 names=[a['jurisdiction']]
 if a['sequence']==95:names=['Baton Rouge, East Baton Rouge Parish']
 env.update(MUNICODE_EXPECTED_CLIENT_NAMES=json.dumps(names),MUNICODE_EXPECTED_STATE=a['state'])
 print('START',a['sequence'],a['jurisdiction'],flush=True)
 p=subprocess.run([env.get('NODE','node'),str(ROOT/'scripts/collect_browser.cjs'),URLS[a['sequence']],str(d),'3'],env=env)
 if p.returncode:raise SystemExit(p.returncode)
 subprocess.run([sys.executable,str(ROOT/'scripts/normalize.py'),str(d),'--offline'],check=True)
 print('COMPLETE',a['sequence'],flush=True)
