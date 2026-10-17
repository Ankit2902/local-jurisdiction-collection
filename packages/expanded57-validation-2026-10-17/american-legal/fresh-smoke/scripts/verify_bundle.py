#!/usr/bin/env python3
"""Verify sealed artifact bytes and report schema, using only Python standard library."""
import hashlib,json
from pathlib import Path
base=Path(__file__).resolve().parents[1]
manifest=json.loads((base/'ARTIFACT-HASHES.json').read_text())
for item in manifest:
 p=base/item['path'];assert p.is_file(),str(p);assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],str(p)
rows=json.loads((base/'results.json').read_text());assignment=json.loads((base/'assignment.json').read_text());assert len(rows)==len(assignment)==11
required={'sequence','jurisdiction','state','source_url','source_family','status','acquisition_method','publisher_download','tested_scope','complete_corpus','record_count','checks','command','evidence_paths','script_paths','limitations','next_action'}
assert {x['sequence'] for x in rows}=={x['sequence'] for x in assignment}
for row in rows:
 assert required<=set(row);assert row['complete_corpus'] is False
 for rel in row['evidence_paths']+row['script_paths']:assert (base/rel).is_file(),rel
 if row['status']=='standalone_e2e_pass':assert row['record_count']>=2
 if row['publisher_download']['status']=='passed':assert any(c['check']=='native_text_matches_rendered' and c['passed'] for c in row['checks'])
print('verified',len(manifest),'artifact hashes and',len(rows),'jurisdiction result rows')
