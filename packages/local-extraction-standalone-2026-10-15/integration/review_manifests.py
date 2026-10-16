#!/usr/bin/env python3
"""Read-only verification of the final component manifests."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECS = [
    ('ecode360', 'BUNDLE-MANIFEST.json', 'sha256'),
    ('codepublishing', 'PACKAGE-SHA256.json', 'files'),
    ('municipal-codes', 'SHA256SUMS', 'text'),
    ('publisher-exports', 'ARTIFACT-HASHES.json', 'files'),
    ('official-alternatives', 'ARTIFACT-HASHES.json', None),
    ('integration/runtime-diagnostics', 'RUNTIME-FINDINGS.json', 'artifact_hashes'),
]

def main():
    results = []
    for folder, name, key in SPECS:
        manifest = ROOT / folder / name
        if key == 'text':
            entries = {line.split(maxsplit=1)[1].lstrip('*'): line.split(maxsplit=1)[0] for line in manifest.read_text().splitlines() if line.strip()}
        else:
            data = json.loads(manifest.read_text())
            entries = data[key] if key else data
            if isinstance(entries, list):
                entries = {r['path']: r['sha256'] for r in entries}
        errors = []
        for name, expected in entries.items():
            p = ROOT / folder / name
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
                errors.append(name)
        results.append({'package': folder, 'manifest': str(manifest.relative_to(ROOT)), 'references': len(entries), 'passed': not errors, 'errors': errors})
    result = {'reviewed_at': datetime.now(timezone.utc).isoformat(), 'all_passed': all(r['passed'] for r in results), 'references_verified': sum(r['references'] for r in results), 'packages': results}
    out = ROOT / 'integration/independent-review/MANIFEST-REVIEW.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['all_passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
