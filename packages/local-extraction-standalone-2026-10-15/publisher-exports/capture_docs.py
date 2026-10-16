#!/usr/bin/env python3
"""Bounded public documentation capture; never weakens TLS or supplies credentials."""
import argparse, datetime, hashlib, json, platform
from pathlib import Path
import requests
SOURCES={
 'ecode-tools':'https://ecode360.com/help/tools',
 'ecode-faq':'https://ecode360.com/help/faq',
 'ecode-users':'https://ecode360.com/help/users',
 'ecode-api':'https://developer.ecode360.com/',
 'subscription':'https://www.icccodesolutions.org/subscription-services/',
 'user-level-chart-2020':'https://ecode360.com/help/pdf/eCode360_UserLevelsChart_20.pdf',
 'codepublishing-home':'https://www.codepublishing.com/',
}
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
 rows=[]
 for key,url in SOURCES.items():
  row={'id':key,'requested_url':url,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'requests ordinary public GET, TLS verification enabled','python':platform.python_version(),'requests':requests.__version__}
  try:
   r=requests.get(url,timeout=40);data=r.content;ext='.pdf' if data.startswith(b'%PDF-') else '.html';path=args.out/(key+ext);path.write_bytes(data)
   row.update(status=r.status_code,final_url=r.url,redirects=[{'status':x.status_code,'url':x.url,'location':x.headers.get('location')} for x in r.history],headers={k:v for k,v in r.headers.items() if k.lower() in ('content-type','etag','last-modified','date')},path=str(path),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
  except requests.RequestException as e: row['error']=str(e)
  row['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();rows.append(row)
 (args.out/'receipts.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps([{'id':r['id'],'status':r.get('status'),'bytes':r.get('bytes'),'error':r.get('error')} for r in rows],indent=2))
if __name__=='__main__':main()
