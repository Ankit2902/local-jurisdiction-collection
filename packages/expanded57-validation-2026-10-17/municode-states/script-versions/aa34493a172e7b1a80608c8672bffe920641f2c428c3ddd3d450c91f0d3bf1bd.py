#!/usr/bin/env python3
"""Source-backed heading/cross-reference/table checks; offline; no missing-target invention."""
import json,pathlib,hashlib
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1]
for folder in list(ROOT.glob('direct/*'))+list(ROOT.glob('supplemental/*')):
 output=folder/'normalized/sections.jsonl'
 if not output.exists():continue
 rows=[json.loads(x) for x in output.read_text().splitlines()];treefile=folder/'toc-full.json'
 if not treefile.exists() and 'supplemental' in str(folder):treefile=ROOT/'direct/des_moines-ia/toc-full.json'
 ids=set()
 def walk(n):
  if n.get('Id'):ids.add(n['Id'])
  for c in n.get('Children') or[]:walk(c)
 if treefile.exists():walk(json.loads(treefile.read_text()))
 checks=[]
 for row in rows:
  s=BeautifulSoup(row['html'],'html.parser');links=[]
  for a in s.find_all('a'):
   attrs=dict(a.attrs);target=attrs.get('data-nodeid') or attrs.get('data-node-id') or attrs.get('data-chunk-id');links.append({'text':a.get_text(' ',strip=True),'attributes':attrs,'target_node_id':target,'target_in_retained_toc':target in ids if target else None})
  heading=lambda v:' '.join(BeautifulSoup(v,'html.parser').get_text(' ',strip=True).split())
  checks.append({'node_id':row['node_id'],'toc_and_content_heading_match':heading(row['toc_heading'])==heading(row['heading']),'source_html_hash_matches':hashlib.sha256(row['html'].encode()).hexdigest()==row['body_sha256'],'source_table_elements':len(s.find_all('table')),'normalized_tables':len(row['tables']),'links_with_complete_source_attributes':links,'same_publication_targets_present_in_TOC':all(x['target_in_retained_toc'] for x in links if x['target_node_id'] and str(x['attributes'].get('data-product-id',row['product_id']))==str(row['product_id']))})
 report={'network_used':False,'checked_records':len(rows),'checks':checks,'passed':all(x['toc_and_content_heading_match'] and x['source_html_hash_matches'] and x['source_table_elements']==x['normalized_tables'] and x['same_publication_targets_present_in_TOC'] for x in checks),'limitation':'Cross-reference target presence checks use retained full TOC for the same publication; linked section bodies not acquired by this check.'}
 (folder/'quality.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'folder':str(folder.relative_to(ROOT)),'passed':report['passed'],'records':len(rows)}))
