#!/usr/bin/env python3
"""One serial bounded headed sample per reviewed route, no automatic route retry."""
import argparse,time
from pathlib import Path
import ecode360 as e
from headed_probe import probe
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--delay',type=float,default=12);p.add_argument('--slugs',nargs='*');p.add_argument('--exclude-slugs',nargs='*',default=[]);a=p.parse_args();rows=e.load(ROOT/'route-registry.json');results=[]
for row in rows:
 if a.slugs and row['slug'] not in a.slugs:continue
 if row['slug'] in a.exclude_slugs:continue
 if (ROOT/'headed-live/CURRENT-HOST-STOP.json').exists():print('HOST_STOPPED',flush=True);break
 try:
  r=probe(row['discovery_url'],row['slug'],row['customer_id'],Path(a.out)/row['slug'],ROOT/'headed-live/RESUMPTION.json',60,row['code_id'],inspect_download=True)
  result={'slug':row['slug'],'accepted':r['accepted'],'initial_http_status':r['initial_http_status'],'final_document_http_status':r['final_document_http_status'],'rate_limit':bool(r['rate_limit']),'bodies':len(r.get('browser_state',{}).get('section_bodies',[])),'receipt':str(Path(a.out)/row['slug']/'receipt.json')};results.append(result);print(result,flush=True);e.dump(Path(a.out)/'summary.json',results)
  if r['rate_limit']:break
 except Exception as ex:print({'slug':row['slug'],'error':str(ex)},flush=True);break
 time.sleep(max(a.delay,10))
