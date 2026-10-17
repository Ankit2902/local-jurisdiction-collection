"""Explicit deterministic package manifest build; do not run this mutable build after sealing."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
skip={'.venv','node_modules','__pycache__'}
manifest={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name not in {'manifest-sha256.json','.DS_Store'} and not p.suffix=='.pyc' and not any(x in skip for x in p.relative_to(ROOT).parts)}
(ROOT/'manifest-sha256.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n');print(json.dumps({'files':len(manifest)}))
