import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'MANIFEST.json').read_text())
for item in manifest['files']:
 p=(root/item['path']).resolve();assert p.is_relative_to(root) and p.is_file()
 assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],item['path']
summary=json.loads((root/'validation-summary.json').read_text())
assert summary['passed'] and summary['launcher_before']==summary['launcher_after']
assert all(c['exit']==0 for c in summary['commands'])
print(json.dumps({'passed':True,'read_only':True,'files':len(manifest['files'])}))
