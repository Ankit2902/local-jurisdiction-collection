#!/usr/bin/env python3
"""Verify the immutable delivered file manifest; no network or source changes."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = json.loads((root / 'BUNDLE-MANIFEST.json').read_text())
failures = []
for item in manifest['files']:
    path = root / item['path']
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        failures.append(item['path'])
print(json.dumps({'verified_files': len(manifest['files']), 'failures': failures}, indent=2))
raise SystemExit(bool(failures))
