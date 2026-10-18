"""Explicit final consistency phase for a retained completed pre-root-guard source run."""
import argparse,base64,copy,json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from source_common import *
from browser_safety import guard_html
from flagstaff_root import root_inventory,ROOT_TOC_URL,URL
from flagstaff_html import FETCH,NT,CURRENCY_URL,inventory,currency,redact
FILES=['flagstaff_root_guard.py','flagstaff_root.py','flagstaff_html.py','flagstaff_inventory.py','source_common.py','shared_transport.py','browser_safety.py']
def run(source,opening_source):
 src=Path(source).resolve();original=Path(opening_source).resolve();before=(src/'checkpoint.json').read_bytes();s=load(src/'checkpoint.json');folder=src/'root-consistency'
 if folder.exists():raise ValueError('Root consistency output exists; no automatic repeated closing request')
 if s['source_url']!=URL or s['errors'] or s['blocked']:raise ValueError('Source identity/failure blocks finalization')
 for a in s['artifacts']:
  if sha((src/a['path']).read_bytes())!=a['sha256']:raise ValueError('Corrupt source artifact')
 expected=[r['root'] for r in s['observed_readers']];docs={key(e['source_url']) for e in s['inventory']};acquired={a['source_url'] for a in s['artifacts'] if a['role']=='content' and a['status']==200}
 if acquired!=docs or not s.get('finished_at'):raise ValueError('Full body acquisition must finish before final root closing')
 for role in ['toc-start','toc-end']:
  records=[]
  for r in s['observed_readers']:
   aa=[a for a in s['artifacts'] if a['role']==role and a['source_url']==r['url']]
   if len(aa)!=1:raise ValueError('Full opening/closing reader inventory required')
   records.append(dict(r,raw=decode((src/aa[0]['path']).read_bytes())[0]))
  if inventory(records)!=s['inventory']:raise ValueError('Retained opening/closing inventory differs')
 native=[a for a in load(original/'network-bodies.json') if a['url']==ROOT_TOC_URL and a.get('status')==200 and a.get('path')]
 if len(native)!=1:raise ValueError('Original native opening root response absent/nonunique')
 opening=native[0];opening_raw=(original/opening['path']).read_bytes()
 if sha(opening_raw)!=opening['sha256'] or root_inventory(opening_raw)!=expected:raise ValueError('Original native opening roots corrupt/mismatched')
 gate=transport.ROOT/sha(b'www.codepublishing.com')[:20]/'state.json'
 if gate.is_file() and load(gate).get('stop'):raise ValueError('Existing publisher stop; no finalization browser started')
 folder.mkdir();proof={'schema':'flagstaff-root-finalization-1','source_checkpoint_before_sha256':sha(before),'source_url':URL,'started_at':stamp(),'code_fingerprint':source_snapshot(folder,FILES),'complete':False,'errors':[],'blocked':[],'image_requests_blocked':[],'artifacts':[],'scope':'Retained hash-verified native root opening plus fresh closing root/currency, after complete source body/reader acquisition; no body refetch or image acquisition'}
 transport.atomic(folder/'opening-root.bin',opening_raw);proof['opening_origin']={**opening,'original_directory':str(original),'original_receipt_sha256':sha((original/'receipt.json').read_bytes())}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(channel='chrome',headless=False)
  try:
   context=browser.new_context()
   def route(r):
    if r.request.resource_type in ['image','font','media']:proof['image_requests_blocked'].append({'url':redact(r.request.url),'source_reference_sha256':sha(r.request.url.encode()),'resource_type':r.request.resource_type});return r.abort()
    if proof['blocked']:return r.abort()
    try:
     forbid(r.request.url)
     if r.request.resource_type in ['document','xhr','fetch']:transport.reserve(r.request.url)
    except Exception as e:proof['blocked'].append({'url':r.request.url,'message':str(e)});return r.abort()
    r.continue_()
   context.route('**/*',route)
   def response(r):
    if r.status in [403,429] or r.headers.get('cf-mitigated','').lower()=='challenge' or r.headers.get('retry-after'):
     proof['blocked'].append({'url':r.url,'status':r.status,'headers':r.headers});transport.stop(URL,r.status,r.headers,'Actual root-finalization refusal at '+r.url)
   context.on('response',response);page=context.new_page()
   def fetch(role,url):
    started=stamp();r=page.evaluate(FETCH,url);raw=base64.b64decode(r.pop('data',''));entry={'role':role,'source_url':url,'final_url':r['url'],'status':r['status'],'headers':r['headers'],'started_at':started,'finished_at':stamp(),'sha256':sha(raw),'bytes':len(raw),'path':role+'.bin'};transport.atomic(folder/entry['path'],raw);proof['artifacts'].append(entry);save(folder/'receipt.json',proof)
    guard_html(raw,url,r['status'],r['headers'])
    if proof['blocked'] or r['status']!=200 or r.get('image_omitted') or r['url']!=url or not raw:raise ValueError('Final source request unavailable/unqualified; no retry')
    return raw
   try:
    r=page.goto(NT,wait_until='domcontentloaded',timeout=180000)
    guard_html(r.body(),NT,r.status,r.headers)
    if proof['blocked']:raise RuntimeError('Actual source access refusal')
    final_root=fetch('root-toc-end',ROOT_TOC_URL);final_currency=fetch('currency-root-guard-end',CURRENCY_URL);proof['roots_equal']=root_inventory(final_root)==expected;proof['currency_equal']=currency(final_currency)==s['opening_currency'];proof['closing_currency']=currency(final_currency);proof['complete']=proof['roots_equal'] and proof['currency_equal']
   except Exception as e:proof['errors'].append({'type':type(e).__name__,'message':str(e)})
   finally:proof['finished_at']=stamp();save(folder/'receipt.json',proof);context.close()
  finally:browser.close()
 if proof['complete'] and not proof['blocked'] and not proof['errors']:
  if (src/'checkpoint.json').read_bytes()!=before:raise ValueError('Source checkpoint changed during finalization; refusing apply')
  transport.atomic(src/'checkpoint-before-root-finalization.json',before)
  entry={'role':'root-toc-start','source_url':ROOT_TOC_URL,'final_url':ROOT_TOC_URL,'status':200,'headers':opening['headers'],'started_at':opening.get('captured_at'),'finished_at':opening.get('captured_at'),'sha256':sha(opening_raw),'bytes':len(opening_raw),'path':'root-consistency/opening-root.bin','explicit_retained_source_import':proof['opening_origin']};s['artifacts'].append(entry)
  for a in proof['artifacts']:s['artifacts'].append(dict(a,path='root-consistency/'+a['path']))
  s['closing_roots_equal']=True;s['root_finalization']={'receipt_path':'root-consistency/receipt.json','receipt_sha256':sha((folder/'receipt.json').read_bytes()),'source_checkpoint_before_sha256':sha(before),'original_acquisition_revision_retained':True,'method':'explicit retained-source plus fresh root/currency closing phase'};save(src/'checkpoint.json',s)
 return proof
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--opening-source',required=True);a=p.parse_args();r=run(a.source,a.opening_source);print(json.dumps(r,indent=2));sys.exit(0 if r['complete'] and not r['blocked'] and not r['errors'] else 2)
