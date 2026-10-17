#!/usr/bin/env python3
"""Serial public native HTTP acquisition with immutable executed-script provenance."""
import argparse,datetime,hashlib,json,pathlib,platform,sys,time,urllib.request,urllib.error,urllib.parse
SELF=pathlib.Path(__file__).resolve()
def sha(b):return hashlib.sha256(b).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def run(out,jobs):
 out.mkdir(parents=True,exist_ok=True);executed=out/'executed';executed.mkdir(exist_ok=True);script=SELF.read_bytes();(executed/(sha(script)+'.py')).write_bytes(script)
 for i,j in enumerate(jobs):
  if i:time.sleep(3.5)
  stem=j['name'];meta={'url':j['url'],'name':stem,'retrieved_utc':now(),'script_sha256':sha(script),'executed_script':'executed/'+sha(script)+'.py','command':sys.argv,'runtime':{'python':platform.python_version()},'method':'standalone urllib HTTPS; no retries','http_method':j.get('method','GET'),'request_data':j.get('data')}
  if (out/(stem+'.meta.json')).exists():raise RuntimeError('Refusing existing acquisition name; use fresh --out')
  try:
   with urllib.request.urlopen(urllib.request.Request(j['url'],data=urllib.parse.urlencode(j['data']).encode() if j.get('data') else None,method=j.get('method','GET'),headers={'User-Agent':'CompliSolv public municipal-code validation/1.0'}),timeout=120) as r:
    data=r.read(100_000_001)
    if len(data)>100_000_000:raise ValueError('100MB bounded download cap')
    meta.update(status=r.status,final_url=r.url,headers=dict(r.headers));ext=j.get('ext','html')
  except urllib.error.HTTPError as e:data=e.read();ext='error.html';meta.update(status=e.code,error=str(e),headers=dict(e.headers))
  except Exception as e:data=str(e).encode();ext='error.txt';meta['error']=str(e)
  filename=stem+'.'+ext;(out/filename).write_bytes(data);meta.update(path=filename,sha256=sha(data),bytes=len(data));(out/(stem+'.meta.json')).write_text(json.dumps(meta,indent=2)+'\n');print(stem,meta.get('status'),len(data),flush=True)
  if meta.get('status')==429:
   (out/'ACCESS-STOP.json').write_text(json.dumps(meta,indent=2));break
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=pathlib.Path,required=True);ap.add_argument('--batch',type=pathlib.Path);ap.add_argument('--name');ap.add_argument('--url');ap.add_argument('--ext',default='html');a=ap.parse_args();jobs=json.loads(a.batch.read_text()) if a.batch else [{'name':a.name,'url':a.url,'ext':a.ext}];run(a.out,jobs)
