import argparse,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent;manifest=root/'ARTIFACT-HASHES.json';a=argparse.ArgumentParser();a.add_argument('--write',action='store_true');args=a.parse_args()
files={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file() and p!=manifest and '__pycache__' not in p.parts and '.venv' not in p.parts}
if args.write:manifest.write_text(json.dumps(files,indent=2)+'\n');print('Wrote',len(files),'hashes')
else:
 expected=json.loads(manifest.read_text());assert all(files.get(p)==h for p,h in expected.items()),'Artifact hash mismatch';print('Verified',len(expected),'hashes')
