#!/usr/bin/env python3
"""One serial bounded headed sample per reviewed route, no automatic route retry."""
import argparse,sys,time
from pathlib import Path
import ecode360 as e
from headed_probe import probe
ROOT=Path(__file__).resolve().parent

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);p.add_argument('--authorization',required=True);p.add_argument('--delay',type=float,default=12);p.add_argument('--slugs',nargs='*');p.add_argument('--exclude-slugs',nargs='*',default=[]);a=p.parse_args(argv)
 if a.slugs is not None and not a.slugs:p.error('empty explicit --slugs selection')
 rows=e.load(ROOT/'route-registry.json');known={r['slug'] for r in rows};requested=set(a.slugs or [])|set(a.exclude_slugs)
 if requested-known:p.error('unreviewed jurisdiction slug: '+','.join(sorted(requested-known)))
 out=Path(a.out)
 if out.exists() and any(out.iterdir()):p.error('new empty output directory required; prior acquisition evidence is immutable')
 if (ROOT/'headed-live/CURRENT-HOST-STOP.json').exists():p.error('publisher host stopped; explicit review/resumption required')
 try:authorization=e.load(a.authorization)
 except (OSError,ValueError) as ex:p.error('authorization record unreadable: '+str(ex))
 if not authorization.get('explicit_user_authorized_resumption'):p.error('explicit reviewed authorization record required')
 rows=[r for r in rows if (not a.slugs or r['slug'] in a.slugs) and r['slug'] not in a.exclude_slugs]
 if not rows:p.error('no reviewed routes selected')
 results=[];blocked=False
 for row in rows:
  if (ROOT/'headed-live/CURRENT-HOST-STOP.json').exists():print('HOST_STOPPED',flush=True);blocked=True;break
  try:
   r=probe(row['discovery_url'],row['slug'],row['customer_id'],out/row['slug'],Path(a.authorization),60,row['code_id'],inspect_download=True)
   result={'slug':row['slug'],'accepted':r['accepted'],'initial_http_status':r['initial_http_status'],'final_document_http_status':r['final_document_http_status'],'rate_limit':bool(r['rate_limit']),'bodies':len(r.get('browser_state',{}).get('section_bodies',[])),'receipt':str(out/row['slug']/'receipt.json')};results.append(result);print(result,flush=True);e.dump(out/'summary.json',results)
   if not r['accepted']:blocked=True
   if r['rate_limit']:blocked=True;break
  except Exception as ex:print({'slug':row['slug'],'error':str(ex)},flush=True);blocked=True;break
  time.sleep(max(a.delay,10))
 return 2 if blocked else 0
if __name__=='__main__':sys.exit(main())
