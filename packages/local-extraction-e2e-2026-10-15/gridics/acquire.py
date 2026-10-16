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

def readiness_state(html,url,actual_url,expected_heading=None):
 if actual_url!=url:return None
 try:
  nodes,records,dispositions=parse_html(html,url);target=next(n for n in nodes if n['path']==urlsplit(url).fragment)
  if expected_heading and target['display_heading']!=expected_heading:return None
  if any(r['row']['source_url']==url or r['row']['source_url'].startswith(url+'/') for r in records) or 'reserved' in target['display_heading'].lower():return nodes,records
 except (ValueError,StopIteration):pass
 return None

def route_ready(html,url,actual_url,expected_heading=None):
 return readiness_state(html,url,actual_url,expected_heading) is not None

def wait_ready(page,url,timeout,expected_heading=None):
 deadline=time.monotonic()+timeout;prev=None;stable=0
 while time.monotonic()<deadline:
  html=page.content();state=readiness_state(html,url,page.url,expected_heading)
  if state:
   nodes,records=state
   # One source parse per observation. Only legal identity/body fingerprints matter.
   key=digest(json.dumps([(n['path'],n['display_heading'],n['semantic_body_sha256']) for n in nodes],sort_keys=True))
   stable=stable+1 if key==prev else 1;prev=key
   if stable>=3:return html
  page.wait_for_timeout(700)
 raise RuntimeError('Requested route content/UUID did not stabilize; no cached success is recorded')

def dismiss_notices(page,out):
 """Only the observed informational disclaimer and optional product tour."""
 accept=page.get_by_role('button',name='Accept',exact=True)
 if accept.count() and accept.is_visible():
  notice=page.get_by_role('heading',name='Legal Disclaimer',exact=True)
  if not notice.count():raise RuntimeError('Unrecognized Accept interface; operator review required')
  text=page.locator('#popup-container').inner_text(timeout=5000)
  if 'provided for informational purposes only' not in text or any(t in text.lower() for t in ['by clicking','you agree','terms of service']):raise RuntimeError('Notice requires operator review')
  save(out/'informational-notice.json',{'text':text,'action':'dismiss observed informational notice'})
  accept.click(timeout=5000)
 # Onboarding appears asynchronously after informational notice dismissal.
 for _ in range(5):
  skip=page.get_by_role('button',name='Skip',exact=True)
  if skip.count() and skip.is_visible():skip.click(timeout=5000);break
  page.wait_for_timeout(200)

