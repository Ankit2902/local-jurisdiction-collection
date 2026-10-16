#!/usr/bin/env python3
"""Offline route planner and diagnostic sample auditor. No network or extraction."""
import argparse
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def inspect_rows(rows):
    findings = []
    numbers = collections.Counter()
    for i, row in enumerate(rows, 1):
        number = str(row.get('section_number') or '').strip()
        name = str(row.get('section_name') or '').strip()
        body = str(row.get('full_text') or '')
        if number.lower() in {'contents', 'table of contents'} or name.lower() in {'contents', 'table of contents'}:
            findings.append({'row': i, 'code': 'CONTENTS_RECORD', 'detail': 'Navigation/chapter aggregate requires source-aware segmentation review.'})
        if not number or not name:
            findings.append({'row': i, 'code': 'MISSING_LABEL', 'detail': 'Missing number or heading; confirm source-backed identity. Unnumbered operative material may be legitimate.'})
        if name.lower().startswith('rev.'):
            findings.append({'row': i, 'code': 'REVISION_HEADER', 'detail': 'Likely PDF running header or continuation fragment.'})
        if any(0x80 <= ord(ch) <= 0x9f or ch == '\ufffd' for ch in name + body):
            findings.append({'row': i, 'code': 'ENCODING_REVIEW', 'detail': 'Control/replacement character requires comparison with raw source.'})
        if not body.strip():
            findings.append({'row': i, 'code': 'EMPTY_BODY', 'detail': 'Classify against source; reserved/repealed nodes may legitimately be empty.'})
        if number:
            numbers[(row.get('code_name', ''), number)] += 1
    for (family, number), count in numbers.items():
        if count > 1:
            findings.append({'code': 'REPEATED_LOCATOR', 'family': family, 'number': number, 'count': count, 'detail': 'Review only. Reused locators are not grounds to merge or drop records.'})
    return findings

def audit_bundle(bundle):
    routes = json.loads((bundle / 'routes.json').read_text())['jurisdictions']
    output = []
    for item in routes:
        path = bundle / item['sample']
        rows = json.loads(path.read_text())['provisions']
        output.append({'slug': item['slug'], 'source_type': item['source_type'], 'sample_rows': len(rows), 'findings': inspect_rows(rows)})
    return {'kind': 'diagnostic_only_not_acceptance', 'jurisdictions': output,
            'summary': {'jurisdictions': len(output), 'sample_rows': sum(x['sample_rows'] for x in output),
                        'jurisdictions_flagged': sum(bool(x['findings']) for x in output)}}

def verify_bundle(bundle):
    manifest = json.loads((bundle / 'BUNDLE-MANIFEST.json').read_text())
    failures = []
    for item in manifest['files']:
        p = bundle / item['path']
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != item['sha256']:
            failures.append(item['path'])
    return {'files_checked': len(manifest['files']), 'failures': failures}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['plan', 'audit-samples', 'verify'])
    parser.add_argument('--bundle', type=Path, default=ROOT)
    parser.add_argument('--source-type', help='Filter plan to one source_type from routes.json')
    parser.add_argument('--output', type=Path, help='Optional JSON result file; otherwise stdout')
    args = parser.parse_args()
    if args.command == 'plan':
        data = json.loads((args.bundle / 'routes.json').read_text())
        selected = [j for j in data['jurisdictions'] if not args.source_type or j['source_type'] == args.source_type]
        if args.source_type and not selected:
            parser.error('Unknown source type: ' + args.source_type)
        result = {'kind': 'plan_only_no_fetch', 'counts': dict(collections.Counter(j['source_type'] for j in selected)), 'jurisdictions': selected}
    elif args.command == 'audit-samples':
        result = audit_bundle(args.bundle)
    else:
        result = verify_bundle(args.bundle)
    value = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    if args.output:
        args.output.write_text(value)
    else:
        print(value, end='')
    return 1 if args.command == 'verify' and result['failures'] else 0

if __name__ == '__main__':
    raise SystemExit(main())
