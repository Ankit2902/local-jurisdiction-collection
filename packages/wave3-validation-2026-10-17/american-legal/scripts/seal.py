#!/usr/bin/env python3
"""Freeze owned package file hashes; does not modify legal evidence."""
import hashlib,json,platform,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
skip={'.venv','node_modules','__pycache__','.git'}
files={}
for p in sorted(root.rglob('*')):
 if not p.is_file() or any(s in skip for s in p.relative_to(root).parts) or p.name=='manifest.json':continue
 files[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
(root/'manifest.json').write_text(json.dumps({'algorithm':'sha256','files':files,'runtime':{'python':sys.version,'platform':platform.platform()}},indent=2)+'\n')
print(len(files),'files sealed')
