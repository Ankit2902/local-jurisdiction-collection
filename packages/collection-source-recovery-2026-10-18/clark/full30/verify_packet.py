#!/usr/bin/env python3
"""Portable stdlib-only byte/receipt/proof verifier. Does not parse PDFs or request network."""
import pathlib,hashlib,json,sys
P=pathlib.Path(__file__).resolve().parent

def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=load(P/'MANIFEST.json')
actual={str(p.relative_to(P))for p in P.rglob('*')if p.is_file()and p.name!='MANIFEST.json'}
assert actual==set(m['files']),'Unexpected/missing selected packet files'
for name,row in m['files'].items():
 p=P/name;assert p.stat().st_size==row['bytes']and sha(p)==row['sha256'],name
aliases=load(P/'compact-body-aliases.json')
for row in aliases['aliases']:
 p=P/row['retained_byte_identical_alias'];assert sha(p)==row['sha256']and p.stat().st_size==row['bytes']
 r=load((P/row['omitted_duplicate']).with_suffix('.receipt.json'));assert r['sha256']==row['sha256']and r['status']==200 and not r.get('access_stop')
s=load(P/'run/checkpoint.json');coverage=load(P/'run/coverage.json');v=load(P/'verify.stdout');status=load(P/'status.json')
assert status['stage']=='collection_terminal'and status['collection_exit']==0 and not status['image_calls']
assert s['completed']and len(s['done'])==len(s['items'])==30 and not s['limits_history']
assert len(s['item_consistency'])==30 and all(x['matches_initial_content']for x in s['item_consistency'])
assert coverage['requested_level']=='file_pages'and coverage['requested_coverage_complete']is True
assert coverage['parsed_record_count']==381 and coverage['image_placeholder_count']==229
assert coverage['legal_semantic_coverage_complete']is False and coverage['jurisdiction_complete']is False
assert v['all_run_files_unchanged']is True and not v['forbidden_calls']
for name,digest in s['scripts'].items():assert sha(P/'run/executed'/name)==sha(P/'runtime'/name)==digest
print(json.dumps({'status':'PASS','file_count':len(m['files']),'bytes':sum(x['bytes']for x in m['files'].values()),'initial_body_aliases':len(aliases['aliases']),'source_scope':'30 official current documents,381physicalpages,file_pages only','native_parse_network_image_calls':0,'qualification':'Manifest/receipt/recorded-terminal checks; actual guarded native verification is retained in verify.stdout, not re-executed.'},indent=2))
