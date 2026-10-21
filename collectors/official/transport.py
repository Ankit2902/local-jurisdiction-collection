"""Serial host-family HTTP/browser rate gate with persisted access stops, never a bypass."""
import sys
from pathlib import Path as _Path
_root = _Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
from collectors.winboot import ensure_fcntl, gate_dir
ensure_fcntl()
import datetime,fcntl,hashlib,json,os,pathlib,time,urllib.request,urllib.error,urllib.parse
from email.utils import parsedate_to_datetime
ROOT=gate_dir('OFFICIAL_GATE_DIR','/tmp/compliSolv-official-publication-gate')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def atomic(path,b):
 path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp-'+str(os.getpid()));tmp.write_bytes(b);os.replace(tmp,path)
def family(url):return urllib.parse.urlparse(url).hostname or 'local'
def reserve(url):
 host=family(url);folder=ROOT/hashlib.sha256(host.encode()).hexdigest()[:20];folder.mkdir(parents=True,exist_ok=True)
 with (folder/'lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);state=folder/'state.json';s=json.loads(state.read_text()) if state.exists() else {}
  if s.get('stop'):raise RuntimeError('Persisted host access stop: '+json.dumps(s['stop']))
  time.sleep(max(0,s.get('last_start',0)+3.5-time.time()));s['last_start']=time.time();atomic(state,json.dumps(s).encode())
  with (folder/'requests.jsonl').open('a') as f:f.write(json.dumps({'url':url,'started_at':now(),'pid':os.getpid()})+'\n')
def stop(url,status,headers,reason):
 folder=ROOT/hashlib.sha256(family(url).encode()).hexdigest()[:20];folder.mkdir(parents=True,exist_ok=True)
 with (folder/'lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);p=folder/'state.json';s=json.loads(p.read_text()) if p.exists() else {};retry=next((v for k,v in headers.items() if k.lower()=='retry-after'),'300')
  try:delay=float(retry)
  except ValueError:
   try:delay=parsedate_to_datetime(retry).timestamp()-time.time()
   except Exception:delay=300
  s['stop']={'status':status,'url':url,'reason':reason,'recorded_at':now(),'retry_after':retry,'not_before':time.time()+max(300,delay),'operator_release_required':True};atomic(p,json.dumps(s).encode())
class Redirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  if urllib.parse.urlparse(newurl).scheme!='https':raise RuntimeError('NonHTTPS redirect refused')
  reserve(newurl);return super().redirect_request(req,fp,code,msg,headers,newurl)
def fetch(url,max_bytes=160_000_000):
 reserve(url);receipt={'url':url,'started_at':now(),'transport':'stdlib urllib; public GET; no automatic retries'}
 try:
  with urllib.request.build_opener(Redirect()).open(urllib.request.Request(url,headers={'User-Agent':'CompliSolv municipal publication research/1.0'}),timeout=180) as response:
   receipt.update(status=response.status,final_url=response.url,headers=dict(response.headers))
   if response.headers.get_content_type().lower().startswith('image/'):
    data=b'';receipt.update(policy_omitted_image=True,reason='User no-image policy; response image body deliberately not read')
   else:data=response.read(max_bytes+1)
 except urllib.error.HTTPError as error:
  receipt.update(status=error.code,final_url=error.url,headers=dict(error.headers),error=str(error))
  if error.headers.get_content_type().lower().startswith('image/'):
   data=b'';receipt['policy_omitted_image']=True
  else:data=error.read(max_bytes+1)
 if len(data)>max_bytes:raise RuntimeError('Configured maximum native-file bytes exceeded')
 challenge=any(k.lower()=='cf-mitigated' and 'challenge' in v.lower() for k,v in receipt['headers'].items()) or b'<title>Just a moment' in data[:20000]
 if receipt['status'] in (403,429) or challenge:stop(url,receipt['status'],receipt['headers'],'HTTP refusal/rate limit/challenge');receipt['access_stop']=True
 receipt.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),finished_at=now());return data,receipt
if __name__=='__main__':
 import sys
 action=sys.argv[1]
 if action=='reserve':reserve(sys.argv[2])
 elif action=='stop':stop(sys.argv[2],int(sys.argv[3]),json.loads(sys.argv[4]),'Browser access refusal/challenge')
