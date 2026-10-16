"""Prepare relocatable historical evidence from the project archive; not runtime dependency.

This maintainer utility takes explicit source paths and never overwrites source files.
"""
import argparse,json,shutil
from pathlib import Path
from bs4 import BeautifulSoup
from ecode360 import digest,dump,inventory_candidate,parse_page

def main():
 p=argparse.ArgumentParser();p.add_argument('--handoff',required=True);p.add_argument('--cache',required=True);p.add_argument('--out',default=str(Path(__file__).parent));a=p.parse_args()
 dest=Path(a.out);routes=[r for r in json.loads((Path(a.handoff)/'routes.json').read_text())['jurisdictions'] if r['source_type']=='ecode360'];dump(dest/'routes.json',routes)
 candidates=[]
 for path in Path(a.cache).glob('*.html'):
  raw=path.read_bytes();s=BeautifulSoup(raw,'html.parser')
  if not s.body or not s.body.get('data-cust-id') or not s.select('header .contentTitle[data-code-content-type]'):continue
  try:ident,records=parse_page(raw.decode('utf-8'),'https://ecode360.com/'+s.body.get('data-guid',''))
  except Exception:continue
  if not records:continue
  candidates.append((path,raw,s,ident,records))
 summaries=[]
 for route in routes:
  matching=[v for v in candidates if route['jurisdiction'].lower() in v[2].body.get('data-customer-name','').lower()]
  if not matching:continue
  # Prefer an ordinary chapter; retain one historical legal DOM per jurisdiction.
  matching.sort(key=lambda x: (not (x[2].title and 'chapter' in x[2].title.get_text().lower()),len(x[4])))
  path,raw,s,ident,records=matching[0];folder=dest/'fixtures'/'historical'/route['slug'];folder.mkdir(parents=True,exist_ok=True)
  (folder/'chapter.html').write_bytes(raw)
  canonical=s.select_one('link[rel=canonical]');url='https://ecode360.com'+canonical['href'] if canonical else route['discovery_url']
  cand=inventory_candidate(raw.decode('utf-8'),url);dump(folder/'toc-candidate.json',cand)
  inventory_nodes=cand['nodes'];nidset={n['node_id'] for n in inventory_nodes}
  parsedids={r['node_id'] for r in records}
  for n in inventory_nodes:
   n['classification']='substantive' if n['node_id'] in parsedids else 'unresolved'
   if n['node_id'] in parsedids:n['classification_evidence']='chapter.html#'+n['node_id']+'_content'
   n['hierarchy']={}
   longname=s.body.get('data-long-page-string','')
   for component in longname.split(', '):
    if component.lower().startswith('title '):n['hierarchy']['title']=component
    if component.lower().startswith('chapter '):n['hierarchy']['chapter']=component
  inv={'jurisdiction_slug':route['slug'],'jurisdiction':route['jurisdiction'],'publication_id':'municipal-code',
       'code_name':'Municipal Code','identity':ident,'source_version':'retained-publisher-code-'+ident['code_id']+'-date-'+ident['currency_raw'],
       'inventory_complete':False,'inventory_scope':'retained chapter on-page TOC only',
       'inventory_evidence':{'path':'chapter.html','sha256':digest(raw),'selector':'#toc .contentTitle[data-code-content-type][data-guid]',
        'note':'Independent navigation headings compared to body headers; partial chapter candidate, not complete publication inventory.'},
       'scrape_date':'2026-10-15','source_retrieval_date':'unknown; bundled August 2026 pilot cache; replay date is not retrieval date',
       'nodes':inventory_nodes}
  dump(folder/'inventory.json',inv)
  dump(folder/'artifacts.json',{'artifacts':[{'path':'chapter.html','sha256':digest(raw),'url':url,'retrieved_at':None,'source':'historical retained pilot cache'}]})
  dump(folder/'origin.json',{'source_path':str(path),'sha256':digest(raw),'bundled_at':'2026-10-15','historical_pilot':'2026-08-28 receipt context; raw capture timestamp unavailable','official_routing_currentness':'unverified'})
  summaries.append({'slug':route['slug'],'title':s.title.get_text() if s.title else '', 'url':url,'raw_sha256':digest(raw),
                    'node_count':len(inventory_nodes),'parsed_record_count':len(records),'raw_path':str((folder/'chapter.html').relative_to(dest)),
                    'source_has_table':bool(s.select('.section_content table')),'source_has_litem':bool(s.select('.section_content .litem')),
                    'source_has_image':bool(s.select('.section_content img'))})
 dump(dest/'evidence'/'historical-fixtures.json',summaries);print(json.dumps(summaries,indent=2))
if __name__=='__main__':main()
