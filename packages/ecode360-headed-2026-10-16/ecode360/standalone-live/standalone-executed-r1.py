#!/usr/bin/env python3
"""Bounded public eCode360 acquisition without Codex: ordinary isolated Playwright.
No stealth, challenge solving, cookies/profile import, proxy or TLS overrides.
"""
import argparse,hashlib,importlib.metadata,json,platform,sys,time
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import ecode360 as e
from ingest_cua import ingest
ROOT=Path(__file__).resolve().parent

def state(page,selector='#codeContent'):
 return page.evaluate('''({selector})=>{const el=document.querySelector(selector);return {url:location.href,title:document.title,html:el?el.outerHTML:null,identity:{customer_id:document.body?.getAttribute('data-cust-id'),code_id:document.body?.getAttribute('data-code-id'),currency_raw:document.body?.getAttribute('data-code-date')},heading_node_id:document.querySelector('#pageTitle .titleTitle[data-guid]')?.getAttribute('data-guid'),section_bodies:Array.from(document.querySelectorAll('.section_content')).map(x=>x.id),toc:Array.from(document.querySelectorAll('#toc .contentTitle[data-guid]')).map(t=>({node_id:t.getAttribute('data-guid'),kind:t.getAttribute('data-code-content-type'),number:t.querySelector('.titleNumber')?.textContent||'',heading:t.querySelector('.titleTitle')?.textContent||t.textContent,href:t.querySelector('a.titleLink')?.getAttribute('href')})),challenge:!!document.querySelector('#challenge-form,#cf-error-details')||/just a moment|attention required|access denied/i.test(document.title)};}''',{'selector':selector})

