"""One root-authorized ordinary browser availability probe while direct transport stays stopped."""
import fcntl,json,os,sys,time
from pathlib import Path
from datetime import datetime,timezone
root=Path(os.environ.get('MUNICODE_GATE_DIR','/tmp/compliSolv-municode-rate-gate'))
with (root/'publisher.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);p=root/'state.json';state=json.loads(p.read_text());auth=state.get('authorized_browser_probe',{})
 if auth.get('id')!=os.environ.get('MUNICODE_PROBE_ID') or time.time()>auth.get('expires_at',0):raise SystemExit('No active coordinated browser probe authorization')
 if time.time()<state.get('actual_rate_limit_until',0):raise SystemExit('Actual publisher rate-limit cooldown active')
 if sys.argv[2]=='document':
  if auth.get('root_seen') or sys.argv[1]!=auth.get('root_url'):raise SystemExit('Only one normal public document navigation authorized')
  auth['root_seen']=True;state['authorized_browser_probe']=auth
 time.sleep(max(0,state.get('last_start',0)+3.5-time.time()));state['last_start']=time.time();p.write_text(json.dumps(state))
 with (root/'requests.jsonl').open('a') as f:f.write(json.dumps({'url':sys.argv[1],'started_at':datetime.now(timezone.utc).isoformat(),'transport':'root-authorized-ordinary-browser-availability-probe','pid':os.getpid()})+'\n')
