"""Publisher-wide conservative POSIX gate. Stops persist until operator investigation; no reset CLI."""
import argparse,datetime,fcntl,json,os,tempfile,time
from pathlib import Path
from email.utils import parsedate_to_datetime
p=argparse.ArgumentParser();p.add_argument('action',choices=['reserve','stop']);p.add_argument('url');p.add_argument('--reason');p.add_argument('--retry-after');a=p.parse_args()
r=Path(os.environ.get('AMLEGAL_GATE_DIR','/tmp/compliSolv-american-legal-full-gate'));r.mkdir(parents=True,exist_ok=True);stop=r/'browser-stop.json'
def atom(p,v):
 t=p.with_name(p.name+'.'+str(os.getpid())+'.tmp');t.write_text(json.dumps(v,indent=2));os.replace(t,p)
if a.action=='stop':
 try:delay=float(a.retry_after or '300')
 except ValueError:
  try:delay=parsedate_to_datetime(a.retry_after).timestamp()-time.time()
  except Exception:delay=300
 atom(stop,{'url':a.url,'reason':a.reason,'retry_after':a.retry_after,'stopped_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'retry_not_before':time.time()+max(300,delay),'operator_review_required':True});raise SystemExit(0)
with (r/'family.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 if stop.exists():raise SystemExit('AmericanLegal browser publisher stop: '+stop.read_text())
 state=r/'state.json';s=json.loads(state.read_text()) if state.exists() else {};time.sleep(max(0,s.get('last_start',0)+3.5-time.time()))
 if stop.exists():raise SystemExit('Publisher stopped while waiting')
 atom(state,{'last_start':time.time()})
 with (r/'requests.jsonl').open('a') as f:f.write(json.dumps({'url':a.url,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid()})+'\n')
