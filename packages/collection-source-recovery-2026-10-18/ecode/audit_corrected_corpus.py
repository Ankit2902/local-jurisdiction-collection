import sys
sys.dont_write_bytecode=True
import json,hashlib,re
from pathlib import Path
B=Path(__file__).resolve().parent;package=B/'corrected-corpus-v3';source=package/'evidence/input'
records=[json.loads(x) for x in (source/'records.jsonl').read_text().splitlines()];by={r['id']:r for r in records};rows=json.loads((package/'aggregate-fulltext.json').read_text())['provisions'];checks=[]
assert len(rows)==len(records)==3006 and len(by)==3006 and all(len(r)==16 for r in rows)
for row in rows:
 nid=row['source_url'].rstrip('/').split('/')[-1];r=by[nid];assert row['full_text']==r['semantic_html'];checks.append({'id':nid,'canonical_html_sha256':hashlib.sha256(row['full_text'].encode()).hexdigest()})
assert len({r['id'] for r in checks})==len(rows)
images=sum(r['full_text'].count('[IMAGE]') for r in rows);tables=sum(len(re.findall(r'<table(?:\s|>)',r['full_text'])) for r in rows)
assert images==440 and tables==256
rep=json.loads((package/'validation-report.json').read_text());cov=json.loads((source/'coverage.json').read_text());assert rep['complete'] is False and rep['selected_publication_ready'] is False and cov['complete'] is False and cov['required_assets']==4
out={'passed':True,'rows':len(rows),'fields_per_row':16,'all_canonical_html_bytes_equal':True,'all_source_owned_records_exactly_once':True,'tables':tables,'image_placeholders':images,'publication_complete':False,'selected_publication_ready':False,'required_unqualified_assets':4,'source_record_sha256':hashlib.sha256((source/'records.jsonl').read_bytes()).hexdigest(),'aggregate_fulltext_sha256':hashlib.sha256((package/'aggregate-fulltext.json').read_bytes()).hexdigest(),'row_bindings':checks,'scope':'Actual exported corrected canonical acquired HTML only; raw source fidelity separately audited; no publication completeness or fresh acquisition claim'}
(B/'corrected-corpus-all-row-audit-v3.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='row_bindings'}))
