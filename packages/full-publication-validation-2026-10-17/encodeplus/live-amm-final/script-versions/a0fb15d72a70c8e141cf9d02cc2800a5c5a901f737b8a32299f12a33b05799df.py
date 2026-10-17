"""Serial public HTTP, same shared enCodePlus gate; no retries/challenge handling."""
import fcntl,json,os,time,platform,urllib.request,urllib.error,urllib.parse
from pathlib import Path
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
from .util import atomic_bytes,atomic_json,digest
PUBLISHER_HOSTS={'online.encodeplus.com','codes.opkansas.org'}
class Stopped(RuntimeError):pass
def scope_path(gate,url):
 host=urllib.parse.urlsplit(url).hostname
 if not host:raise ValueError('No source hostname')
 return gate/'state.json' if host in PUBLISHER_HOSTS else gate/'hosts'/digest(host.encode())/'state.json'
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kw):return None
def now():return datetime.now(timezone.utc).isoformat()
def fetch(url,out,timeout=120):
 out=Path(out);assert not out.exists() and not out.with_name(out.name+'.receipt.json').exists(),'Refusing existing request output'
 gate=Path(os.environ.get('ENCODEPLUS_GATE_DIR','/tmp/compliSolv-encodeplus-rate-gate'));gate.mkdir(parents=True,exist_ok=True);original=url;redirects=[]
 for _ in range(6):
  assert urllib.parse.urlsplit(url).scheme in ['http','https'],'Unsupported network scheme'
  with (gate/'publisher.lock').open('a+') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);global_path=gate/'state.json';global_state=json.loads(global_path.read_text()) if global_path.exists() else {};sp=scope_path(gate,url);state=global_state if sp==global_path else (json.loads(sp.read_text()) if sp.exists() else {})
   if state.get('stopped'):raise Stopped('Publisher stopped: '+str(state.get('stop_reason')))
   if time.time()<state.get('cooldown_until',0):raise Stopped('Shared publisher cooldown active until '+str(state['cooldown_until']))
   time.sleep(max(0,global_state.get('last_start',0)+3.5-time.time()));global_state['last_start']=time.time();atomic_json(global_path,global_state);started=now();error=None
   try:
    req=urllib.request.Request(url,headers={'User-Agent':'CompliSolv public publication collection/1.0'})
    response=urllib.request.build_opener(NoRedirect()).open(req,timeout=timeout);body=response.read();status=response.status;headers=dict(response.headers);response.close()
   except urllib.error.HTTPError as e:body=e.read();status=e.code;headers=dict(e.headers);error=str(e)
   except Exception as e:body=b'';status=None;headers={};error=str(e)
   low={k.lower():v for k,v in headers.items()};challenge=status in [401,403] or low.get('cf-mitigated')=='challenge' or (status==200 and any(x in body[:10000].lower() for x in [b'<title>just a moment',b'cf-chl-',b'verify you are human']))
   if status==429:
    retry=low.get('retry-after','300')
    try:delay=float(retry)
    except ValueError:
     try:delay=parsedate_to_datetime(retry).timestamp()-time.time()
     except Exception:delay=300
    state['cooldown_until']=time.time()+max(300,delay)
   if challenge:state.update(stopped=True,stop_reason={'url':url,'status':status,'at':now()})
   atomic_json(sp,state)
   with (gate/'requests.jsonl').open('a') as log:log.write(json.dumps({'url':url,'started_at':started,'status':status,'pid':os.getpid(),'cooldown_until':state.get('cooldown_until'),'stopped':state.get('stopped',False)})+'\n')
  location=low.get('location')
  if status in [301,302,303,307,308] and location:
   redirects.append({'url':url,'status':status,'location':location});url=urllib.parse.urljoin(url,location);continue
  receipt={'url':original,'final_url':url,'started_at':started,'finished_at':now(),'http_status':status,'headers':headers,'sha256':digest(body),'bytes':len(body),'redirects':redirects,'runtime':platform.python_version(),'transport_sha256':digest(Path(__file__).read_bytes()),'error':error,'challenge':bool(challenge)}
  atomic_bytes(out,body);atomic_json(out.with_name(out.name+'.receipt.json'),receipt)
  if status!=200 or challenge:raise Stopped('HTTP/challenge stop: '+str(status)+' '+url)
  return body,receipt
 raise Stopped('Too many redirects')
