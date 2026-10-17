"""Durable response cache and ordinary headed browser transport."""
import base64,datetime,json,os,subprocess,sys
from pathlib import Path
from model import digest,canonical
BASE=Path(__file__).resolve().parent

def atomic(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.'+str(os.getpid())+'.tmp')
 with tmp.open('wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 os.replace(tmp,path)
def save(path,obj):atomic(path,json.dumps(obj,ensure_ascii=False,indent=2).encode()+b'\n')
class Browser:
 def __init__(self):
  env=dict(os.environ,PYTHON=sys.executable);self.p=subprocess.Popen([env.get('NODE_BIN','node'),str(BASE/'browser.cjs')],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
 def call(self,op,url=None,**kw):
  self.p.stdin.write(json.dumps(dict(op=op,url=url,**kw))+'\n');self.p.stdin.flush();line=self.p.stdout.readline()
  if not line:raise RuntimeError('Browser transport ended unexpectedly')
  r=json.loads(line)
  if not r['ok']:raise RuntimeError(json.dumps(r))
  return r['result']
 def close(self):
  if self.p.poll() is None:
   try:self.call('close');self.p.wait(timeout=20)
   except Exception:self.p.terminate();self.p.wait(timeout=20)
class Cache:
 def __init__(self,folder,browser):
  self.folder=Path(folder);self.browser=browser;self.path=self.folder/'requests.json';self.entries=json.loads(self.path.read_text()) if self.path.exists() else {}
  for k,v in self.entries.items():
   assert not Path(v['file']).is_absolute() and '..' not in Path(v['file']).parts,'Unsafe cache path'
   assert digest((self.folder/v['file']).read_bytes())==v['sha256'],'Corrupt cached source '+k
 def fetch(self,url,op='fetch',key=None,**kw):
  key=key or op+':'+url
  if key in self.entries:
   e=self.entries[key];assert e['requested_url']==url and e['op']==op,'Cached request identity mismatch';return (self.folder/e['file']).read_bytes(),e
  try:result=self.browser.call(op,url,**kw)
  except RuntimeError as exc:
   save(self.folder/'failure-response.json',{'url':url,'op':op,'error':str(exc)});raise
  raw=base64.b64decode(result.pop('body'));assert result['status']==200,'HTTP error '+str(result['status']);file='raw/'+digest(key.encode())+'.bin';atomic(self.folder/file,raw)
  for name in ['rendered','scope_html','ready_html']:
   if name in result:
    extra=file+'.'+name+'.html';data=result.pop(name).encode();atomic(self.folder/extra,data);result[name+'_file']=extra;result[name+'_sha256']=digest(data)
  e={'op':op,'requested_url':url,'file':file,'sha256':digest(raw),'bytes':len(raw),'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'response':result};self.entries[key]=e;save(self.path,self.entries);return raw,e
