#!/usr/bin/env python3
"""Independently rerun every delivered package's offline unittest suite.
Run with the Python environment documented in README.md. No live acquisition.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ['ecode360', 'codepublishing', 'municipal-codes', 'gridics', 'civicplus', 'bulk-and-official-html']

def source_hashes(folder):
    excluded = {'__pycache__', '.venv', '.browsers', 'node_modules', '.review-venv'}
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob('*')) if p.is_file() and p.suffix in {'.py', '.mjs', '.js'}
            and not any(part in excluded for part in p.parts)}

def main():
    out = ROOT / 'integration' / 'independent-review'
    out.mkdir(parents=True, exist_ok=True)
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--packages', nargs='+', choices=PACKAGES, default=PACKAGES)
    selected = ap.parse_args().packages
    results = []
    for name in selected:
        folder = ROOT / name
        args = ['-m', 'unittest', 'discover', '-s', '.', '-p', 'test*.py', '-v']
        if name == 'municipal-codes':
            args = ['-m', 'unittest', '-v'] + [p.stem for p in sorted(folder.glob('test*.py'))] + ['validate_retained', 'validate_live_snapshots']
        command = [sys.executable] + args
        before_hashes = source_hashes(folder)
        proc = subprocess.run(command, cwd=folder, text=True, capture_output=True)
        log = proc.stdout + proc.stderr
        (out / (name + '.txt')).write_text(log, encoding='utf-8')
        found = re.search(r'Ran (\d+) tests? in', log)
        count = int(found.group(1)) if found else 0
        scripts = source_hashes(folder)
        source_unchanged = scripts == before_hashes
        result = {'package': name, 'command': 'python ' + ' '.join(args),
                  'exit_code': proc.returncode, 'tests': count,
                  'passed': proc.returncode == 0 and count > 0 and source_unchanged,
                  'source_unchanged_during_tests': source_unchanged,
                  'log': 'integration/independent-review/' + name + '.txt', 'delivered_source_sha256': scripts}
        results.append(result)
        print(name, count, 'PASS' if result['passed'] else 'FAIL', flush=True)
    existing = out / 'RESULTS.json'
    if existing.exists():
        previous = json.loads(existing.read_text())['packages']
        results.extend(r for r in previous if r['package'] not in selected)
    report = {'reviewed_at': datetime.now(timezone.utc).isoformat(), 'python': sys.version,
              'scope': 'Offline tests and retained-source replay only; does not certify a full collection or future browser automation.',
              'packages': results, 'total_tests': sum(r['tests'] for r in results),
              'all_passed': len(results) == len(PACKAGES) and all(r['passed'] for r in results)}
    (out / 'RESULTS.json').write_text(json.dumps(report, indent=2) + '\n')
    return 0 if all(r['passed'] for r in results if r['package'] in selected) else 1

if __name__ == '__main__':
    raise SystemExit(main())
