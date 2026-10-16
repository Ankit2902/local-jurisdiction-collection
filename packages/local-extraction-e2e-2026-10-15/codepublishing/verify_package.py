"""Verify delivery file hashes. Extra work/, .venv/ and Python cache files are allowed."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = json.loads((root/'PACKAGE-SHA256.json').read_text())
failures=[]
for name, expected in manifest['files'].items():
    path=(root/name).resolve()
    if root not in path.parents or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        failures.append(name)
print(json.dumps({'files_verified':len(manifest['files']), 'failures':failures, 'status':'passed' if not failures else 'failed'},indent=2))
raise SystemExit(bool(failures))
