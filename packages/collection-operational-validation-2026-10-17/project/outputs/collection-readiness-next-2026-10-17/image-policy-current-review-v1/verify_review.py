import sys;sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
B=Path(__file__).resolve().parent
m=json.loads((B/'MANIFEST.json').read_text())
for f in m['files']:assert hashlib.sha256((B/f['path']).read_bytes()).hexdigest()==f['sha256'],f['path']
r=json.loads((B/'review.json').read_text());assert r['existing_lightweight_checks']==72 and r['all_correctly_invoked_checks_passed'] and r['source_stable_during_checks'];assert all(x['passed'] for x in r['results']);assert r['reviewer_repo_mutations']==r['new_publisher_requests']==r['heavy_PDF_replays']==0
s=json.loads((B/'final-source-rescan.json').read_text());assert s['source_review_passed'] and s['raw_before_inert_issues_repaired_by_owner'] and s['new_attachment_stream_audit_scope_repaired_by_owner'] and s['independent_updated_auditor_tests_passed']==6
print(json.dumps({'review_scope_passed':True,'files_verified':len(m['files']),'initial_existing_checks':72,'independent_updated_auditor_tests':6,'findings_reported_and_source_patched':3,'owner_browser_execution_receipt_pending':s['owner_bounded_browser_execution_receipt_pending'],'readonly':True}))
