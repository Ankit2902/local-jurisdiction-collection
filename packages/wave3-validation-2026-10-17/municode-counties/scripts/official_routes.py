"""Official government routing evidence only. Never follows a publisher redirect."""
import json,hashlib,platform,time,urllib.request,urllib.error,urllib.parse,argparse
from datetime import datetime,timezone
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
SOURCES={
'baton-rouge-udc':'https://www.brla.gov/706/Unified-Development-Code',
'clark-title30':'https://www.clarkcountynv.gov/government/departments/comprehensive_planning_department/library/title-30',
'clark-county':'https://www.clarkcountynv.gov/government/elected_officials/county_clerk/county-code',
'cambridge-zoning':'https://www.cambridgema.gov/cdd/zoninganddevelopment/zoning/ordinance',
'stamford':'https://www.stamfordct.gov/government/boards-commissions/board-of-representatives',
'baton-rouge':'https://www.brla.gov/1129/Code-of-Ordinances'}
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.current=None
 def handle_starttag(self,t,a):
  d=dict(a)
  if t=='a' and d.get('href'):self.current={'href':d['href'],'text':''}
 def handle_data(self,d):
  if self.current:self.current['text']+=d
 def handle_endtag(self,t):
  if t=='a' and self.current:self.links.append(self.current);self.current=None

def run(offline=False):
 out=ROOT/'evidence/routes';out.mkdir(parents=True,exist_ok=True);inventory=[]
 for name,url in SOURCES.items():
  p=out/(name+'.html');rp=p.with_name(p.name+'.receipt.json')
  if not p.exists() and not offline:
   assert urllib.parse.urlparse(url).hostname.endswith('.gov');started=datetime.now(timezone.utc).isoformat();status=None;headers={};body=b'';error=None
   try:
    r=urllib.request.build_opener(NoRedirect()).open(urllib.request.Request(url,headers={'User-Agent':'CompliSolv bounded official-source validation/1.0'}),timeout=45);body=r.read();status=r.status;headers=dict(r.headers)
   except urllib.error.HTTPError as ex:body=ex.read();status=ex.code;headers=dict(ex.headers);error=str(ex)
   except Exception as ex:error=repr(ex)
   p.write_bytes(body);rp.write_text(json.dumps({'url':url,'started_at':started,'finished_at':datetime.now(timezone.utc).isoformat(),'http_status':status,'headers':headers,'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body),'error':error,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'runtime':platform.python_version(),'publisher_requests_sent':0,'redirect_policy':'No redirect followed; publisher destinations inventoried only.'},indent=2));time.sleep(3.5)
  if p.exists():
   parser=Links();parser.feed(p.read_text(errors='replace'));links=[{'url':urllib.parse.urljoin(url,x['href']),'text':' '.join(x['text'].split())} for x in parser.links if any(t in (x['href']+' '+x['text']).lower() for t in ['code','ordinance','zoning','charter','pdf','development','plan of government'])];inventory.append({'name':name,'url':url,'http_status':json.loads(rp.read_text()).get('http_status'),'links':links,'evidence_path':str(p.relative_to(ROOT))});print(name,inventory[-1]['http_status'],len(links),flush=True)
 (ROOT/'official-route-inventory.json').write_text(json.dumps(inventory,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true');run(p.parse_args().offline)
