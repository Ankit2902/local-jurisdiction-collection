#!/usr/bin/env python3
"""Retain official routing-page evidence without following blocked publisher routes."""
import hashlib,json,time,urllib.request,urllib.error
from pathlib import Path
base=Path(__file__).resolve().parents[1];items=json.loads((base/'research/publication-inventory.json').read_text());out=base/'research/official-routes';out.mkdir(exist_ok=True)
for item in items:
 url=item['official_route'];receipt={'url':url,'acquired_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
 try:
  with urllib.request.urlopen(url,timeout=35) as r:b=r.read();receipt.update(status=r.status,final_url=r.url,content_type=r.headers.get('Content-Type'))
  (out/f"{item['sequence']}.html").write_bytes(b);receipt.update(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 except urllib.error.HTTPError as e:
  b=e.read();(out/f"{item['sequence']}-failure.html").write_bytes(b);receipt.update(status=e.code,error=str(e),sha256=hashlib.sha256(b).hexdigest())
 except Exception as e:receipt['error']=str(e)
 (out/f"{item['sequence']}.json").write_text(json.dumps(receipt,indent=2)+'\n');print(item['sequence'],receipt.get('status'),receipt.get('error',''),flush=True);time.sleep(3.5)
