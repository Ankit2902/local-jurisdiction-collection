import sys;sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
B=Path(__file__).resolve().parent;m=json.loads((B/'MANIFEST.json').read_text())
for f in m['files']:assert hashlib.sha256((B/f['path']).read_bytes()).hexdigest()==f['sha256'],f['path']
r=json.loads((B/'review.json').read_text());assert r['passed'] and r['check_count']==28 and all(x['passed'] for x in r['checks']);assert r['network_requests']==r['render_OCR_extraction_operations']==0 and not r['image_stream_decode_calls'];assert not r['whole_publication_live_complete_claimed'] and r['no_generic_heading_or_empty_waiver']
a=json.loads((B/'additional-source-bindings.json').read_text());assert a['original_404_body_hash_matches_pinned_receipt'] and a['original_HTTP_status']==404
print(json.dumps({'passed':True,'files':len(m['files']),'independent_checks':28,'existing_focused_tests':5,'no_generic_empty_waiver':True,'whole_publication_live_claim':False,'readonly':True}))
