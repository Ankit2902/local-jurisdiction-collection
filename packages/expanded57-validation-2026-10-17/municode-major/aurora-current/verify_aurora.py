#!/usr/bin/env python3
"""Read-only offline replay and native HTML equivalence checks, no browser/network."""
import csv,hashlib,json,sys,tempfile
from pathlib import Path
import collect
ROOT=Path(__file__).resolve().parent

def main():
 job=json.loads((ROOT/'jobs.json').read_text())['aurora'];sample=ROOT/'evidence/sample';meta=json.loads((sample/'acquisition.json').read_text());raw=(sample/'source.html').read_bytes();assert collect.sha(raw)==meta['sha256']
 with tempfile.TemporaryDirectory() as tmp:
  d=Path(tmp)
  for p in ['source.html','acquisition.json']:(d/p).write_bytes((sample/p).read_bytes())
  checks=collect.parse(job,d)
  for p in ['records.jsonl','records.csv']:assert (d/p).read_bytes()==(sample/p).read_bytes(),p
 export=json.loads((sample/'publisher-export.json').read_text());f=sample/export['downloads'][0]['path'];assert collect.sha(f.read_bytes())==export['downloads'][0]['sha256']
 native,notes=collect.mc.parse_page(f.read_text(),meta['url'],job['base']);live=json.loads((sample/'parse-details.json').read_text())['source_records'];assert [(r['citation'],r['full_text']) for r in native]==[(r['citation'],r['full_text']) for r in live]
 assert len(native)==15
 report={'records':len(native),'live_replay_byte_equal_jsonl_csv':True,'native_html_citations_bodies_equal':True,'native_html_hash_verified':True,'table_count':checks['table_count'],'complete_corpus':False,'scope':'General City Code chapter1 articleI;15 operative sections; reserved1-16 through1-35 heading has no operative body and is retained in raw/notes','currency':'Ordinance2026-42, passed August10,2026'}
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
