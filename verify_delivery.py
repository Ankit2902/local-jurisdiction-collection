#!/usr/bin/env python3
"""Verify all manifested delivery bytes. Standard library; no network."""
import hashlib
import json
import argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parent
EXCLUDED={'.venv','.review-venv','.browsers','node_modules','__pycache__','.pytest_cache','.DS_Store','.git'}
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--full',action='store_true',help='Require restored release evidence as well as Git-tracked files')
 args=parser.parse_args()
 manifest=json.loads((ROOT/'DELIVERY-MANIFEST.json').read_text());errors=[];deferred=[]
 for entry in manifest['files']:
  p=ROOT/entry['path']
  if not p.resolve().is_relative_to(ROOT.resolve()):errors.append({'path':entry['path'],'error':'outside_repository'});continue
  if not p.is_file():
   if entry.get('storage')=='release' and not args.full:deferred.append(entry['path']);continue
   errors.append({'path':entry['path'],'error':'missing'});continue
  if p.stat().st_size!=entry['bytes']:errors.append({'path':entry['path'],'error':'size'});continue
  h=hashlib.sha256()
  with p.open('rb') as stream:
   for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
  if h.hexdigest()!=entry['sha256']:errors.append({'path':entry['path'],'error':'sha256'})
 expected={x['path'] for x in manifest['files']}
 directories=manifest.get('managed_directories',['packages','archives'])
 for directory in directories:
  if not (ROOT/directory).resolve().is_relative_to(ROOT.resolve()):raise ValueError('Managed directory outside repository')
 actual={str(p.relative_to(ROOT)) for directory in directories for p in (ROOT/directory).rglob('*') if p.is_file() and not any(x in EXCLUDED for x in p.relative_to(ROOT).parts) and p.suffix not in {'.pyc','.pyo'}}
 for p in sorted(actual-expected):errors.append({'path':p,'error':'unmanifested_delivery_file'})
 print(json.dumps({'status':('PASS_GIT_FILES' if deferred else 'PASS_FULL_DELIVERY') if not errors else 'FAIL','files':len(expected),'bytes':manifest['bytes'],'deferred_release_files':deferred,'next_step':'python3 fetch_evidence.py, then python3 verify_delivery.py --full' if deferred else None,'errors':errors},indent=2))
 return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
