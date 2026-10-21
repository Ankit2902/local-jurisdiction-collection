"""Atomic, hash-bound source artifacts and conservative shared ICC-family gate."""
from __future__ import annotations
import sys
from pathlib import Path
_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
from collectors.winboot import ensure_fcntl, gate_dir
ensure_fcntl()
import datetime,fcntl,hashlib,json,os,time
from email.utils import parsedate_to_datetime

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(data):return hashlib.sha256(data).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def read(p):return json.loads(Path(p).read_text())
def atomic(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.tmp-'+str(os.getpid()));
 with tmp.open('wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 os.replace(tmp,p)
 if os.name != 'nt':
  fd=os.open(p.parent,os.O_RDONLY)
  try:os.fsync(fd)
  finally:os.close(fd)
def save(p,x):atomic(p,json.dumps(x,ensure_ascii=False,indent=2).encode()+b'\n')
class QualificationError(ValueError):pass
class AccessStop(RuntimeError):pass
class Gate:
 def __init__(self,family,root=None,spacing=3.5):self.root=Path(root or gate_dir('ICC_GATE_DIR','/tmp/complisolv-icc-full-gate'))/family;self.root.mkdir(parents=True,exist_ok=True);self.spacing=max(3.5,spacing)
 def check(self):
  if (self.root/'STOP.json').exists():raise AccessStop('Shared family access stop retained: '+str(self.root/'STOP.json'))
 def reserve(self,url):
  with (self.root/'gate.lock').open('a') as f:
   fcntl.flock(f,fcntl.LOCK_EX);self.check();p=self.root/'state.json';s=read(p) if p.exists() else {};time.sleep(max(0,s.get('last_start',0)+self.spacing-time.time()));self.check();save(p,{'last_start':time.time(),'url':url})
 def stop(self,event):
  retry=event.get('retry_after');delay=300
  if retry:
   try:delay=max(300,float(retry))
   except ValueError:
    try:delay=max(300,parsedate_to_datetime(retry).timestamp()-time.time())
    except Exception:pass
  save(self.root/'STOP.json',{'observed_at':now(),'event':event,'retry_after_seconds_minimum':delay,'operator_review_required':True,'automatic_retry':False})
