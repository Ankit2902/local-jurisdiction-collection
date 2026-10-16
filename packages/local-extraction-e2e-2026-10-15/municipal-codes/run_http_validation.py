#!/usr/bin/env python3
"""Bounded delivered CLI HTTP probes. Creates a fresh output directory per source."""
import datetime,json,pathlib,subprocess,sys
import municipal_codes_cli as m
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'http-final');root.mkdir(exist_ok=False)
rows=[]
for slug,(_,_,base) in m.ROUTES.items():
 cmd=[sys.executable,'municipal_codes_cli.py','acquire','--slug',slug,'--url',base+'/1.01.010','--out',str(root/slug)]
 started=m.now();r=subprocess.run(cmd,text=True,capture_output=True,timeout=40);(root/(slug+'.log')).write_text(r.stdout+r.stderr)
 rows.append(dict(slug=slug,command=cmd,started_at=started,finished_at=m.now(),exit_code=r.returncode));print(slug,r.returncode,flush=True)
m.write_json(root/'commands.json',rows)
