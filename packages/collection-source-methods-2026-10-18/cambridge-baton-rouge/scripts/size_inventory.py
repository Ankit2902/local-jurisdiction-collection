"""Header-only size inventory; no native/image bodies read. Stops on first refusal."""
import sys
sys.dont_write_bytecode=True
import json,urllib.request,urllib.error
from pathlib import Path
from discover import ROOT,transport
rows=json.loads((ROOT/'brla-udc-inventory.json').read_text())['selected_visible_documents']
dest=ROOT/'headers';dest.mkdir(exist_ok=True)
results=[]
for row in rows:
 n=dest/(row['source_document_id']+'.json')
 if n.exists():raise RuntimeError('Existing header attempt retained; no automatic retry')
 if row['source_document_id']=='2263':
  meta=json.loads((ROOT/'source/brla-first-native.headers.json').read_text());assert meta['url']==row['url']and meta['status']==200 and meta['body_read']is False
  meta['reused_exact_initial_HEAD_receipt']='source/brla-first-native.headers.json'
 else:
  transport.reserve(row['url']);meta={'url':row['url'],'method':'HEAD','started_at':transport.now(),'body_read':False}
  try:
   with urllib.request.build_opener(transport.Redirect()).open(urllib.request.Request(row['url'],method='HEAD',headers={'User-Agent':'CompliSolv municipal publication research/1.0'}),timeout=90)as res:meta.update(status=res.status,final_url=res.url,headers=dict(res.headers))
  except urllib.error.HTTPError as exc:meta.update(status=exc.code,final_url=exc.url,headers=dict(exc.headers))
  if meta['status']in (403,429)or any(k.lower()=='cf-mitigated'and'challenge'in v.lower()for k,v in meta['headers'].items()):
   transport.stop(row['url'],meta['status'],meta['headers'],'HTTP refusal/rate limit/challenge');meta['access_stop']=True
  meta['finished_at']=transport.now()
 n.write_text(json.dumps(meta,indent=2)+'\n')
 headers={k.lower():v for k,v in meta['headers'].items()}
 length=headers.get('content-length')
 entry={'ordinal':row['ordinal'],'document_id':row['source_document_id'],'url':row['url'],'label':row['label'],'status':meta['status'],'content_type':headers.get('content-type'),'declared_bytes':int(length)if length and length.isdigit()else None,'receipt':n.relative_to(ROOT).as_posix()}
 results.append(entry);(ROOT/'size-preflight.json').write_text(json.dumps({'results':results,'attempted':len(results),'selected':30,'body_reads':0,'complete':len(results)==30,'known_declared_bytes':sum(x['declared_bytes']or 0 for x in results),'unknown_lengths':sum(x['declared_bytes']is None for x in results)},indent=2)+'\n')
 print(json.dumps(entry),flush=True)
 if meta.get('access_stop')or meta['status']!=200:raise SystemExit(2)
