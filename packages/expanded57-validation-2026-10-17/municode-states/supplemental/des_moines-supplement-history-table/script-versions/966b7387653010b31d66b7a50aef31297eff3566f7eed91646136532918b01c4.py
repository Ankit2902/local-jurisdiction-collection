"""Portable Municode HTTP acquisition with a shared process-safe rate gate.
Set MUNICODE_GATE_DIR identically in concurrent collectors (default /tmp/compliSolv-municode-rate-gate).
Every request across Municode hosts, including redirects, holds an flock; starts are >=3s apart.
A 429 persists shared cooldown >=Retry-After or 300s; requests during cooldown fail without network.
"""
import fcntl, hashlib, json, os, platform, time, urllib.request, urllib.error, urllib.parse
from pathlib import Path
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
class Cooldown(RuntimeError): pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kw): return None

def fetch(url, out, method='GET', data=None, headers=None, spacing=3, timeout=60):
    """Save raw bytes + receipt; HTTP failures retained then raised. No retries. Redirects individually gated."""
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    gate=Path(os.environ.get('MUNICODE_GATE_DIR','/tmp/compliSolv-municode-rate-gate'));gate.mkdir(parents=True,exist_ok=True)
    receipt={'url':url,'started_at':now(),'method':method,'runtime':{'python':platform.python_version()},'script_sha256':sha(Path(__file__).read_bytes()),'redirects':[]}
    for redirect in range(6):
        with (gate/'publisher.lock').open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            statepath=gate/'state.json'
            state=json.loads(statepath.read_text()) if statepath.exists() else {}
            if time.time()<state.get('cooldown_until',0): raise Cooldown('Shared publisher cooldown active until '+datetime.fromtimestamp(state['cooldown_until'],timezone.utc).isoformat())
            time.sleep(max(0,state.get('last_start',0)+max(3,spacing)-time.time()))
            state['last_start']=time.time();statepath.write_text(json.dumps(state))
            req=urllib.request.Request(url,data=data,method=method,headers={'User-Agent':'CompliSolv bounded public-code validation/1.0','X-CSRF':'1',**(headers or {})})
            started=now();error=None
            try:
                resp=urllib.request.build_opener(NoRedirect()).open(req,timeout=timeout)
                body=resp.read();status=resp.status;rh=dict(resp.headers)
            except urllib.error.HTTPError as exc:
                body=exc.read();status=exc.code;rh=dict(exc.headers);error=str(exc)
            except Exception as exc:
                body=b'';status=None;rh={};error=repr(exc)
            if status==429:
                retry=rh.get('Retry-After','300')
                try: delay=float(retry)
                except ValueError:
                    try: delay=parsedate_to_datetime(retry).timestamp()-time.time()
                    except Exception: delay=300
                state['cooldown_until']=time.time()+max(300,delay);statepath.write_text(json.dumps(state))
            with (gate/'requests.jsonl').open('a') as log: log.write(json.dumps({'url':url,'started_at':started,'status':status,'pid':os.getpid(),'cooldown_until':state.get('cooldown_until')})+'\n')
        if status in [301,302,303,307,308] and rh.get('Location'):
            receipt['redirects'].append({'url':url,'status':status,'location':rh['Location']});url=urllib.parse.urljoin(url,rh['Location'])
            if status==303:method='GET';data=None
            continue
        out.write_bytes(body)
        receipt.update({'final_url':url,'finished_at':now(),'http_status':status,'headers':rh,'sha256':sha(body),'bytes':len(body),'error':error,'raw_file':out.name})
        out.with_name(out.name+'.receipt.json').write_text(json.dumps(receipt,indent=2))
        if status!=200: raise RuntimeError(f'HTTP {status} {url}: {error}')
        return body,receipt
    raise RuntimeError('Too many redirects')

def get_json(url,out):return json.loads(fetch(url,out)[0])

def api(path,**params):return 'https://library.municode.com/api/'+path+('?' +urllib.parse.urlencode(params) if params else '')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('url');p.add_argument('out');a=p.parse_args();b,r=fetch(a.url,a.out);print(json.dumps(r,indent=2))
