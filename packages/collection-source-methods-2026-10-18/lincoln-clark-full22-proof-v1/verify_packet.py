#!/usr/bin/env python3
"""Portable stdlib integrity/identity/closing audit; not a repeated native parser."""
import pathlib,json,hashlib,csv,sys
P=pathlib.Path(__file__).resolve().parent

def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text())
def check():
 manifest=load(P/'MANIFEST.json')
 for x in manifest['files']:
  path=P/x['path'];assert path.is_file()and path.stat().st_size==x['bytes']and sha(path.read_bytes())==x['sha256'],'Manifest mismatch '+x['path']
 run=P/'run';cp=load(run/'checkpoint.json');c=load(run/'config.json');cov=load(run/'coverage.json');inventory=load(P/'clark-uncodified-inventory.json')
 from source_inventory import validate
 assert c==load(P/'ordinance-config.json')and c['coverage_level']=='file_pages'
 assert len(cp['items'])==len(cp['done'])==22 and cp['completed']and not cp.get('failures')
 validate((run/cp['identity']['source_ref']).read_bytes(),c['source_url'],inventory)
 validate((run/cp['consistency']['raw_ref']).read_bytes(),c['source_url'],inventory)
 assert cp['consistency']['consistent']and len(cp['item_consistency'])==22
 aliases=load(P/'capture-to-run-aliases.json');assert len(aliases['documents'])==22
 for item,source,alias in zip(cp['items'],inventory['uncodified_ordinances'],aliases['documents']):
  assert(item['url'],item['heading'])==(source['url'],source['ordinance'])
  initial=run/item['raw_ref'];body=initial.read_bytes();m=load(initial.with_suffix('.receipt.json'))
  closing=next(x for x in cp['item_consistency']if x['id']==item['id']);p=run/closing['raw_ref'];end=p.read_bytes();em=load(p.with_suffix('.receipt.json'))
  assert body.startswith(b'%PDF-')and sha(body)==m['sha256']==sha(end)==em['sha256']==closing['sha256']==alias['sha256']
  assert m['url']==em['url']==item['url']and m['status']==em['status']==200 and closing['matches_initial_content']
  assert em['started_at']>m['started_at'],'Closing must be a genuinely later successful response'
  assert initial.read_bytes()[:5]==b'%PDF-'and not m.get('policy_omitted_image')
 for n,digest in cp['scripts'].items():assert sha((run/'executed'/n).read_bytes())==digest==sha((P/'runtime'/n).read_bytes())
 rows=[json.loads(s)for s in(run/'records.jsonl').read_text().splitlines()];assert len(rows)==198 and len({r['id']for r in rows})==198
 with(run/'records.csv').open(newline='')as f:
  csv.field_size_limit(32000000);csvrows=list(csv.DictReader(f))
 assert[(r['id'],r['text'])for r in csvrows]==[(r['id'],r['text'])for r in rows]
 assert cov['requested_coverage_complete']and cov['requested_level']=='file_pages'and not cov['legal_semantic_coverage_complete']and not cov['jurisdiction_complete']
 proof=load(P/'verify-status.json');assert proof['exit_code']==0 and proof['source_files_unchanged']and not proof['image_api_calls']and not proof['network_calls']
 for name,digest in proof['source_hashes'].items():assert sha((run/name).read_bytes())==digest
 refusal=load(P/'lincoln-comprehensive.receipt.json');assert refusal['status']==403 and sha((P/'lincoln-comprehensive.html').read_bytes())==refusal['sha256']
 return {'manifest_files':len(manifest['files']),'ordinance_documents':22,'physical_pages':198,'native_opening_closing_pairs':22,'source_row_titles_dates':'exact','read_only_producer_files':proof['source_file_count'],'scope':'file_pages only','legal_semantic_coverage_complete':False,'jurisdiction_complete':False,'native_parse_performed':False,'network_or_image_calls':0,'lincoln_http_status':403}
if __name__=='__main__':
 try:print(json.dumps(check(),indent=2))
 except Exception as e:print(json.dumps({'error':str(e)}));sys.exit(3)
