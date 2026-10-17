#!/usr/bin/env python3
"""Bounded route discovery; retained landing HTML is not a passing legal sample."""
import argparse,datetime,json,pathlib,platform,hashlib,shutil,sys,gzip
from html.parser import HTMLParser
from urllib.parse import urljoin
from transport import fetch
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCES={'lincoln-home':'https://online.encodeplus.com/regs/lincoln-ne/','lincoln-code':'https://online.encodeplus.com/regs/lincoln-ne/doc-viewer.aspx','lincoln-official':'https://www.lincoln.ne.gov/City/Departments/City-Attorneys-Office','overland-home':'https://codes.opkansas.org/municipal-code/doc-view.aspx','overland-documents':'https://codes.opkansas.org/municipal-code/page.aspx?name=documents','overland-official':'https://www.opkansas.gov/unified-development-ordinance-update?contentId=92fbe589-2186-411e-a63d-39ca43c301f3'}
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.current=None;self.scripts=[]
 def handle_starttag(self,t,a):
  d=dict(a)
  if t=='a' and d.get('href'):self.current={'url':d['href'],'text':''}
  if t=='script' and d.get('src'):self.scripts.append(d['src'])
 def handle_data(self,d):
  if self.current:self.current['text']+=d
 def handle_endtag(self,t):
  if t=='a' and self.current:self.links.append(self.current);self.current=None
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--offline',action='store_true');p.add_argument('--key',choices=SOURCES);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 if not a.offline:
  if any(a.out.iterdir()):p.error('Fresh live output directory must be empty')
  snap=a.out/'script-versions';snap.mkdir()
  for name in ['discover.py','transport.py']:
   src=ROOT/'scripts'/name;shutil.copy2(src,snap/(hashlib.sha256(src.read_bytes()).hexdigest()+src.suffix))
  (a.out/'run.json').write_text(json.dumps({'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':sys.argv,'runtime':platform.python_version(),'os':platform.platform(),'script_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()},indent=2))
 result={}
 for key,url in SOURCES.items():
  if a.key and a.key!=key:continue
  dest=a.out/(key+'.html')
  if not a.offline:
   try:fetch(url,dest)
   except Exception as e:print(key,str(e),flush=True)
  if not dest.exists():continue
  receipt=json.loads(dest.with_name(dest.name+'.receipt.json').read_text());data=dest.read_bytes();encoding=next((v for k,v in receipt.get('headers',{}).items() if k.lower()=='content-encoding'),'')
  if encoding=='br':
   import brotli
   data=brotli.decompress(data)
  elif encoding=='gzip':data=gzip.decompress(data)
  html=data.decode('utf-8',errors='replace');lp=Links();lp.feed(html)
  links=[{**l,'url':urljoin(receipt.get('final_url',url),l['url'])} for l in lp.links]
  result[key]={'url':url,'status':receipt.get('http_status'),'links':links,'scripts':[urljoin(url,x) for x in lp.scripts]}
 (a.out/'discovery.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:{'status':v['status'],'links':len(v['links']),'scripts':v['scripts']} for k,v in result.items()},indent=2))
