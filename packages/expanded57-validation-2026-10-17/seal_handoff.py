#!/usr/bin/env python3
"""Create the final SHA-256 manifest, verify the package, then ZIP the exact files."""
import datetime
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from build_handoff import EXCLUDE, ROOT, sha

def main():
    files = []
    for p in sorted(ROOT.rglob('*')):
        rel = p.relative_to(ROOT)
        if any(part in EXCLUDE for part in rel.parts) or p.suffix in ('.pyc', '.pyo'):
            continue
        if rel.as_posix() in ('MANIFEST.json', 'integrity-verification.json'):
            continue
        if p.is_symlink():
            raise RuntimeError('Unexpected symlink in deliverable: ' + str(rel))
        if p.is_file():
            files.append({'path': rel.as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)})
    manifest = {'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'hash': 'SHA-256', 'excluded': sorted(EXCLUDE) + ['*.pyc', '*.pyo', 'root manifest itself', 'root integrity report'],
                'files': files}
    (ROOT / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    result = subprocess.run([sys.executable, str(ROOT / 'verify_handoff.py')], capture_output=True, text=True)
    print(result.stdout, flush=True)
    if result.returncode:
        raise RuntimeError(result.stderr or 'Integrity verification failed')
    (ROOT / 'integrity-verification.json').write_text(result.stdout)
    archive = ROOT.parent / (ROOT.name + '.zip')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=4, allowZip64=True) as z:
        for row in files:
            z.write(ROOT / row['path'], ROOT.name + '/' + row['path'])
        for name in ('MANIFEST.json', 'integrity-verification.json'):
            z.write(ROOT / name, ROOT.name + '/' + name)
    with zipfile.ZipFile(archive) as z:
        bad = z.testzip()
        if bad:
            raise RuntimeError('ZIP CRC check failed: ' + bad)
        expected = {ROOT.name + '/' + row['path'] for row in files} | {ROOT.name + '/MANIFEST.json', ROOT.name + '/integrity-verification.json'}
        assert set(z.namelist()) == expected
    checksum = sha(archive)
    archive.with_suffix('.zip.sha256').write_text(checksum + '  ' + archive.name + '\n')
    print(json.dumps({'archive': str(archive), 'bytes': archive.stat().st_size, 'sha256': checksum,
                      'manifest_files': len(files), 'zip_crc_passed': True}, indent=2))

if __name__ == '__main__':
    main()
