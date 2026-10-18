import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'MANIFEST.json').read_text())
for item in manifest['files']:
 p=(root/item['path']).resolve()
 assert p.is_relative_to(root) and p.is_file()
 assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],item['path']
report=json.loads((root/'current-production-validation.json').read_text())
assert report['passed'] and report['source_before']==report['source_after']
assert not report['production_modified'] and all(x['exit']==0 for x in report['commands'])
print(json.dumps({'passed':True,'read_only':True,'files':len(manifest['files']),'current_production_validation_passed':True}))
