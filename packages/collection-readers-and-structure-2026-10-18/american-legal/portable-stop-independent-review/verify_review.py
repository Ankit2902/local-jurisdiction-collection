"""Read-only compact independent peer artifact check."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((H/'MANIFEST.json').read_bytes());actual={str(p.relative_to(H)):sha(p)for p in H.rglob('*')if p.is_file()and p.name!='MANIFEST.json'};assert actual==m['files'];r=json.loads((H/'review.json').read_bytes());assert r['passed']and r['packet_tests']==10 and r['shipped_portable_tests']==6 and len(r['additional_state_request_tripwire_trials'])==12 and r['all23ALcatalog_entries_advised']and r['nonAL_catalog_entries_unchanged']==202 and r['original_tmp_stop_preserved']and not r['freshgate_state_requests_created'];print(json.dumps({'passed':True,'peer_files':len(actual),'AL_scope':23,'unchanged_nonAL':202,'publisher_requests':0},indent=2))