def acquire(browser,job,out,*,headed=False,operator_assisted=False,channel='chrome'):
 out=Path(out)
 if out.exists() and any(out.iterdir()):raise e.ValidationError('use a fresh empty output directory; prior evidence is immutable')
 out.mkdir(parents=True,exist_ok=True);url=e.fetch_url(job['discovery_url']);requested=url.rsplit('/',1)[-1]
 r={'schema_version':1,'job':{'slug':job['slug'],'id':'source','url':url,'kind':'legal','expected_node_id':requested},'started_at':e.now(),'transport':'standalone Python Playwright ordinary browser','headed':headed,'operator_assisted':operator_assisted,'runtime':{'python':sys.version,'platform':platform.platform(),'playwright':importlib.metadata.version('playwright'),'browser':browser.version,'channel':channel},'acquisition_script_sha256':e.digest(Path(__file__).read_bytes()),'parser_sha256':e.digest((ROOT/'ecode360.py').read_bytes()),'accepted':False,'standalone_e2e_verified':False,'full_document':False,'capture_kind':'exact legal-content DOM subtree','capture_selector':'#codeContent','inventory_complete':False,'full_collection_verified':False}
 context=None;raw=None
 try:
  context=browser.new_context();page=context.new_page();response=page.goto(url,wait_until='domcontentloaded',timeout=30000)
  r['http_status']=response.status if response else None
  if response:
   data=response.body();(out/'response.html').write_bytes(data);r['http_response_sha256']=e.digest(data)
   chain=[];req=response.request
   while req:chain.append(req.url);req=req.redirected_from
   r['navigation_urls']=list(reversed(chain))
  initial=state(page);r['initial_state']={k:v for k,v in initial.items() if k!='html'}
  if initial['challenge'] or r['http_status'] in {401,403,429}:
   if not operator_assisted:
    r['blocker']='Publisher access/challenge response; no retry or challenge interaction attempted'
    raise e.ValidationError(r['blocker'])
   print('Operator-assisted mode: use the isolated browser only through normal publisher access. The script does not solve challenges. Press Enter after legal content is readable.',flush=True)
   input();r['operator_resume_at']=e.now()
  page.locator('.section_content').first.wait_for(state='attached',timeout=10000)
  before=None;after=None
  for attempt in range(4):
   before=state(page);time.sleep(0.25);after=state(page)
   if before['html'] and before['html']==after['html']:break
  r['settling_reads']=attempt+1
  before_html=before.pop('html');after_html=after.pop('html')
  raw=(before_html or '').encode('utf-8');before['sha256']=e.digest(raw);after['sha256']=e.digest((after_html or '').encode('utf-8'))
  r.update(browser_state=before,after_capture=after,raw_artifact_path='source.html',sha256=e.digest(raw),bytes=len(raw),requested_node_ready=before['heading_node_id']==requested,source_version_stable=before['identity']==after['identity'])
  r['accepted']=bool(raw and before_html==after_html and before['url']==url and after['url']==url and not before['challenge'] and all(before['identity'].values()) and before['identity']==after['identity'] and before['heading_node_id']==requested and before['section_bodies'] and before['toc'])
  if not r['accepted']:r['blocker']='Source URL/heading/customer/version/TOC/body readiness or start/end content stability check failed'
  (out/'source.html').write_bytes(raw)
 except Exception as exc:
  r['error']=str(exc)
  try:
   if context:
    page=context.pages[-1];data=page.content().encode('utf-8');(out/'rendered-failure.html').write_bytes(data);r['failure_dom_sha256']=e.digest(data);r['final_url']=page.url;r['title']=page.title();page.screenshot(path=str(out/'failure.png'),full_page=False)
  except Exception as capture_error:r['failure_capture_error']=str(capture_error)
 finally:
  if context:context.close()
 r['finished_at']=e.now();e.dump(out/'receipt.json',r)
 if r['accepted']:
  # Shared source verifier/parser is runtime-independent. The returned result is
  # explicitly relabeled here: a standalone acquisition is never called CUA.
  result=ingest(out/'receipt.json',job['jurisdiction'],out/'pipeline')
  passed=result.pop('supported_browser_e2e_verified');result['standalone_e2e_verified']=passed;result['standalone_automated_acquisition_verified']=passed and not operator_assisted;result['operator_assisted_acquisition_verified']=passed and operator_assisted;result['transport']=r['transport'];result['status']='current_standalone_acquisition_parse_exports_verified' if passed else 'failed_closed'
  e.dump(out/'pipeline/e2e-result.json',result);r['standalone_e2e_verified']=passed;e.dump(out/'receipt.json',r)
 return r

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--routes',default=str(ROOT/'current-routes.json'));p.add_argument('--slugs',nargs='*');p.add_argument('--out',required=True);p.add_argument('--channel',choices=['chrome','chromium'],default='chrome');p.add_argument('--headed',action='store_true');p.add_argument('--operator-assisted',action='store_true');p.add_argument('--delay',type=float,default=1.5);a=p.parse_args()
 if a.operator_assisted and not a.headed:p.error('operator-assisted mode requires --headed')
 routes=e.load(a.routes)
 if a.slugs:
  selected=set(a.slugs);unknown=selected-{r['slug'] for r in routes}
  if unknown:p.error('unknown route slugs: '+','.join(sorted(unknown)))
  routes=[r for r in routes if r['slug'] in selected]
 results=[];out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 try:
  with sync_playwright() as pw:
   launch={'headless':not a.headed}
   if a.channel=='chrome':launch['channel']='chrome'
   browser=pw.chromium.launch(**launch)
   for i,job in enumerate(routes):
    r=acquire(browser,job,out/job['slug'],headed=a.headed,operator_assisted=a.operator_assisted,channel=a.channel)
    results.append({'slug':job['slug'],'http_status':r.get('http_status'),'accepted':r['accepted'],'standalone_e2e_verified':r['standalone_e2e_verified'],'blocker':r.get('blocker') or r.get('error'),'receipt':str((out/job['slug']/'receipt.json').relative_to(out))})
    e.dump(out/'summary.json',{'results':results,'all_pass':all(x['standalone_e2e_verified'] for x in results),'full_collection_verified':False});print(json.dumps(results[-1]),flush=True)
    if i<len(routes)-1:time.sleep(max(0,a.delay))
   browser.close()
 except Exception as exc:e.dump(out/'runtime-failure.json',{'error':str(exc),'time':e.now(),'script_sha256':e.digest(Path(__file__).read_bytes())});print(str(exc),file=sys.stderr);return 2
 return 0 if all(x['standalone_e2e_verified'] for x in results) else 2
if __name__=='__main__':sys.exit(main())
