#!/usr/bin/env python3
"""Small serial public-source acquisitions. No authentication, challenge handling or retries."""
import argparse,datetime,hashlib,json,pathlib,time,urllib.request,urllib.error
BASE=pathlib.Path(__file__).resolve().parent
UA='CompliSolv validation/1.0 (public municipal-code research)'
SOURCES={
 'portland_index':'https://www.portland.gov/code',
 'portland_title1':'https://www.portland.gov/code/1/all',
 'portland_title18':'https://www.portland.gov/code/18/all',
 'portland_zoning':'https://www.portland.gov/code/33',
 'portland_charter_index':'https://www.portland.gov/charter-code-policies',
 'portland_charter':'https://www.portland.gov/charter',
 'portland_zoning_ch10':'https://www.portland.gov/sites/default/files/code/10-legal-framewk_0.pdf',
 'baltimore_index':'https://codes.baltimorecity.gov/',
 'baltimore_repo':'https://api.github.com/repos/baltimore-legref/law-html',
 'baltimore_html_bulk':'https://codeload.github.com/baltimore-legref/law-html/zip/refs/heads/publication/2026-09-28',
 'milwaukee_index':'https://city.milwaukee.gov/cityclerk/lrb/ordinances/tableofcontents',
 'milwaukee_zoning_pdf':'https://city.milwaukee.gov/ImageLibrary/Groups/ccClerk/Ordinances/Volume-2/CH295-sub5.pdf'}
def fetch(name,url,out):
 raw=out/'raw';raw.mkdir(parents=True,exist_ok=True)
 meta={'url':url,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'Python urllib HTTPS GET'}
 ext='zip' if name.endswith('bulk') else 'json' if name.endswith('repo') else 'pdf' if url.endswith('.pdf') else 'html'
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA}),timeout=180) as r:
   data=r.read(160_000_001)
   if len(data)>160_000_000:raise ValueError('160MB validation download limit exceeded')
   meta.update(status=r.status,final_url=r.url,headers=dict(r.headers))
 except urllib.error.HTTPError as e:
  data=e.read();ext='error.html';meta.update(status=e.code,error=str(e),headers=dict(e.headers))
 except Exception as e:
  meta['error']=str(e);data=b'';ext='error.txt'
 fn=f'raw/{name}.{ext}';(out/fn).write_bytes(data)
 meta.update(path=fn,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
 (raw/f'{name}.meta.json').write_text(json.dumps(meta,indent=2)+'\n');print(name,meta.get('status'),len(data),flush=True)
 return meta
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--only',nargs='+',choices=SOURCES,default=list(SOURCES));ap.add_argument('--out',type=pathlib.Path,default=BASE);a=ap.parse_args()
 for i,n in enumerate(a.only):
  if i:time.sleep(3)
  m=fetch(n,SOURCES[n],a.out)
  if m.get('status')==429:break # Respect any Retry-After; no further family requests in this run.
