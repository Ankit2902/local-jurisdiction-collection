#!/usr/bin/env python3
"""Offline deterministic retained-source replay, CSV parity and table geometry verification."""
import csv,hashlib,json,platform,sys,tempfile
from pathlib import Path
from bs4 import BeautifulSoup
import collect
ROOT=Path(__file__).resolve().parent
SAMPLES={'phoenix':'phoenix-final','bakersfield':'bakersfield-browser','newark':'newark-live','anchorage':'anchorage-browser','burlington':'burlington-leaf-export'}
def geometry(t):
 t=BeautifulSoup(str(t),'html.parser')
 for im in t.select('img'):im.replace_with('[IMAGE]'+(' '+im.get('alt') if im.get('alt') else ''))
 return [[{'tag':c.name,'text':c.get_text(' ',strip=True),'rowspan':c.get('rowspan'),'colspan':c.get('colspan')} for c in r.find_all(['td','th'],recursive=False)] for r in t.select('tr')]
def main():
 jobs=json.loads((ROOT/'jobs.json').read_text());report=[]
 for slug,folder in SAMPLES.items():
  source=ROOT/'evidence'/folder;meta=json.loads((source/'acquisition.json').read_text());saved=(source/'records.jsonl').read_bytes();checks=json.loads((source/'checks.json').read_text())
  with tempfile.TemporaryDirectory() as tmp:
   target=Path(tmp)
   for n in ['source.html','acquisition.json']:(target/n).write_bytes((source/n).read_bytes())
   replay=collect.parse(jobs[slug],target)
   assert (target/'records.jsonl').read_bytes()==saved,'nondeterministic JSONL '+slug
   assert (target/'records.csv').read_bytes()==(source/'records.csv').read_bytes(),'CSV mismatch '+slug
  table_checks=[]
  if slug=='newark':
   details=json.loads((source/'parse-details.json').read_text());s=BeautifulSoup((source/'source.html').read_text(),'html.parser')
   for rec in details['source_records']:
    body=s.find(id=rec['node_id']+'_content');orig=body.select('table');parsed=BeautifulSoup(rec['semantic_html'],'html.parser').select('table')
    assert [geometry(t) for t in orig]==[geometry(t) for t in parsed],rec['node_id']
    table_checks.append({'node_id':rec['node_id'],'tables':len(orig),'geometry_and_cell_text_equal':True})
  report.append({'job':slug,'source':str(source.relative_to(ROOT)),'records':checks['record_count'],'source_hash_verified':True,'deterministic_jsonl_csv_replay':True,'table_checks':table_checks})
 if (ROOT/'offline-verification.json').exists():
  assert json.loads((ROOT/'offline-verification.json').read_text())['results']==report,'retained offline report differs'
 else:
  collect.save(ROOT/'offline-verification.json',{'checked_at':collect.now(),'runtime':{'python':platform.python_version(),'platform':platform.platform()},'results':report})
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
