"""Authoring seal only; excludes local runtime and itself to avoid recursion."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
files=[]
for p in sorted(ROOT.rglob('*')):
 if not p.is_file() or any(x in ['.venv','node_modules','__pycache__'] for x in p.relative_to(ROOT).parts) or p.name in ['manifest.json','.DS_Store'] or p.suffix=='.log':continue
 files.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(ROOT/'manifest.json').write_text(json.dumps({'hash_algorithm':'sha256','excluded':['.venv','node_modules','__pycache__','*.log','manifest.json','.DS_Store'],'files':files},indent=2)+'\n')
print(json.dumps({'files':len(files),'bytes':sum(f['bytes'] for f in files)}))
