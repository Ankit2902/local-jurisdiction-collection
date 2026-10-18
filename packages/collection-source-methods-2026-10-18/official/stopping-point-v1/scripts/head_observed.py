"""One source-observed native document HEAD. No response body or retry."""
import argparse,hashlib,json,pathlib,sys,urllib.error,urllib.request
sys.dont_write_bytecode=True
import transport
from fetch_observed import preflight
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--url',required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();assert not a.out.exists()
 original=transport.reserve
 def reserve(url):preflight(url);return original(url)
 transport.reserve=reserve;reserve(a.url);r={'url':a.url,'method':'HEAD','started_at':transport.now(),'response_body_bytes_read':0,'automatic_retry':False}
 try:
  with urllib.request.build_opener(transport.Redirect()).open(urllib.request.Request(a.url,method='HEAD',headers={'User-Agent':'CompliSolv municipal publication research/1.0'}),timeout=180)as response:r.update(status=response.status,final_url=response.url,headers=dict(response.headers))
 except urllib.error.HTTPError as e:r.update(status=e.code,final_url=e.url,headers=dict(e.headers),error=str(e))
 challenge=any(k.lower()=='cf-mitigated'and 'challenge'in v.lower()for k,v in r['headers'].items())
 if r['status']in[403,429]or challenge:transport.stop(a.url,r['status'],r['headers'],'HEAD refusal/rate-limit/challenge');r['access_stop']=True
 r['finished_at']=transport.now();r['executed_sources']={n:hashlib.sha256((pathlib.Path(__file__).parent/n).read_bytes()).hexdigest()for n in ['head_observed.py','fetch_observed.py','transport.py']};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));return 3 if r['status']!=200 or r.get('access_stop')else 0
if __name__=='__main__':raise SystemExit(main())
