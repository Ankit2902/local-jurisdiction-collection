import sys
sys.dont_write_bytecode=True
import argparse,json,urllib.parse,urllib.request,urllib.error
from pathlib import Path
from bs4 import BeautifulSoup
from discover import ROOT,transport
p=argparse.ArgumentParser();p.add_argument('--url',required=True);p.add_argument('--name',required=True);p.add_argument('--head',action='store_true');a=p.parse_args()
u=urllib.parse.urlsplit(a.url)
assert u.scheme=='https'and u.hostname in {'www.cambridgema.gov','www.brla.gov'}
assert a.name.replace('-','').isalnum()
out=ROOT/'source'/(a.name+('.headers.json'if a.head else'.html'))
assert not out.exists(),'Existing acquisition retained; no automatic retry'
if a.head:
 transport.reserve(a.url);meta={'url':a.url,'method':'HEAD','started_at':transport.now(),'body_read':False}
 try:
  with urllib.request.build_opener(transport.Redirect()).open(urllib.request.Request(a.url,method='HEAD',headers={'User-Agent':'CompliSolv municipal publication research/1.0'}),timeout=90)as res:
   meta.update(status=res.status,final_url=res.url,headers=dict(res.headers))
 except urllib.error.HTTPError as exc:meta.update(status=exc.code,final_url=exc.url,headers=dict(exc.headers))
 if meta['status']in (403,429)or any(k.lower()=='cf-mitigated'and'challenge'in v.lower()for k,v in meta['headers'].items()):
  transport.stop(a.url,meta['status'],meta['headers'],'HTTP refusal/rate limit/challenge');meta['access_stop']=True
 meta['finished_at']=transport.now();out.write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta,indent=2));sys.exit(2if meta.get('access_stop')else 0)
data,meta=transport.fetch(a.url,max_bytes=3_000_000);out.write_bytes(data);out.with_suffix('.receipt.json').write_text(json.dumps(meta,indent=2)+'\n')
if meta.get('access_stop')or meta['status']!=200:sys.exit(2)
s=BeautifulSoup(data,'html.parser')
for n in s.select('script,style,nav,header,footer'):n.decompose()
s=s.select_one('main')or s
d={'source_url':a.url,'source_sha256':meta['sha256'],'headings':[n.get_text(' ',strip=True)for n in s.select('h1,h2,h3,h4')],'text':s.get_text('\n',strip=True),'anchors':[{'label':n.get_text(' ',strip=True),'href':n['href'],'url':urllib.parse.urljoin(a.url,n['href'])}for n in s.select('a[href]')]}
out.with_suffix('.analysis.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':meta['status'],'bytes':len(data),'anchors':len(d['anchors']),'sha256':meta['sha256']}))
