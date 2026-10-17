"""Serial official-government routing discovery; never sends publisher requests."""
import json,hashlib,platform,re,time,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone
from html.parser import HTMLParser
from urllib.parse import urljoin,urlparse
ROOT=Path(__file__).resolve().parents[1]
JOBS=[('madison','https://madison.gov/attorney'),('lexington','https://www.lexingtonky.gov/government/laws-ordinances/code-ordinances'),('reno','https://www.reno.gov/government/departments/city-attorney/civil-division/faqs.php')]
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,t,a):
  if t=='a' and dict(a).get('href'):self.links.append(dict(a)['href'])
if __name__=='__main__':
 results=[]
 for name,url in JOBS:
  out=ROOT/'evidence/official-routes'/name;out.mkdir(parents=True,exist_ok=True);rec={'url':url,'started_at':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};raw=b''
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'CompliSolv official code routing validation/1.0'}),timeout=60) as response:raw=response.read();rec.update(status=response.status,final_url=response.url,headers=dict(response.headers))
  except urllib.error.HTTPError as e:raw=e.read();rec.update(status=e.code,error=str(e),headers=dict(e.headers))
  except Exception as e:rec.update(status=None,error=str(e))
  (out/'source.html').write_bytes(raw);rec.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),finished_at=datetime.now(timezone.utc).isoformat());(out/'receipt.json').write_text(json.dumps(rec,indent=2));p=Links();p.feed(raw.decode('utf8','replace'));links=[urljoin(rec.get('final_url',url),h) for h in p.links if re.search('municode|ecode|ordinance|charter|zoning|\.pdf',h,re.I)];results.append({'jurisdiction':name,'status':rec['status'],'url':url,'links':links});print(name,rec['status'],json.dumps(links),flush=True);time.sleep(3.5)
 (ROOT/'official-routing.json').write_text(json.dumps(results,indent=2))
