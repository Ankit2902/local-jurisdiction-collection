#!/usr/bin/env python3
"""Bounded public CodeHUB acquisition in a disposable Playwright browser.
No cookies, credentials, anti-bot workarounds, undocumented endpoints or TLS overrides.
"""
import argparse,json,time
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit
from gridics import BASE,VERSION,valid_route,route,inventory_html,parse_html,digest,save,own_heading

# All these selectors occur in the retained 2026-08 pilot DOM. No API is inferred.
TREE='ul.doc-tree[role="tree"]'
CLOSED=TREE+' li.has-children.doc-tree-treenode-switcher-close'

def route_ready(html,url,actual_url,expected_heading=None):
 if actual_url!=url:return False
 try:
  nodes,records,dispositions=parse_html(html,url)
  target=next(n for n in nodes if n['path']==urlsplit(url).fragment)
  if expected_heading and target['display_heading']!=expected_heading:return False
  # Content-bearing target or its actual rendered descendants; reserved targets valid.
  return any(r['row']['source_url']==url or r['row']['source_url'].startswith(url+'/') for r in records) or 'reserved' in target['display_heading'].lower()
 except (ValueError,StopIteration):return False

def wait_ready(page,url,timeout,expected_heading=None):
 deadline=time.monotonic()+timeout;prev=None;stable=0
 while time.monotonic()<deadline:
  html=page.content()
  if route_ready(html,url,page.url,expected_heading):
   # Stability hashes legal content only. Three consecutive observations, fresh page per URL.
   ns,rs,ds=parse_html(html,url);key=digest(json.dumps([ns,rs],sort_keys=True))
   stable=stable+1 if key==prev else 1;prev=key
   if stable>=3:return html
  page.wait_for_timeout(700)
 raise RuntimeError('Requested route content/UUID did not stabilize; no cached success is recorded')

