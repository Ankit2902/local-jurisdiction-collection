#!/usr/bin/env python3
"""Check current package manifests and run acquisition JavaScript regressions.

Offline only. Requires Node20+; --node may select a particular executable.
Writes review logs outside the package-level sealed evidence directories.
"""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--node', default='node')
    args = ap.parse_args()
    out = ROOT / 'integration/independent-review'
    out.mkdir(exist_ok=True)
    node = []
    for package, script, checks in [('ecode360', 'test_capture.mjs', 11), ('codepublishing', 'test_acquire_cua.mjs', 10), ('municipal-codes', 'test_checksum.mjs', 6)]:
        p = ROOT / package / script
        before = hashlib.sha256(p.read_bytes()).hexdigest()
        proc = subprocess.run([args.node, script], cwd=p.parent, text=True, capture_output=True)
        log = out / (package + '-node.txt')
        log.write_text(proc.stdout + proc.stderr)
        node.append({'package': package, 'command': 'node ' + script, 'exit_code': proc.returncode, 'checks': checks, 'passed': proc.returncode == 0 and before == hashlib.sha256(p.read_bytes()).hexdigest(), 'source_sha256': before, 'log': str(log.relative_to(ROOT))})
    manifests = [
        ('ecode360', 'BUNDLE-MANIFEST.json', 'sha256'),
        ('codepublishing', 'PACKAGE-SHA256.json', 'files'),
        ('municipal-codes', 'VALIDATION-REPORT.json', 'artifact_hashes'),
        ('gridics', 'E2E-VALIDATION.json', 'artifact_hashes'),
        ('civicplus', 'E2E-ARTIFACT-HASHES.json', None),
        ('bulk-and-official-html', 'ARTIFACT-HASHES.json', None)]
    verified = []
    for package, file, key in manifests:
        data = json.loads((ROOT / package / file).read_text())
        entries = data[key] if key else data
        errors = []
        for name, digest in entries.items():
            p = ROOT / package / name
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
                errors.append(name)
        verified.append({'package': package, 'manifest': package + '/' + file, 'checked': len(entries), 'passed': not errors, 'errors': errors})
    report = {'reviewed_at': datetime.now(timezone.utc).isoformat(), 'node_version': subprocess.check_output([args.node, '--version'], text=True).strip(), 'node_suites': node, 'node_checks': sum(x['checks'] for x in node), 'package_manifests': verified, 'all_passed': all(x['passed'] for x in node + verified)}
    (out / 'ARTIFACT-REVIEW.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['all_passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
