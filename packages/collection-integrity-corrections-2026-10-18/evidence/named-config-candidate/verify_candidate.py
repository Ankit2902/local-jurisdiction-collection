"""Read-only artifact integrity and minimal-delta checks, no network/runtime installs."""
import difflib,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((root/'MANIFEST.json').read_text())
for item in manifest['files']:
 path=(root/item['path']).resolve()
 assert path.is_relative_to(root) and path.is_file(),item['path']
 assert sha(path)==item['sha256'],item['path']
summary=json.loads((root/'validation-summary.json').read_text())
assert summary['status']=='isolated_candidate_passed_not_promoted'
assert summary['validation']['all_passed'] and summary['network_requests']==0
patch=''
for item in summary['source_changes']:
 rel=item['path'];before=root/'baseline'/rel;after=root/'candidate'/rel
 assert sha(before)==item['before_sha256'] and sha(after)==item['candidate_sha256']
 patch+=''.join(difflib.unified_diff(before.read_text().splitlines(True),after.read_text().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
assert patch==(root/'named-config-binding.patch').read_text()
assert len(summary['source_changes'])==3
assert summary['validation']['focused_tests']==11 and summary['validation']['existing_readiness_tests']==16
print(json.dumps({'passed':True,'read_only':True,'files':len(manifest['files']),'minimal_source_files':3,'candidate_not_promoted':True}))
