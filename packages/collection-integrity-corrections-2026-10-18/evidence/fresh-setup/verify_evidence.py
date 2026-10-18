"""Verify compact retained setup evidence without runtime imports or network."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'MANIFEST.json').read_text())
for item in manifest['files']:
 path=(root/item['path']).resolve()
 assert path.is_relative_to(root) and path.is_file(),item['path']
 assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],item['path']
assert manifest['excluded_operational_directories']==['runtime-v1']
audit=json.loads((root/'independent-runtime-audit.json').read_text())
receipt=json.loads((root/'fresh-runtime-receipt.json').read_text())
commands=json.loads((root/'commands.json').read_text())
assert audit['passed'] and audit['direct_pins_matched']==11 and audit['source_integrity']['unchanged']
assert all(c['exit']==0 for c in commands) and len(commands)==4
assert audit['local_alias_check']['same_api'] and receipt['browser']['headed'] and receipt['browser']['passed']
assert audit['publisher_requests']==0 and receipt['publisher_requests']==0
assert not audit['standalone_profile_comparison']['profiles_equivalent_claimed']
assert not audit['standalone_profile_comparison']['live_american_legal_transport_qualified']
assert not audit['setup_or_doctor_defects_observed']
print(json.dumps({'passed':True,'read_only':True,'files':len(manifest['files']),'fresh_setup_and_doctor_passed':True,'runtime_directory_not_required':True,'publisher_requests':0}))
