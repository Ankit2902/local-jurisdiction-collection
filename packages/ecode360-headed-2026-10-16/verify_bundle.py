#!/usr/bin/env python3
"""Verify this portable handoff against its SHA-256 manifest (no network).

--write is for deliberate resealing after reviewed changes, not normal verification.
Runtime installations and Python caches are excluded from the delivery.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / 'BUNDLE-MANIFEST.json'
EXCLUDED = {'.venv', '.browsers', 'node_modules', '__pycache__', '.review-venv', '.DS_Store', '.pytest_cache'}

def files():
    return [p for p in sorted(ROOT.rglob('*')) if p.is_file() and p != MANIFEST
            and not any(part in EXCLUDED for part in p.relative_to(ROOT).parts)
            and p.suffix not in {'.pyc', '.pyo'}]

def hashes():
    return {str(p.relative_to(ROOT)): {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
            for p in files()}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    actual = hashes()
    if args.write:
        MANIFEST.write_text(json.dumps({'schema_version': 1, 'algorithm': 'sha256', 'excluded_runtime_directories': sorted(EXCLUDED), 'files': actual}, indent=2) + '\n')
    expected = json.loads(MANIFEST.read_text())['files']
    errors = [{'path': name, 'problem': 'missing_or_changed'} for name, value in expected.items() if actual.get(name) != value]
    errors += [{'path': name, 'problem': 'unmanifested'} for name in actual.keys() - expected.keys()]
    print(json.dumps({'status': 'PASS' if not errors else 'FAIL', 'files': len(expected), 'bytes': sum(v['bytes'] for v in expected.values()), 'errors': errors}, indent=2))
    return 1 if errors else 0

if __name__ == '__main__':
    raise SystemExit(main())
