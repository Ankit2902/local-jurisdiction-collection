"""Publisher-wide conservative gate. Stops persist until operator investigation; no reset CLI."""
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
import argparse,datetime,fcntl,json,os,tempfile,time
from email.utils import parsedate_to_datetime
p=argparse.ArgumentParser();p.add_argument('action',choices=['reserve','stop']);p.add_argument('url');p.add_argument('--reason');p.add_argument('--retry-after');a=p.parse_args()
# This observed workflow stop is intentionally anchored in source as well as data.
# A fresh checkout, missing /tmp gate, or deleted/altered bundled advisory is not
# authorization to retry. No operator-reset/bypass flag is provided here.
KNOWN_STOP_SHA256 = 'cc41433c18b63efb119a07e3e1ce27c8309921471f2e2d0b4f8cc564adbcb66d'
KNOWN_REFUSAL_SHA256 = '7367c1b4392e05049918bfa7e074881e425e1c9424e8e4a786337e8adaecdf8e'
def portable_stop():
 advisory = Path(__file__).resolve().parent / 'access-advisory.json'
 detail = 'Bundled source-bound advisory missing or invalid; the known stop remains.'
 try:
  data=json.loads(advisory.read_text());records=data.get('advisories',[])
  matching=[x for x in records if x.get('family')=='american-legal']
  assert data.get('schema_version')==1 and len(matching)==1
  record=matching[0]
  assert record.get('source_sha256')==KNOWN_STOP_SHA256
  assert record.get('raw_refusal_witness',{}).get('sha256')==KNOWN_REFUSAL_SHA256
  assert record.get('operator_review_required') is True and record.get('automatic_retry') is False
  detail=json.dumps(record,sort_keys=True)
 except (OSError,ValueError,TypeError,AssertionError,AttributeError):
  pass
 return 'AmericanLegal portable workflow access stop; no automatic retry. Other route availability after the observed stop is untested. '+detail
# Refuse before creating custom/default gate directories, locks, state or requests.
if a.action=='reserve':raise SystemExit(portable_stop())
r=gate_dir('AMLEGAL_GATE_DIR','/tmp/compliSolv-american-legal-full-gate');r.mkdir(parents=True,exist_ok=True);stop=r/'browser-stop.json'
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
