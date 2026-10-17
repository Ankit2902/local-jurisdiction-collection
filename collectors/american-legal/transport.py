"""Durable response cache and ordinary headed browser transport."""
import base64,datetime,json,os,subprocess,sys,fcntl
from pathlib import Path
from model import digest,canonical
BASE=Path(__file__).resolve().parent
class AccessStop(RuntimeError):pass
class HTTPError(RuntimeError):
 def __init__(self,entry):
  self.entry=entry;self.status=entry['response']['status'];super().__init__('HTTP '+str(self.status)+' '+entry['requested_url'])
class RunLock:
 def __init__(self,folder):
  folder=Path(folder).resolve();folder.parent.mkdir(parents=True,exist_ok=True);self.path=folder.parent/('.'+folder.name+'.lock');self.file=None
 def __enter__(self):
  self.file=self.path.open('a+')
  try:fcntl.flock(self.file,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:self.file.close();raise RuntimeError('Another collector owns output: '+str(self.path))
  self.file.seek(0);self.file.truncate();self.file.write(json.dumps({'pid':os.getpid(),'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}));self.file.flush();return self
 def __exit__(self,*args):
  fcntl.flock(self.file,fcntl.LOCK_UN);self.file.close()

def atomic(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.'+str(os.getpid())+'.tmp')
 with tmp.open('wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 os.replace(tmp,path)
def save(path,obj):atomic(path,json.dumps(obj,ensure_ascii=False,indent=2).encode()+b'\n')
class Browser:
 def __init__(self):
  env=dict(os.environ,PYTHON=sys.executable);self.p=subprocess.Popen([env.get('NODE_BIN','node'),str(BASE/'browser.cjs')],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True);self.in_flight=False
 def call(self,op,url=None,**kw):
  self.in_flight=True;self.p.stdin.write(json.dumps(dict(op=op,url=url,**kw))+'\n');self.p.stdin.flush();line=self.p.stdout.readline();self.in_flight=False
  if not line:raise RuntimeError('Browser transport ended unexpectedly')
  r=json.loads(line)
  if not r['ok']:
   if r.get('access_stop'):raise AccessStop(json.dumps(r))
   raise RuntimeError(json.dumps(r))
  return r['result']
 def close(self):
  if self.p.poll() is None:
   if not self.in_flight:
    try:self.p.stdin.write(json.dumps({'op':'close'})+'\n');self.p.stdin.flush();self.p.wait(timeout=20);return
    except (BrokenPipeError,subprocess.TimeoutExpired):pass
   self.p.terminate()
   try:self.p.wait(timeout=20)
   except subprocess.TimeoutExpired:self.p.kill();self.p.wait(timeout=10)
class Cache:
 def __init__(self,folder,browser):
  self.folder=Path(folder);self.browser=browser;self.path=self.folder/'requests.json';self.entries=json.loads(self.path.read_text()) if self.path.exists() else {};self.retry_unavailable_assets=False;self.refreshed=set()
  for k,v in self.entries.items():
   assert not Path(v['file']).is_absolute() and '..' not in Path(v['file']).parts,'Unsafe cache path'
   assert digest((self.folder/v['file']).read_bytes())==v['sha256'],'Corrupt cached source '+k
 def fetch(self,url,op='fetch',key=None,**kw):
  key=key or op+':'+url
  if key in self.entries:
   e=self.entries[key];assert e['requested_url']==url and e['op']==op,'Cached request identity mismatch'
   if e['response']['status']==200:return (self.folder/e['file']).read_bytes(),e
   if not self.retry_unavailable_assets or op not in ['head','binary'] or key in self.refreshed or e['response']['status'] in [403,429]:raise HTTPError(e)
   self.entries['history:'+str(len(self.entries))+':'+key]=e;del self.entries[key];self.refreshed.add(key);save(self.path,self.entries)
  if op=='export':
   checkpoint=self.folder/'export-checkpoint.json';kw['export_state_file']=str(checkpoint.resolve())
   if checkpoint.exists():
    state=json.loads(checkpoint.read_text());assert state['requested_url']==url and all(state[k]==kw[k] for k in ['code_uuid','code_slug','version']),'Export checkpoint identity differs'
    payload=state['payload'];assert payload['version']==kw['version'] and json.loads(payload['scope'])==[{'code_slug':kw['code_slug']}] and payload['for_print'] is False and payload['output_format']=='html','Export checkpoint scope differs';kw['resume_export']=state
  try:result=self.browser.call(op,url,**kw)
  except RuntimeError as exc:
   save(self.folder/'failure-response.json',{'url':url,'op':op,'error':str(exc)});raise
  raw=base64.b64decode(result.pop('body'));file='raw/'+digest((key+':'+digest(raw)).encode())+'.bin';atomic(self.folder/file,raw)
  for name in ['rendered','scope_html','ready_html']:
   if name in result:
    extra=file+'.'+name+'.html';data=result.pop(name).encode();atomic(self.folder/extra,data);result[name+'_file']=extra;result[name+'_sha256']=digest(data)
  e={'op':op,'requested_url':url,'file':file,'sha256':digest(raw),'bytes':len(raw),'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'response':result};self.entries[key]=e;save(self.path,self.entries)
  if result['status']!=200:raise HTTPError(e)
  return raw,e
