"""Portable stdlib-only integrity check; no network/native/image parser imports."""
import sys
sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((ROOT/'CAPTURE-MANIFEST.json').read_text())
for n,r in m['files'].items():
 p=ROOT/'capture'/n
 assert p.stat().st_size==r['bytes']and sha(p)==r['sha256'],n
assert sha(ROOT/'CAPTURE-PROOF.json')==m['capture_proof_sha256']
assert sha(ROOT/'native-capture-summary.json')==m['native_summary_sha256']
assert sha(ROOT/'capture-status.json')==m['capture_status_sha256']
s=json.loads((ROOT/'native-capture-summary.json').read_text())
assert len(s['documents'])==30 and sum(x['pages']for x in s['documents'])==606 and sum(x['bytes']for x in s['documents'])==31_404_496
assert not s['image_calls']and s['whole_publication_qualified']is False and s['text_or_table_parse_performed']is False
for n,h in json.loads((ROOT/'runtime-source-binding.json').read_text()).items():assert sha(ROOT/'runtime'/n)==h,n
for x in s['documents']:
 p=ROOT/'capture'/x['raw_ref'];r=json.loads(p.with_suffix('.receipt.json').read_text())
 assert x['sha256']==r['sha256']==sha(p)and x['url']==r['url']and r['status']==200 and not r.get('access_stop')and not r.get('policy_omitted_image')
print(json.dumps({'passed':True,'capture_files':len(m['files']),'original_PDFs':30,'physical_pages':606,'bytes':31_404_496,'nativeparse_performed':False,'publisher_requests':0,'full_publication_qualified':False},indent=2))
