"""Complete public HTML traversal from actual native Flagstaff source TOC, ordinary Chrome."""
import argparse,base64,json,re,sys
from pathlib import Path
from urllib.parse import urljoin,urlsplit,parse_qs
from playwright.sync_api import sync_playwright
from source_common import *
from browser_safety import guard_html
from flagstaff_root import root_inventory,ROOT_TOC_URL
URL='https://www.codepublishing.com/AZ/Flagstaff/';NT=URL+'html/FlagstaffNT.html';CURRENCY_URL=URL+'html/disclaimer.html'
FILES=['flagstaff_html.py','flagstaff_inventory.py','flagstaff_root.py','source_common.py','shared_transport.py','browser_safety.py']
def roots_and_readers(source):
 source=Path(source);frames=load(source/'selected-frames.json');f=next(f for f in frames if 'FlagstaffTOC.pl' in f['url']);raw=(source/f['path']).read_bytes()
 if sha(raw)!=f['sha256']:raise ValueError('Corrupt retained expanded TOC')
 meta=load(source/'receipt.json')
 if meta.get('blocked'):raise ValueError('Retained source refusal; no migration/retry')
 s=BeautifulSoup(raw,'html.parser');root=s.select_one('#divmuni');roots=[]
 for p in root.find_all('p',recursive=False):
  box=p.select_one('input[name="code"]');a=p.find('a',href=True)
  if box and a:roots.append({'source_url':urljoin(f['url'],a['href']),'value':box['value'],'label':clean(a.get_text(' ',strip=True)),'source_id':a.get('id')})
 bodies=load(source/'network-bodies.json');readers=[]
 for r in roots:
  candidates=[a for a in bodies if '/reader.pl?' in a['url'] and parse_qs(urlsplit(a['url']).query).get('cite')==[r['source_id']] and a.get('status')==200 and a.get('path')]
  if len(candidates)!=1:raise ValueError('Exact observed native TOC reader absent/nonunique '+r['source_id'])
  a=candidates[0]
  if sha((source/a['path']).read_bytes())!=a['sha256']:raise ValueError('Corrupt retained native TOC reader')
  readers.append({'root':r,'url':a['url'],'retained_sha256':a['sha256']})
 if len(roots)<10:raise ValueError('Truncated primary roots')
 return readers,{'path':str(source.resolve()),'receipt_sha256':sha((source/'receipt.json').read_bytes()),'selected_frame_sha256':sha(raw),'kind':'explicit_retained_source_inventory_migration; all readers freshly acquired before traversal'}
def inventory(reader_records):
 edges=[]
 for index,record in enumerate(reader_records):
  r=record['root'];edges.append(dict(r,edge_id=sha((str(index)+'::root').encode()),root_index=index,source_order=len(edges)))
  bs=BeautifulSoup(record['raw'],'html.parser')
  for p in bs.select('p'):
   box=p.select_one('input[name="code"]');a=p.find('a',href=True)
   if not box or not a:continue
   u=urljoin(URL+'cgi/FlagstaffTOC.pl',a['href'])
   if not u.startswith(URL+'html/') or not urlsplit(u).path.lower().endswith('.html'):raise ValueError('Unprofiled primary TOC document type '+u)
   edges.append({'edge_id':sha((str(index)+'::edge-'+str(len(edges))).encode()),'root_index':index,'source_order':len(edges),'source_url':u,'value':box['value'],'label':clean(a.get_text(' ',strip=True)),'source_id':a.get('id'),'ancestor_classes':box.get('class',[])})
 if len(edges)<=len(reader_records):raise ValueError('Expanded primary inventory empty')
 return edges
