#!/usr/bin/env python3
"""Bounded live execution of delivered Playwright command; no access bypass."""
import datetime,json,os,pathlib,subprocess,sys
import municipal_codes_cli as m
out=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'standalone-final')
node=os.environ.get('NODE_BINARY','node')
results=[]
for slug,(_,_,base) in m.ROUTES.items():
 dest=out/slug;dest.mkdir(parents=True,exist_ok=False)
 cmd=[node,'browser_capture.mjs',base+'/1.01.010',str(dest),'section','1.01.010']
 started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 run=subprocess.run(cmd,env=dict(os.environ,HEADLESS='1',BROWSER_CHANNEL='chrome'),capture_output=True,text=True,timeout=55)
 (dest/'command.log').write_text(run.stdout+run.stderr)
 results.append(dict(slug=slug,command=cmd,started_at=started,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit_code=run.returncode))
 print(slug,run.returncode,flush=True)
out.mkdir(exist_ok=True);(out/'commands.json').write_text(json.dumps(results,indent=2)+'\n')
