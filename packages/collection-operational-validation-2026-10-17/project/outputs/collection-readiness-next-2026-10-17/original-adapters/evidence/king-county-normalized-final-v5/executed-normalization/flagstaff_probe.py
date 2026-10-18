"""Read-only bounded parser probe of an actively growing full run; never complete."""
import argparse,json,sys
from pathlib import Path
from source_common import *
from flagstaff_html_normalize import parse

def run(source,out):
 src=Path(source).resolve();out=Path(out);s=load(src/'checkpoint.json');reports=[]
 for a in s['artifacts']:
  if a['role']!='content':continue
  raw=(src/a['path']).read_bytes()
  if sha(raw)!=a['sha256']:raise ValueError('Corrupt source')
  records,report=parse(raw,a['source_url'],[e for e in s['inventory'] if key(e['source_url'])==a['source_url']]);reports.append(report)
 r={'complete':False,'scope':'Bounded parser probe of exact acquired artifacts at checkpoint read; not full publication','source_checkpoint_sha256':sha((src/'checkpoint.json').read_bytes()),'inventory_documents':len(s['source_documents']),'acquired_parsed_documents':len(reports),'source_blocks':sum(x['source_blocks'] for x in reports),'owned_blocks':sum(x['owned_blocks'] for x in reports),'source_toc_edges':sum(x['source_toc_edges'] for x in reports),'matched_toc_edges':sum(x['matched_toc_edges'] for x in reports),'missing_toc':sum(len(x['missing_toc_edges']) for x in reports),'extra_headings':sum(len(x['extra_body_headings']) for x in reports),'heading_only':sum(len(x['heading_only_unresolved']) for x in reports),'reports':reports};save(out,r);return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();r=run(a.source,a.out);print(json.dumps({k:v for k,v in r.items() if k!='reports'},indent=2))
