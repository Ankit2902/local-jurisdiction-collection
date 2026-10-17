#!/usr/bin/env python3
"""Offline integrity and scope checks for the expanded-jurisdiction handoff.

Run with Python 3.10+: python verify_handoff.py
This validates retained artifacts, not publisher availability or corpus completeness.
"""
import argparse
import hashlib
import json
from pathlib import Path

STATUSES = {'standalone_e2e_pass','standalone_partial','manual_download_import_pass','cua_only','blocked','untested'}

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    args=p.parse_args();root=args.root.resolve();errors=[]
    scope=json.loads((root/'scope57.json').read_text())
    results=json.loads((root/'results57.json').read_text())
    manifest=json.loads((root/'MANIFEST.json').read_text())
    expected={r['sequence']:r for r in scope}
    if len(expected)!=57 or sorted(expected)!=list(range(1,58)):errors.append('Scope is not the frozen first 57 targets')
    ids=[r['sequence'] for r in results]
    if len(ids)!=len(set(ids)) or set(ids)!=set(expected):errors.append('Results must contain every target once')
    for r in results:
        seq=r['sequence']; label=f"{seq}: {r.get('jurisdiction')}"
        if seq not in expected:continue
        if r.get('state')!=expected[seq]['state']:errors.append(label+': state differs from scope')
        if r.get('status') not in STATUSES:errors.append(label+': invalid status')
        if r.get('status')=='standalone_e2e_pass':
            if not isinstance(r.get('record_count'),int) or r['record_count']<=0:errors.append(label+': pass has no positive parsed record count')
            if not r.get('command') or not r.get('checks'):errors.append(label+': pass missing command or checks')
            if not r.get('evidence_paths') or not r.get('script_paths'):errors.append(label+': pass missing evidence or scripts')
        for field in ['evidence_paths','script_paths']:
            for name in r.get(field,[]):
                path=(root/name).resolve()
                if not path.is_relative_to(root):errors.append(label+': path outside handoff: '+name)
                elif not path.exists():errors.append(label+': missing path: '+name)
        if not r.get('tested_scope'):errors.append(label+': missing tested scope')
        if r.get('complete_corpus') is True and not r.get('completeness_evidence'):errors.append(label+': complete corpus claim lacks evidence')
    for item in manifest['files']:
        path=(root/item['path']).resolve()
        if not path.is_relative_to(root):errors.append('Manifest path outside root: '+item['path']);continue
        if not path.is_file():errors.append('Manifest file missing: '+item['path']);continue
        if path.stat().st_size!=item['bytes'] or digest(path)!=item['sha256']:errors.append('Changed file: '+item['path'])
    report={'scope_count':len(expected),'result_count':len(results),'manifest_file_count':len(manifest['files']),'errors':errors,'passed':not errors}
    print(json.dumps(report,indent=2));return 1 if errors else 0

if __name__=='__main__':raise SystemExit(main())
