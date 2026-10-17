#!/usr/bin/env python3
"""Read-only offline source/inventory/output verification, including incomplete-run detection."""
import sys
sys.dont_write_bytecode=True
import argparse,csv,json,pathlib
import collect,model

def verify(run):
 run=pathlib.Path(run).resolve();coverage=collect.reconcile(run);state=collect.load(run/'checkpoint.json');expected=[]
 for item in state['items']:
  p=run/'items'/(model.sha(item['id'].encode())[:24]+'.json')
  if p.exists():expected+=collect.load(p)['records']
 stored=(run/'records.jsonl').read_bytes()
 if stored!=collect.lines(expected):raise ValueError('Global normalized output missing/duplicate/corrupt records')
 with (run/'records.csv').open(newline='') as f:
  csv.field_size_limit(32_000_000);rows=list(csv.DictReader(f))
 if len(rows)!=len(expected) or any(row['id']!=r['id'] or row['text']!=r['text'] for row,r in zip(rows,expected)):raise ValueError('CSV/JSONL roundtrip mismatch')
 if (run/'coverage.json').exists() and collect.load(run/'coverage.json')!=coverage:raise ValueError('Stored coverage differs from recomputed evidence')
 return coverage
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run',type=pathlib.Path);a=p.parse_args()
 try:
  r=verify(a.run);print(json.dumps({'offline':True,'read_only':True,'coverage':collect.brief(r)},indent=2));raise SystemExit(0 if r['requested_coverage_complete'] else 3)
 except Exception as e:print(json.dumps({'offline':True,'read_only':True,'error':str(e)}));raise SystemExit(3)
