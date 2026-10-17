#!/usr/bin/env python3
"""Run ordinary headed Chrome acquisition and native exports into a new portable package."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);p.add_argument('--sequence',required=True,type=int);a=p.parse_args()
targets=[t for t in json.loads((root/'targets.json').read_text()) if t['sequence']==a.sequence]
if len(targets)!=1:p.error('Sequence is not an American Legal target')
out=a.out.resolve()
if out.exists():p.error('--out must not already exist')
(out/'scripts/executed').mkdir(parents=True);(out/'research').mkdir()
for name in ['discover_alp.mjs','alp_export.mjs','alp_normalize.py','replay.py','encode_parse.py','html_semantics.py','collect_alp.py']:
 shutil.copy2(root/'scripts'/name,out/'scripts'/name)
for name in ['assignment.json','requirements.txt','package.json']:shutil.copy2(root/name,out/name)
(out/'targets.json').write_text(json.dumps(targets,indent=2)+'\n')
b=Path(__file__).read_bytes();(out/'scripts/executed'/('wrapper-'+hashlib.sha256(b).hexdigest()+'.py')).write_bytes(b)
node=os.environ.get('NODE_BIN','node')
subprocess.run([node,str(out/'scripts/discover_alp.mjs')],check=True)
subprocess.run([node,str(out/'scripts/alp_export.mjs'),'--sequence',str(a.sequence)],check=True)
subprocess.run([sys.executable,str(out/'scripts/replay.py'),'--write','--sequence',str(a.sequence)],check=True)
