#!/usr/bin/env python3
"""Verify all delivered package/archive bytes. Standard library; no network."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
EXCLUDED={'.venv','.review-venv','.browsers','node_modules','__pycache__','.pytest_cache','.DS_Store','.git'}
def main():
 manifest=json.loads((ROOT/'DELIVERY-MANIFEST.json').read_text());errors=[]
 for entry in manifest['files']:
  p=ROOT/entry['path']
  if not p.is_file():errors.append({'path':entry['path'],'error':'missing'});continue
  if p.stat().st_size!=entry['bytes']:errors.append({'path':entry['path'],'error':'size'});continue
  h=hashlib.sha256()
  with p.open('rb') as stream:
   for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
  if h.hexdigest()!=entry['sha256']:errors.append({'path':entry['path'],'error':'sha256'})
 expected={x['path'] for x in manifest['files']}
 actual={str(p.relative_to(ROOT)) for directory in ['packages','archives'] for p in (ROOT/directory).rglob('*') if p.is_file() and not any(x in EXCLUDED for x in p.relative_to(ROOT).parts) and p.suffix not in {'.pyc','.pyo'}}
 for p in sorted(actual-expected):errors.append({'path':p,'error':'unmanifested_delivery_file'})
 print(json.dumps({'status':'PASS' if not errors else 'FAIL','files':len(expected),'bytes':manifest['bytes'],'errors':errors},indent=2))
 return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
