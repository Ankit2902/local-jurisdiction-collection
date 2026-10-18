"""Census scoped exclusions against original raw bytes; no producer imports."""
import pathlib,json,hashlib,re,collections,time
from bs4 import BeautifulSoup
P=pathlib.Path(__file__).resolve().parents[4];O=pathlib.Path(__file__).resolve().parent
S=P/'outputs/collection-readiness-post-91f6c59-2026-10-17/ecode/albany-image-context-replay-v2'
cp=json.loads((S/'checkpoint.json').read_text());counts=collections.Counter();hits=[];t=time.monotonic();bodies=0
for a in cp['artifacts']:
 if a['status']!=200:continue
 p=S/a['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256']; soup=BeautifulSoup(p.read_bytes(),'html.parser')
 code=soup.find(id='codeContent')
 if not code:continue
 for body in code.find_all(id=re.compile(r'^\d+_content$')):
  if 'content' not in body.get('class',[]):continue
  bodies+=1
  for e in body.find_all(True):
   if e.name in ['script','style','button','input','noscript']:counts['tag:'+e.name]+=1;hits.append([a['path'],body['id'],str(e)])
   for c in ['actions','selection-control','contentTitle']:
    if c in e.get('class',[]):counts['class:'+c]+=1;hits.append([a['path'],body['id'],str(e)])
assert bodies==3252 and not hits
r={'passed':True,'original_owned_bodies_checked':bodies,'scoped_exclusion_matches':dict(counts),'matches':hits,'interpretation':'No such UI tag/class exists within any original owned body; filtering them cannot hide any actual legal text in this observed source. Outer UI is separately classified.','producer_imports_or_network_image_operations':0,'source_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'seconds':time.monotonic()-t}
(O/'scoped-ui-exclusion-census.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
