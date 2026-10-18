"""Gated HEAD sizes for observed native links only; no redirects/retries/body reads."""
from pathlib import Path
import sys,json,urllib.request,urllib.error,hashlib
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P/'runtime'));import transport
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**kw):return None
rows=json.loads((P/'clark-uncodified-inventory.json').read_text())['uncodified_ordinances'];out=[]
for row in rows:
 url=row['url'];transport.reserve(url);m={'url':url,'method':'HEAD','started_at':transport.now(),'body_read':False,'bytes_read':0,'ordinance':row['ordinance'],'transport':'Ordinary urllib HEAD with shared official transport.reserve/stop; redirects deliberately not followed, no GET fallback'}
 try:
  response=urllib.request.build_opener(NoRedirect()).open(urllib.request.Request(url,method='HEAD',headers={'User-Agent':'CompliSolv municipal publication research/1.0'}),timeout=180)
 except urllib.error.HTTPError as e:response=e
 with response:
  m.update(status=response.code,final_url=response.url,headers=dict(response.headers),finished_at=transport.now())
  # Deliberately never call read(), including HTTPError bodies or image MIME.
 challenge=any(k.lower()=='cf-mitigated'and 'challenge'in str(v).lower()for k,v in m['headers'].items())
 if m['status']in(403,429)or challenge:transport.stop(url,m['status'],m['headers'],'Observed native PDF HEAD refusal/rate/challenge; no GET fallback');m['access_stop']=True
 out.append(m);(P/'size-metadata.json').write_text(json.dumps({'completed_metadata':len(out)==len(rows)and all(m['status']==200 for m in out),'expected':len(rows),'responses':out,'native_body_requests_or_reads':0},indent=2)+'\n');print(json.dumps({k:v for k,v in m.items()if k!='headers'}),flush=True)
 if m['status']!=200 or challenge:break