def expand_tree(page,out,max_expansions,timeout):
 page.locator(TREE).wait_for(state='attached',timeout=timeout*1000)
 states=[]
 for ix in range(max_expansions+1):
  html=page.content();rows=inventory_html(html);save(out/'navigation-current.json',rows)
  raw=html.encode();name='raw/navigation-'+digest(raw)+'.html';p=out/name;p.parent.mkdir(exist_ok=True);p.write_bytes(raw)
  states.append({'path':name,'sha256':digest(raw),'node_count':len(rows)})
  collapsed=page.locator(CLOSED)
  if collapsed.count()==0:
   # No claim about unseen virtualization or additional publications without source comparison.
   save(out/'navigation-evidence.json',{'states':states,'all_observed_branches_expanded':all(n['children_enumerated'] for n in rows),'full_inventory_qualified':False,'reason':'Requires publisher/rendered comparison for virtualization and publication scope.'})
   return rows,states
  if ix==max_expansions:raise RuntimeError('Navigation expansion bound reached; inventory remains partial')
  before=collapsed.first.get_attribute('class')
  identity=next(c for c in before.split() if c.startswith('id-'))
  li=page.locator(TREE+' li.'+identity)
  li.locator(':scope > .doc-tree-node-content-wrapper > .doc-tree-iconEle').click()
  deadline=time.monotonic()+timeout
  while time.monotonic()<deadline:
   # Re-query current DOM; non-anchor interaction only with observed CodeHUB control.
   if 'doc-tree-treenode-switcher-open' in (li.get_attribute('class') or '') and li.locator(':scope > ul[role="group"] li').count()>0:break
   page.wait_for_timeout(300)
  else:raise RuntimeError('Navigation control did not expose children: '+str(before))
 raise AssertionError('unreachable')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--url',action='append',required=True,help='Observed full UUID route; repeat for bounded sample')
 p.add_argument('--out',required=True);p.add_argument('--snapshot-id',required=True);p.add_argument('--source-version',required=True,help='Explicit binding; may be unknown legal version + snapshot ID')
 p.add_argument('--inventory',action='store_true',help='Expand observed non-anchor tree controls; never marks full corpus qualified')
 p.add_argument('--max-expansions',type=int,default=300);p.add_argument('--max-routes',type=int,default=6);p.add_argument('--timeout',type=int,default=40);p.add_argument('--headed',action='store_true')
 p.add_argument('--operator-window',type=int,default=0,help='Headed operator time in seconds to dismiss informational notices using ordinary UI; maximum 60')
 a=p.parse_args()
 if a.operator_window<0 or a.operator_window>60 or (a.operator_window and not a.headed):raise ValueError('Operator window requires --headed and 0..60 seconds')
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 if len(a.url)>a.max_routes:raise ValueError('Bounded route limit exceeded')
 if any(not valid_route(u) for u in a.url):raise ValueError('Only observed Cupertino UUID/hash routes are accepted')
 config={'urls':a.url,'snapshot_id':a.snapshot_id,'source_version':a.source_version,'inventory':a.inventory,'max_expansions':a.max_expansions,'timeout':a.timeout,'headed':a.headed,'operator_window':a.operator_window,'acquisition_version':VERSION,'code_sha256':digest(Path(__file__).read_bytes())}
 cp=out/'acquisition-checkpoint.json';state={'binding':config,'artifacts':[],'failures':[]}
 if cp.exists():
  state=json.loads(cp.read_text())
  if state['binding']!=config:raise ValueError('Acquisition checkpoint binding mismatch')
 from playwright.sync_api import sync_playwright
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=not a.headed)
  try:
   for url in a.url:
    done=next((x for x in state['artifacts'] if x['url']==url),None)
    if done:
     if digest((out/done['path']).read_bytes())!=done['sha256']:raise ValueError('Cached artifact corrupted')
     continue
    # Fresh page/context prevents a preceding route's legal content from satisfying readiness.
    context=browser.new_context();page=context.new_page();responses=[]
    page.on('response',lambda r:responses.append({'url':r.url,'status':r.status,'resource_type':r.request.resource_type}))
    try:
     response=page.goto(url,wait_until='domcontentloaded',timeout=a.timeout*1000)
     if response and response.status in {401,403,429,503}:raise RuntimeError('Publisher returned HTTP '+str(response.status)+'; operator review required')
     if a.operator_window:page.wait_for_timeout(a.operator_window*1000)
     html=wait_ready(page,url,a.timeout);raw=html.encode();name='raw/'+digest(url)+'.html';(out/'raw').mkdir(exist_ok=True);(out/name).write_bytes(raw)
     item={'path':name,'sha256':digest(raw),'url':url,'retrieved_at':datetime.now(timezone.utc).isoformat(),'response_metadata_path':'raw/'+digest(url)+'-responses.json'}
     save(out/item['response_metadata_path'],responses)
     if a.inventory:
      rows,states=expand_tree(page,out,a.max_expansions,a.timeout);ib=(out/'navigation-current.json').read_bytes();state['inventory']={'path':'navigation-current.json','sha256':digest(ib)}
     state['artifacts'].append(item);save(cp,state)
    except Exception as exc:
     fail={'url':url,'error':str(exc),'retrieved_at':datetime.now(timezone.utc).isoformat()};state['failures'].append(fail)
     name='raw/failed-'+digest(url)+'.html';(out/'raw').mkdir(exist_ok=True);(out/name).write_text(page.content(),encoding='utf8');fail['raw_path']=name;fail['raw_sha256']=digest((out/name).read_bytes());save(out/'last-failure-responses.json',responses);save(cp,state)
     raise
    finally:context.close()
   manifest={'snapshot_id':a.snapshot_id,'source_version':a.source_version,'currency_raw':None,'artifacts':state['artifacts'],'inventory':state.get('inventory'),'full_inventory_qualified':False,'full_collection_validated':False}
   save(out/'snapshot-manifest.json',manifest);save(cp,state)
  finally:browser.close()
 print(json.dumps({'status':'bounded_acquisition_only','manifest':str(out/'snapshot-manifest.json'),'routes':len(state['artifacts'])},indent=2))
if __name__=='__main__':main()
