#!/usr/bin/env python3
"""Recover retained publisher OPEN link using standard HTTP (no browser or Codex)."""
import hashlib,json,sys,urllib.request,urllib.error
from pathlib import Path
root=Path(__file__).resolve().parents[1];d=root/'raw'/sys.argv[1];receipt=json.loads((d/'receipt.json').read_text());url=receipt['publisher_export']['links'][0]['url']
try:
 with urllib.request.urlopen(url,timeout=60) as r:b=r.read();status=r.status;ct=r.headers.get('Content-Type','')
 p=d/('publisher-export.zip' if b[:2]==b'PK' else 'publisher-export.html');p.write_bytes(b)
 receipt['publisher_export']={'status':'passed','url':url,'file':str(p.relative_to(root)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'content_type':ct,'http_status':status,'scope':receipt['sample_title'],'format':'publisher Save HTML; not browser print','recovery_method':'Python urllib GET of native public OPEN link'}
 (d/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(status,ct,len(b))
except urllib.error.HTTPError as e:
 (d/'export-http-failure.txt').write_text(str(e)+'\n'+e.read().decode(errors='replace'));raise
