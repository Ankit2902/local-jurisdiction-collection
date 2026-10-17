"""Government-only route capture. Refuses redirects to publisher domains; fresh directory required."""
import argparse,hashlib,json,platform,re,time,urllib.request,urllib.error
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin,urlparse
ALLOWED={'www.cityofhenderson.com','www.orlando.gov','www.greensboro-nc.gov','www.durhamnc.gov','www.jerseycitynj.gov','www.plano.gov','www.stpete.org','www.cityofmadison.com','madison.gov','www.lexingtonky.gov','www.reno.gov'}
class GovRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  if urlparse(newurl).hostname not in ALLOWED:raise urllib.error.HTTPError(req.full_url,code,'External redirect preserved; not followed',headers,fp)
  return super().redirect_request(req,fp,code,msg,headers,newurl)
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,t,a):
  if t=='a' and dict(a).get('href'):self.links.append(dict(a)['href'])
def capture(url,out):
 if urlparse(url).hostname not in ALLOWED:raise ValueError('Government host not allowed')
 if out.exists():raise ValueError('Fresh output directory required')
 out.mkdir(parents=True);(out/'executed-discover_official.py').write_bytes(Path(__file__).read_bytes());r={'url':url,'started_at':datetime.now(timezone.utc).isoformat(),'method':'government-only-ordinary-http-routing','python':platform.python_version(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};raw=b''
 try:
  with urllib.request.build_opener(GovRedirect()).open(urllib.request.Request(url,headers={'User-Agent':'CompliSolv official code routing validation/1.0'}),timeout=60) as response:raw=response.read();r.update(status=response.status,final_url=response.url,headers=dict(response.headers))
 except urllib.error.HTTPError as e:raw=e.read();r.update(status=e.code,error=str(e),headers=dict(e.headers))
 except Exception as e:r.update(status=None,error=str(e))
 (out/'source.html').write_bytes(raw);r.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),finished_at=datetime.now(timezone.utc).isoformat());p=Links();p.feed(raw.decode('utf8','replace'));r['related_links']=[urljoin(r.get('final_url',url),h) for h in p.links if re.search('municode|ecode|ordinance|charter|zoning|development|code',h,re.I)];(out/'receipt.json').write_text(json.dumps(r,indent=2));print(json.dumps({'url':url,'status':r['status'],'related_links':r['related_links']}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('url');p.add_argument('out',type=Path);a=p.parse_args();capture(a.url,a.out)
