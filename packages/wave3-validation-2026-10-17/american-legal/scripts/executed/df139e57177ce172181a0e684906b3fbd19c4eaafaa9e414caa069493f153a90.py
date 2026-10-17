#!/usr/bin/env python3
"""Small serial official-source evidence acquisition; never follows publisher links automatically."""
import datetime,hashlib,json,sys,time,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCES=[('cincinnati-route','https://www.cincinnati-oh.gov/council/references-resources/municipal-code/','.html'),('fairfax-route','https://www.fairfaxcounty.gov/plan2build/codes-ordinances-and-regulations-overview','.html'),('fairfax-zoning-route','https://www.fairfaxcounty.gov/planning-development/zoning-ordinance','.html'),('toledo-route','https://toledo.oh.gov/departments/plan-commission/codes','.html'),('sandiego-county-route','https://www.sandiegocounty.gov/content/sdc/cob/ocd.html.html','.html'),('cincinnati-ch319-excerpt','https://www.cincinnati-oh.gov/sites/dote/assets/File/Appendix%20E%20Cincinnati%20Municipal%20Code.pdf','.pdf')]
def run():
 root=ROOT/'raw'/'official';root.mkdir(exist_ok=True);script=Path(__file__);h=hashlib.sha256(script.read_bytes()).hexdigest();(ROOT/'scripts'/'executed'/(h+'.py')).write_bytes(script.read_bytes());stop_hosts=set()
 for name,url,ext in SOURCES:
  host=urllib.parse.urlsplit(url).hostname
  if host in stop_hosts:continue
  receipt={'url':url,'acquired_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'script_sha256':h,'runtime':sys.version,'method':'Python urllib ordinary HTTP GET'}
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'CompliSolv public legal-source bounded validation'}),timeout=60) as r:b=r.read();receipt.update(status=r.status,final_url=r.url,headers=dict(r.headers))
  except urllib.error.HTTPError as e:b=e.read();receipt.update(status=e.code,error=str(e),headers=dict(e.headers));stop_hosts.add(host) if e.code in (403,429) else None
  except Exception as e:b=b'';receipt['error']=str(e)
  p=root/(name+ext);p.write_bytes(b);receipt.update(bytes=len(b),sha256=hashlib.sha256(b).hexdigest());p.with_suffix(p.suffix+'.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(name,receipt.get('status'),len(b),flush=True);time.sleep(3.5)
if __name__=='__main__':run()
