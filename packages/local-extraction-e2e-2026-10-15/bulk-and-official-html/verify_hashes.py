"""Write/verify portable SHA-256 manifest; excludes volatile Python bytecode."""
import argparse,hashlib,json
from pathlib import Path
BASE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();target=BASE/'ARTIFACT-HASHES.json'
files={str(f.relative_to(BASE)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(BASE.rglob('*')) if f.is_file() and f!=target and '__pycache__' not in f.parts and '.venv' not in f.parts and not f.name.endswith('.tmp')}
if a.write:target.write_text(json.dumps(files,indent=2)+'\n');print('Wrote',len(files),'hashes')
else:
 expected=json.loads(target.read_text());fail=[name for name,digest in expected.items() if files.get(name)!=digest]
 if fail:raise SystemExit('Hash mismatches: '+repr(fail))
 print('Verified',len(expected),'hashes')
