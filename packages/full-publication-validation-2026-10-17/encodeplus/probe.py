#!/usr/bin/env python3
import argparse,pathlib,json,hashlib,shutil,sys,platform,datetime
from transport import fetch
p=argparse.ArgumentParser();p.add_argument('url');p.add_argument('out',type=pathlib.Path);a=p.parse_args()
if a.out.exists():p.error('Output must be new; no hidden cache/reuse')
a.out.parent.mkdir(parents=True,exist_ok=True);d=a.out.parent/'script-versions';d.mkdir(exist_ok=True)
for src in [pathlib.Path(__file__),pathlib.Path(__file__).with_name('transport.py')]:shutil.copy2(src,d/(hashlib.sha256(src.read_bytes()).hexdigest()+src.suffix))
run={'command':sys.argv,'runtime':platform.python_version(),'os':platform.platform(),'script_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
try:
 b,r=fetch(a.url,a.out);run.update(status='fetched',bytes=len(b))
except Exception as e:run.update(status='failed',error=str(e))
run['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();a.out.with_name(a.out.name+'.command.json').write_text(json.dumps(run,indent=2));print(json.dumps(run))
