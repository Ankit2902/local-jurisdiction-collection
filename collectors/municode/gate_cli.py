"""Browser-only shared rate gate. Direct HTTP remains stopped after wave3 challenges.
A fresh browser challenge/429 writes an atomic stop flag before waiting for the lock.
"""
import sys
from pathlib import Path
_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
from collectors.winboot import boot, gate_dir, ensure_fcntl
if __name__ == '__main__':
    boot()
else:
    ensure_fcntl()
import fcntl,json,os,time,hashlib
from urllib.parse import urlparse
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
root=gate_dir('MUNICODE_GATE_DIR','/tmp/compliSolv-municode-rate-gate');root.mkdir(parents=True,exist_ok=True);stop=root/'browser-stop.json';action=sys.argv[1]
external_host=urlparse(sys.argv[2]).hostname if len(sys.argv)>2 else None
external_stop=root/('external-stop-'+hashlib.sha256((external_host or '').encode()).hexdigest()+'.json')
if action=='stop-external':
 record={'host':external_host,'url':sys.argv[2],'reason':' '.join(sys.argv[3:]),'recorded_at':datetime.now(timezone.utc).isoformat(),'operator_release_required':True};tmp=external_stop.with_suffix('.'+str(os.getpid())+'.tmp');tmp.write_text(json.dumps(record));os.replace(tmp,external_stop);raise SystemExit(0)
if action in ['stop-browser','cooldown']:
 record={'reason':'HTTP429' if action=='cooldown' else (' '.join(sys.argv[2:]) or 'Publisher challenge'),'recorded_at':datetime.now(timezone.utc).isoformat(),'operator_release_required':True};tmp=root/('browser-stop-'+str(os.getpid())+'.tmp');tmp.write_text(json.dumps(record));os.replace(tmp,stop)
with (root/'publisher.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);p=root/'state.json';s=json.loads(p.read_text()) if p.exists() else {}
 if action=='reserve':
  if external_stop.exists():raise SystemExit('External required-source access stop: '+external_stop.read_text())
  if stop.exists():raise SystemExit('Browser publisher access stop: '+stop.read_text())
  if s.get('family_stop') and not s.get('browser_workflow_authorized'):raise SystemExit('Publisher family stopped; no browser workflow authorization')
  limit=s.get('actual_rate_limit_until',0) if s.get('family_stop') else max(s.get('actual_rate_limit_until',0),s.get('cooldown_until',0))
  if time.time()<limit:raise SystemExit('Publisher rate-limit cooldown active')
  time.sleep(max(0,s.get('last_start',0)+3.5-time.time()))
  if stop.exists():raise SystemExit('Browser publisher access stop during gate wait')
  s['last_start']=time.time()
  with (root/'requests.jsonl').open('a') as f:f.write(json.dumps({'url':sys.argv[2],'started_at':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'transport':'ordinary-headed-browser-public-workflow','gate_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})+'\n')
 elif action=='cooldown':
  retry=sys.argv[2] if len(sys.argv)>2 else '300'
  try:delay=float(retry)
  except ValueError:
   try:delay=parsedate_to_datetime(retry).timestamp()-time.time()
   except Exception:delay=300
  s['actual_rate_limit_until']=max(s.get('actual_rate_limit_until',0),time.time()+max(300,delay));s['browser_access_stop']=record
  if not s.get('family_stop'):s['cooldown_until']=max(s.get('cooldown_until',0),s['actual_rate_limit_until'])
 elif action=='stop-browser':s['browser_access_stop']=record
 else:raise SystemExit('Unknown browser gate action')
 p.write_text(json.dumps(s))
