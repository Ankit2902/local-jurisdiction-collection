import hashlib,json,os,tempfile
from pathlib import Path

def digest(data):return hashlib.sha256(data).hexdigest()
def canonical(obj):return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def hash_json(obj):return digest(canonical(obj))
def read_json(path):return json.loads(Path(path).read_text())
def atomic_bytes(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as out:out.write(data);out.flush();os.fsync(out.fileno())
  os.replace(name,path)
 finally:
  if os.path.exists(name):os.unlink(name)
def atomic_json(path,obj):atomic_bytes(path,json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True).encode()+b'\n')
def validate_file(root,path,expected):
 p=Path(root)/path
 if not p.is_file() or digest(p.read_bytes())!=expected:raise ValueError('Missing/corrupt retained file: '+str(p))
 return p
