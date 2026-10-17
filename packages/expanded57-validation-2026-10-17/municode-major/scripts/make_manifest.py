"""Hash package files after final offline replay; exclude caches and the manifest itself."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
files=[]
for p in sorted(ROOT.rglob('*')):
 if not p.is_file() or any(x in p.parts for x in ['__pycache__','.venv','node_modules','.git']):continue
 if p.name=='MANIFEST.json':continue
 files.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(ROOT/'MANIFEST.json').write_text(json.dumps({'generated_at':datetime.now(timezone.utc).isoformat(),'files':files},indent=2));print(json.dumps({'files':len(files),'bytes':sum(x['bytes'] for x in files)}))
