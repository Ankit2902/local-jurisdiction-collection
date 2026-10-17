"""Shared rate gate for ordinary browser routes; never handles or exports cookies."""
import sys,fcntl,json,os,time
from pathlib import Path
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
root=Path(os.environ.get('MUNICODE_GATE_DIR','/tmp/compliSolv-municode-rate-gate'));root.mkdir(parents=True,exist_ok=True)
with (root/'publisher.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);p=root/'state.json';s=json.loads(p.read_text()) if p.exists() else {}
 if sys.argv[1]=='reserve':
  if time.time()<s.get('cooldown_until',0):raise SystemExit('Shared publisher cooldown active until '+datetime.fromtimestamp(s['cooldown_until'],timezone.utc).isoformat())
  time.sleep(max(0,s.get('last_start',0)+3.5-time.time()));s['last_start']=time.time()
  with (root/'requests.jsonl').open('a') as f:f.write(json.dumps({'url':sys.argv[2],'started_at':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'transport':'headed-browser-route'})+'\n')
 elif sys.argv[1]=='cooldown':
  retry=sys.argv[2] if len(sys.argv)>2 else '300'
  try:delay=float(retry)
  except ValueError:
   try:delay=parsedate_to_datetime(retry).timestamp()-time.time()
   except Exception:delay=300
  s['cooldown_until']=max(s.get('cooldown_until',0),time.time()+max(300,delay))
 p.write_text(json.dumps(s))