FETCH="""async u=>{let r=await fetch(u,{credentials:'same-origin',redirect:'follow'});let h=Object.fromEntries(r.headers.entries());if((h['content-type']||'').toLowerCase().startsWith('image/')){if(r.body)await r.body.cancel();return {status:r.status,url:r.url,headers:h,image_omitted:true};}let a=new Uint8Array(await r.arrayBuffer()),s='';for(let i=0;i<a.length;i+=16384)s+=String.fromCharCode(...a.subarray(i,i+16384));return {status:r.status,url:r.url,headers:h,data:btoa(s)};}"""
def collect(out,inventory_source=None,resume=False,import_inventory_capture=None):
 out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
 if resume:
  state=load(out/'checkpoint.json')
  if state['errors'] or state.get('blocked'):raise ValueError('Retained failure/access stop: no automatic retry')
  for n,h in state['code_fingerprint'].items():
   if sha((Path(__file__).parent/n).read_bytes())!=h:raise ValueError('Resume acquisition version mismatch')
  for a in state['artifacts']:
   if sha((out/a['path']).read_bytes())!=a['sha256']:raise ValueError('Corrupt retained source')
  readers=state['observed_readers']
  if state.get('closing_inventory_equal') and state.get('closing_currency_equal') and state.get('closing_roots_equal'):return state
 else:
  if any(out.iterdir()):raise ValueError('Fresh output required')
  if inventory_source is None:
   from flagstaff_inventory import run
   result=run(out/'inventory-origin')
   if result.get('error') or result.get('blocked'):raise ValueError('Native inventory acquisition failed')
   inventory_source=out/'inventory-origin'
  readers,provenance=roots_and_readers(inventory_source);state={'schema':'flagstaff-full-html-1','source_url':URL,'started_at':stamp(),'code_fingerprint':source_snapshot(out,FILES),'observed_readers':readers,'inventory_provenance':provenance,'artifacts':[],'errors':[],'blocked':[],'images_downloaded':False,'image_requests_blocked':[],'complete':False};save(out/'checkpoint.json',state)
 if import_inventory_capture:
  original=Path(import_inventory_capture).resolve();old=load(original/'checkpoint.json')
  if resume or state['artifacts'] or old.get('blocked') or any(e.get('message')!='Current publication edition marker absent' for e in old.get('errors',[])):raise ValueError('Only explicit parser-only inventory import accepted; source failures never migrated')
  if old.get('source_url')!=URL or old.get('observed_readers')!=readers:raise ValueError('Imported native inventory source identity differs')
  for r in readers:
   aa=[a for a in old['artifacts'] if a['role']=='toc-start' and a['source_url']==r['url'] and a['status']==200]
   if len(aa)!=1:raise ValueError('Imported source inventory missing/duplicate')
   a=dict(aa[0]);raw=(original/a['path']).read_bytes()
   if sha(raw)!=a['sha256']:raise ValueError('Imported native inventory corrupt')
   original_path=a['path'];a['path']=f'raw/{len(state["artifacts"]):04d}-toc-start.bin';a['import_provenance']={'source_checkpoint_sha256':sha((original/'checkpoint.json').read_bytes()),'original_path':original_path,'original_code_fingerprint':old['code_fingerprint'],'original_source_directory':str(original)};transport.atomic(out/a['path'],raw);state['artifacts'].append(a)
  save(out/'checkpoint.json',state)
 gate=transport.ROOT/sha(b'www.codepublishing.com')[:20]/'state.json'
 if gate.exists() and load(gate).get('stop'):raise ValueError('Persisted publisher host stop; browser not started')
 with sync_playwright() as pw:
  browser=pw.chromium.launch(channel='chrome',headless=False);state['browser']=browser.version
  try:
   context=browser.new_context()
   def route(r):
    if r.request.resource_type in ['image','font','media']:
     state['image_requests_blocked'].append({'url':redact(r.request.url),'resource_type':r.request.resource_type});return r.abort()
    if state['blocked']:return r.abort()
    try:
     forbid(r.request.url)
     if r.request.resource_type in ['document','xhr','fetch']:transport.reserve(r.request.url)
    except Exception as e:state['blocked'].append({'url':r.request.url,'error':str(e)});return r.abort()
    r.continue_()
   context.route('**/*',route)
   def response(r):
    if r.status in [403,429] or r.headers.get('cf-mitigated','').lower()=='challenge' or r.headers.get('retry-after'):
     state['blocked'].append({'url':r.url,'status':r.status,'headers':r.headers,'at':stamp()});transport.stop(URL,r.status,r.headers,'Actual ordinary-browser source refusal at '+r.url)
   context.on('response',response);page=context.new_page()
   def fetch(role,url):
    forbid(url);started=stamp();r=page.evaluate(FETCH,url);raw=base64.b64decode(r.pop('data',''));entry={'role':role,'source_url':url,'final_url':r['url'],'status':r['status'],'headers':r['headers'],'started_at':started,'finished_at':stamp(),'sha256':sha(raw),'bytes':len(raw),'path':f'raw/{len(state["artifacts"]):04d}-{role}.bin'};transport.atomic(out/entry['path'],raw);state['artifacts'].append(entry);save(out/'checkpoint.json',state)
    guard_html(raw,url,r['status'],r['headers'])
    if r.get('image_omitted'):raise ValueError('Source returned image; image body not downloaded')
    if r['status']!=200 or state['blocked']:raise RuntimeError('Source refusal/failure retained; no retry')
    if not raw or b'<title>Just a moment' in raw[:20000]:raise ValueError('Empty/unqualified/challenge source response')
    if r['url']!=url:raise ValueError('Unexpected source URL redirect identity')
    return raw
   try:
    bootstrap=page.goto(NT,wait_until='domcontentloaded',timeout=180000)
    guard_html(bootstrap.body(),NT,bootstrap.status,bootstrap.headers)
    if state['blocked']:raise RuntimeError('Publisher source access stop')
    expected_roots=[r['root'] for r in readers]
    retained_roots=[a for a in state['artifacts'] if a['role']=='root-toc-start']
    if len(retained_roots)>1:raise ValueError('Duplicate opening native root inventory')
    root_raw=(out/retained_roots[0]['path']).read_bytes() if retained_roots else fetch('root-toc-start',ROOT_TOC_URL)
    if root_inventory(root_raw)!=expected_roots:raise ValueError('Current top-level publication roots differ from source-observed scope')
    opening=[]
    for r in readers:
     retained=[a for a in state['artifacts'] if a['role']=='toc-start' and a['source_url']==r['url']]
     if len(retained)>1:raise ValueError('Duplicate retained opening inventory')
     body=(out/retained[0]['path']).read_bytes() if retained else fetch('toc-start',r['url'])
     opening.append(dict(r,raw=decode(body)[0]))
    edges=inventory(opening)
    if state.get('inventory') and state['inventory']!=edges:raise ValueError('Resume source inventory drift')
    state['inventory']=edges;save(out/'checkpoint.json',state)
    retained_currency=[a for a in state['artifacts'] if a['role']=='currency-start']
    if len(retained_currency)>1:raise ValueError('Duplicate opening currency source receipt')
    if retained_currency:
     initial_currency=currency((out/retained_currency[0]['path']).read_bytes())
     if state.get('opening_currency') and state['opening_currency']!=initial_currency:raise ValueError('Opening currency marker differs from retained source')
    else:
     if state.get('opening_currency'):raise ValueError('Opening currency marker has no retained source receipt')
     initial_currency=currency(fetch('currency-start',CURRENCY_URL))
    state['opening_currency']=initial_currency;save(out/'checkpoint.json',state)
    if resume:
     if root_inventory(fetch('root-resume-validation',ROOT_TOC_URL))!=expected_roots:raise ValueError('Resumed primary root inventory drift')
     validation=[];role='toc-resume-validation-'+str(len(state['artifacts']))
     for r in readers:validation.append(dict(r,raw=decode(fetch(role,r['url']))[0]))
     if inventory(validation)!=edges:raise ValueError('Resumed publication inventory drift')
     observed=currency(fetch('currency-resume-validation',CURRENCY_URL))
     if observed!=state['opening_currency']:raise ValueError('Resumed source edition drift')
    docs=list(dict.fromkeys(key(e['source_url']) for e in edges));state['source_documents']=docs;save(out/'checkpoint.json',state)
    acquired={a['source_url'] for a in state['artifacts'] if a['role']=='content' and a['status']==200}
    for u in docs:
     if u in acquired:continue
     fetch('content',u);acquired.add(u);print(json.dumps({'acquired':len(acquired),'documents':len(docs),'url':u}),flush=True)
    closing=[]
    prior=[a for a in state['artifacts'] if a['role'] in ['toc-end','currency-end','root-toc-end']]
    for a in prior:a['role']='abandoned-partial-'+a['role'];a['disposition']='Retained interrupted closing, replaced by complete fresh closing validation'
    save(out/'checkpoint.json',state)
    for r in readers:closing.append(dict(r,raw=decode(fetch('toc-end',r['url']))[0]))
    state['closing_inventory_equal']=inventory(closing)==edges
    state['closing_roots_equal']=root_inventory(fetch('root-toc-end',ROOT_TOC_URL))==expected_roots
    state['closing_currency']=currency(fetch('currency-end',CURRENCY_URL));state['closing_currency_equal']=state['closing_currency']==state['opening_currency']
   except Exception as e:state['errors'].append({'type':type(e).__name__,'message':str(e),'at':stamp()})
   finally:state['finished_at']=stamp();state['content_acquired']=len({a['source_url'] for a in state['artifacts'] if a['role']=='content' and a['status']==200});save(out/'checkpoint.json',state);context.close()
  finally:browser.close()
 return state

def currency(raw):
 text=BeautifulSoup(decode(raw)[0],'html.parser').get_text(' ',strip=True);m=re.search(r'The Flagstaff City Charter and City Code are current through[^.]*\.',text,re.I)
 if not m:raise ValueError('Current publication edition marker absent')
 return clean(m.group(0))
def redact(s):return '[IMAGE]' if 'data:image/' in s.lower() else s
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--inventory-source');p.add_argument('--resume',action='store_true');p.add_argument('--import-inventory-capture');a=p.parse_args();r=collect(a.out,a.inventory_source,a.resume,a.import_inventory_capture);print(json.dumps({'acquired':r.get('content_acquired',0),'documents':len(r.get('source_documents',[])),'errors':r['errors'],'blocked':r['blocked'],'acquisition_only':True},indent=2));sys.exit(3 if r['blocked'] else 2 if r['errors'] else 0)