def expand_tree(page,out,max_expansions,timeout):
 page.locator(TREE).wait_for(state='attached',timeout=timeout*1000)
 states=[];events=[]
 for ix in range(max_expansions+1):
  collapsed=page.locator(CLOSED);remaining=collapsed.count()
  if ix%25==0 or remaining==0 or ix==max_expansions:
   html=page.locator(TREE).evaluate('(el)=>el.outerHTML');rows=inventory_html(html)
   actual=page.locator('div.section[data-path]').evaluate_all('(nodes)=>nodes.map(n=>({path:n.getAttribute("data-path"),id:n.id}))');paths={n['path']:n['id'] for n in actual}
   for row in rows:
    if paths.get(row['path'])=='section-'+row['node_id']:row['source_url']=row['candidate_source_url'];row['route_qualification']='matching_rendered_publisher_data_path'
   save(out/'navigation-current.json',rows)
   raw=html.encode();name='raw/navigation-'+digest(raw)+'.html';p=out/name;p.parent.mkdir(exist_ok=True);p.write_bytes(raw)
   states.append({'path':name,'sha256':digest(raw),'node_count':len(rows),'closed_controls':remaining,'expansions':ix})
   save(out/'navigation-expansion-log.json',events)
   print(json.dumps({'phase':'navigation','expansions':ix,'nodes':len(rows),'closed':remaining}),flush=True)
  if remaining==0:
   save(out/'navigation-evidence.json',{'states':states,'expansion_count':len(events),'all_observed_branches_expanded':all(n['children_enumerated'] for n in rows),'full_inventory_qualified':False,'reason':'All observed controls expanded; independent publisher total/virtualization/publication scope still requires reconciliation.'})
   return rows,states
  if ix==max_expansions:raise RuntimeError('Navigation expansion bound reached; inventory remains partial')
  before=collapsed.first.get_attribute('class');identity=next(c for c in before.split() if c.startswith('id-'));li=page.locator(TREE+' li.'+identity)
  label=li.locator(':scope > .doc-tree-node-content-wrapper > .doc-tree-title').inner_text()
  li.locator(':scope > .doc-tree-node-content-wrapper > .doc-tree-iconEle').click(timeout=timeout*1000)
  deadline=time.monotonic()+timeout
  while time.monotonic()<deadline:
   if 'doc-tree-treenode-switcher-open' in (li.get_attribute('class') or '') and li.locator(':scope > ul[role="group"] li').count()>0:break
   page.wait_for_timeout(300)
  else:raise RuntimeError('Navigation control did not expose children: '+str(before))
  events.append({'node_id':identity[3:],'publisher_class_identity':identity[3:],'label':label,'children':li.locator(':scope > ul[role="group"] li').count(),'at':datetime.now(timezone.utc).isoformat()})
 raise AssertionError('unreachable')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--url',action='append',required=True,help='Observed full UUID route; repeat for bounded sample')
 p.add_argument('--out',required=True);p.add_argument('--snapshot-id',required=True);p.add_argument('--source-version',required=True,help='Explicit binding; may be unknown legal version + snapshot ID')
 p.add_argument('--inventory',action='store_true',help='Expand observed non-anchor tree controls; never marks full corpus qualified')
 p.add_argument('--max-expansions',type=int,default=300);p.add_argument('--max-routes',type=int,default=6);p.add_argument('--timeout',type=int,default=40);p.add_argument('--headed',action='store_true')
 p.add_argument('--dismiss-notices',action='store_true',help='Dismiss only observed informational disclaimer and optional onboarding tour; never authentication/agreements')
 p.add_argument('--stop-after',type=int,help='Cleanly interrupt after N newly acquired routes; resume with identical bound config and omit this progress limit')
 p.add_argument('--verify-end',action='store_true',help='Reload each requested route and require equal legal UUID/body fingerprints before checkpointing')
 p.add_argument('--operator-window',type=int,default=0,help='Headed operator time in seconds to dismiss informational notices using ordinary UI; maximum 60')
 a=p.parse_args()
 if a.operator_window<0 or a.operator_window>60 or (a.operator_window and not a.headed):raise ValueError('Operator window requires --headed and 0..60 seconds')
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 if len(a.url)>a.max_routes:raise ValueError('Bounded route limit exceeded')
 if any(not valid_route(u) for u in a.url):raise ValueError('Only observed Cupertino UUID/hash routes are accepted')
 config={'urls':a.url,'snapshot_id':a.snapshot_id,'source_version':a.source_version,'inventory':a.inventory,'max_expansions':a.max_expansions,'timeout':a.timeout,'headed':a.headed,'operator_window':a.operator_window,'verify_end':a.verify_end,'dismiss_notices':a.dismiss_notices,'acquisition_version':VERSION,'code_sha256':digest(Path(__file__).read_bytes())}
 cp=out/'acquisition-checkpoint.json';state={'binding':config,'artifacts':[],'failures':[]}
 if cp.exists():
  state=json.loads(cp.read_text())
  if state['binding']!=config:raise ValueError('Acquisition checkpoint binding mismatch')
 from playwright.sync_api import sync_playwright
 print(json.dumps({'phase':'launch','at':datetime.now(timezone.utc).isoformat()}),flush=True)
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=not a.headed,timeout=a.timeout*1000)
  print(json.dumps({'phase':'launched','browser_version':browser.version}),flush=True)
  new_count=0
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
     print(json.dumps({'phase':'goto','url':url}),flush=True)
     response=page.goto(url,wait_until='domcontentloaded',timeout=a.timeout*1000)
     if response and response.status in {401,403,429,503}:raise RuntimeError('Publisher returned HTTP '+str(response.status)+'; operator review required')
     print(json.dumps({'phase':'document_loaded','url':page.url,'status':response.status if response else None}),flush=True)
     if a.operator_window:page.wait_for_timeout(a.operator_window*1000)
     html=wait_ready(page,url,a.timeout);raw=html.encode();name='raw/'+digest(url)+'.html';(out/'raw').mkdir(exist_ok=True);(out/name).write_bytes(raw)
     item={'path':name,'sha256':digest(raw),'url':url,'retrieved_at':datetime.now(timezone.utc).isoformat(),'response_metadata_path':'raw/'+digest(url)+'-responses.json'}
     if a.verify_end:
      before_nodes,_,_=parse_html(html,url);before=[(n['path'],n['display_heading'],n['semantic_body_sha256']) for n in before_nodes]
      end_response=page.reload(wait_until='domcontentloaded',timeout=a.timeout*1000)
      if end_response and end_response.status in {401,403,429,503}:raise RuntimeError('Publisher reload refused HTTP '+str(end_response.status))
      end_html=wait_ready(page,url,a.timeout);end_nodes,_,_=parse_html(end_html,url);after=[(n['path'],n['display_heading'],n['semantic_body_sha256']) for n in end_nodes]
      end_name='raw/'+digest(url)+'-end.html';(out/end_name).write_text(end_html,encoding='utf8')
      item['consistency']={'start_semantic_sha256':digest(json.dumps(before,sort_keys=True)),'end_semantic_sha256':digest(json.dumps(after,sort_keys=True)),'equal':before==after,'end_raw_path':end_name,'end_raw_sha256':digest(end_html),'checked_at':datetime.now(timezone.utc).isoformat()}
      if before!=after:raise RuntimeError('Start/end legal snapshot drift; no success checkpoint')
     save(out/item['response_metadata_path'],responses)
     if a.inventory and not state.get('inventory'):
      if a.dismiss_notices:dismiss_notices(page,out)
      rows,states=expand_tree(page,out,a.max_expansions,a.timeout);ib=(out/'navigation-current.json').read_bytes();state['inventory']={'path':'navigation-current.json','sha256':digest(ib)}
     state['artifacts'].append(item);save(cp,state);new_count+=1
     print(json.dumps({'phase':'checkpointed','url':url,'sha256':item['sha256']}),flush=True)
     if a.stop_after and new_count>=a.stop_after:
      save(out/'snapshot-manifest.json',{'snapshot_id':a.snapshot_id,'source_version':a.source_version,'currency_raw':None,'artifacts':state['artifacts'],'inventory':state.get('inventory'),'full_inventory_qualified':False,'full_collection_validated':False,'acquisition_status':'interrupted_by_requested_progress_limit'})
      print(json.dumps({'status':'interrupted','new_routes':new_count}),flush=True);return
    except Exception as exc:
     fail={'url':url,'error':str(exc),'retrieved_at':datetime.now(timezone.utc).isoformat()};state['failures'].append(fail)
     name='raw/failed-'+digest(url)+'.html';(out/'raw').mkdir(exist_ok=True);(out/name).write_text(page.content(),encoding='utf8');fail['raw_path']=name;fail['raw_sha256']=digest((out/name).read_bytes());save(out/'last-failure-responses.json',responses);save(cp,state)
     raise
    finally:context.close()
   manifest={'snapshot_id':a.snapshot_id,'source_version':a.source_version,'currency_raw':None,'artifacts':state['artifacts'],'inventory':state.get('inventory'),'full_inventory_qualified':False,'full_collection_validated':False,'acquisition_status':'completed_bounded_routes'}
   save(out/'snapshot-manifest.json',manifest);save(cp,state)
  finally:browser.close()
 print(json.dumps({'status':'bounded_acquisition_only','manifest':str(out/'snapshot-manifest.json'),'routes':len(state['artifacts'])},indent=2))
if __name__=='__main__':main()
