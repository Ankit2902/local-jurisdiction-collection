"""Portable strict source retention helpers; only explicit legitimate routes, no images."""
import datetime,hashlib,json,os,re,shutil
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,urljoin
from bs4 import BeautifulSoup
import shared_transport as transport

def sha(b):return hashlib.sha256(b).hexdigest()
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,v):transport.atomic(p,json.dumps(v,indent=2,ensure_ascii=False).encode()+b'\n')
def load(p):return json.loads(Path(p).read_text())
def clean(t):return re.sub(r'\s+',' ',str(t).replace('\xa0',' ')).strip()
def key(u):
 p=urlsplit(u);return urlunsplit((p.scheme,p.netloc,p.path,p.query,''))
def forbid(u):
 p=urlsplit(u);h=p.hostname or ''
 if p.scheme!='https' or p.username or p.password:raise ValueError('Only ordinary public HTTPS source routes accepted')
 if h=='ecode360.com' or h.endswith('.municipal.codes') or h.endswith('municode.com') or h in ['static.spokanecity.org','ldh.la.gov']:raise ValueError('Stopped publisher/host: no source request allowed')
 if re.search(r'\.(png|jpe?g|gif|svg|webp|avif|bmp|tiff?)(?:$|[?#])',u,re.I):raise ValueError('Separate image request prohibited')
def decode(raw,content_type=''):
 try:text=raw.decode('utf-8-sig');encoding='utf-8-sig'
 except UnicodeDecodeError:
  m=re.search(br'charset\s*=\s*[\"\']?([\w-]+)',raw[:4096],re.I);encoding=m.group(1).decode() if m else 'cp1252'
  if encoding.lower() in ['iso-8859-1','latin1','windows-1252']:encoding='cp1252'
  text=raw.decode(encoding,'strict')
 if '\ufffd' in text or re.search('[\x80-\x9f]',text):raise ValueError('Unresolved source decoding defect')
 return text,encoding

def source_snapshot(out,names):
 folder=out/'executed-acquisition';folder.mkdir();f={}
 for n in names:
  p=Path(__file__).parent/n;raw=p.read_bytes();(folder/n).write_bytes(raw);f[n]=sha(raw)
 return f

def acquire(out,state,role,url):
 forbid(url);b,m=transport.fetch(url);entry={'role':role,'source_url':url,'path':f'raw/{len(state["artifacts"]):04d}-{role}.bin',**m};transport.atomic(out/entry['path'],b);state['artifacts'].append(entry);save(out/'checkpoint.json',state)
 if m.get('access_stop') or m.get('status')!=200:raise RuntimeError('Source access failed; no retry: '+json.dumps(entry))
 if m.get('policy_omitted_image'):raise ValueError('Source route returned image: body deliberately not downloaded')
 return b,entry
