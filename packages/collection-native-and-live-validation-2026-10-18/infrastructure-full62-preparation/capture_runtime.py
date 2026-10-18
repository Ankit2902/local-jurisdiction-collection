#!/usr/bin/env python3
"""Run only after the parent announces a final code freeze."""
import argparse,hashlib,json,pathlib,shutil
p=argparse.ArgumentParser();p.add_argument('--repo',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
if a.out.exists():raise ValueError('Fresh snapshot path required')
family=a.repo/'collectors/encodeplus';names=sorted([x for x in family.glob('*.py')]+[family/'targets.json',family/'requirements.txt',family/'configs/native-82-0c6b3dc40877.json'])
manifest={}
for source in names:
 rel=source.relative_to(a.repo);dest=a.out/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest);manifest[rel.as_posix()]=hashlib.sha256(dest.read_bytes()).hexdigest()
for name,h in manifest.items():
 if hashlib.sha256((a.repo/name).read_bytes()).hexdigest()!=h:raise ValueError('Source changed while copying')
(a.out/'SOURCE-HASHES.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
print(json.dumps({'files':len(manifest),'manifest_sha256':hashlib.sha256((a.out/'SOURCE-HASHES.json').read_bytes()).hexdigest()},indent=2))
