"""Bounded official-page discovery receipts, or explicitly requested public-file download.
No browser, credentials, TLS override or site-specific access workaround is used.
"""
import argparse,concurrent.futures,datetime,hashlib,json,re
from pathlib import Path
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup

def sha(data):return hashlib.sha256(data).hexdigest()
def get(url,path,limit=8*1024*1024):
    if urlparse(url).scheme!='https':raise ValueError('HTTPS source required')
    if (urlparse(url).hostname or '').lower().removeprefix('www.')=='ecode360.com':raise ValueError('Publisher probes disabled in official-alternatives scope')
    path=Path(path)
    if path.exists() or Path(str(path)+'.receipt.json').exists():raise ValueError('Use fresh output path')
    receipt={'url':url,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'certificate_verification':True,'status':'attempted'}
    data=b''
    try:
        with requests.get(url,timeout=30,stream=True,allow_redirects=False) as r:
            receipt.update(http_status=r.status_code,final_url=r.url,content_type=r.headers.get('Content-Type'),last_modified=r.headers.get('Last-Modified'),location=r.headers.get('Location'),redirects=[{'status':x.status_code,'url':x.url} for x in r.history])
            for part in r.iter_content(65536):
                data+=part
                if len(data)>limit:raise ValueError('Bounded byte limit exceeded')
            if r.status_code in {301,302,303,307,308}:raise ValueError('Redirect retained but not followed: '+urljoin(url,r.headers.get('Location','')))
            if r.status_code!=200:raise ValueError('HTTP '+str(r.status_code))
            if not data:raise ValueError('Empty HTTP200 response is not a usable source')
            receipt['status']='downloaded'
    except Exception as exc:receipt.update(status='failed',error=type(exc).__name__+': '+str(exc))
    path.parent.mkdir(parents=True,exist_ok=True)
    if data:path.write_bytes(data)
    receipt.update(ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),bytes=len(data),sha256=sha(data))
    if receipt['status']=='downloaded' and 'html' in (receipt.get('content_type') or ''):
        soup=BeautifulSoup(data,'html.parser');receipt['title']=soup.title.get_text(' ',strip=True) if soup.title else ''
        receipt['relevant_links']=[{'label':' '.join(a.get_text(' ',strip=True).split()),'url':urljoin(receipt['final_url'],a['href'])} for a in soup.select('a[href]') if re.search(r'code|charter|ordinance|download|\.pdf|full.?text|complete',a.get_text(' ',strip=True)+' '+a['href'],re.I)]
        main=soup.select_one('main,#main-content,#MainContent,#content,.main-content') or soup.body or soup
        receipt['main_text']=' '.join(main.get_text(' ',strip=True).split())[:24000]
    Path(str(path)+'.receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');return receipt

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True);d=sub.add_parser('discover');d.add_argument('--routes',type=Path,required=True);d.add_argument('--out',type=Path,required=True);a=sub.add_parser('download');a.add_argument('--url',required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--max-mb',type=int,default=40);args=ap.parse_args()
    if args.command=='download':
        result=get(args.url,args.out,args.max_mb*1024*1024);print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['status']=='downloaded' else 1
    if args.out.exists():raise ValueError('Fresh discovery output required')
    routes=json.loads(args.routes.read_text());jobs=[(r['slug'],i,url) for r in routes for i,url in enumerate(r['official_pages'])]
    def job(j):
        slug,i,url=j;return {'slug':slug,'receipt':get(url,args.out/slug/(str(i)+'.html'))}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(job,jobs))
    (args.out/'INDEX.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'attempts':len(results),'downloaded':sum(x['receipt']['status']=='downloaded' for x in results)},indent=2))
if __name__=='__main__':raise SystemExit(main())
