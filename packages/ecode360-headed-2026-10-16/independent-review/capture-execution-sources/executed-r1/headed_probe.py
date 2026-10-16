#!/usr/bin/env python3
"""Explicitly authorized ordinary headed sentinel with passive verification only."""
import argparse,json,platform,sys,time
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
from playwright.sync_api import sync_playwright
import ecode360 as e
from standalone import state
ROOT=Path(__file__).resolve().parent

def public_url(url):
 u=urlsplit(url);return urlunsplit((u.scheme,u.netloc,u.path,'',''))

def probe(url,slug,customer,out,authorization,seconds=60):
 url=e.fetch_url(url);out=Path(out)
 if out.exists() and any(out.iterdir()):raise e.ValidationError('new empty output directory required')
 auth=e.load(authorization)
 if not auth.get('explicit_user_authorized_resumption'):raise e.ValidationError('explicit resumption authorization required')
 stop=ROOT/'headed-live/CURRENT-HOST-STOP.json'
 if stop.exists():raise e.ValidationError('new-phase host stop exists; no browser launch permitted')
 out.mkdir(parents=True,exist_ok=True)
 scriptsha=e.digest(Path(__file__).read_bytes());events=[];rate={};initial_status=None;last_doc_status=None;before=None;after=None;source=None
 r={'schema_version':1,'job':{'slug':slug,'id':'source','url':url,'kind':'legal','expected_node_id':url.rsplit('/',1)[-1]},'started_at':e.now(),'transport':'standalone Python Playwright ordinary headed Chrome; fresh isolated context; passive verification only','acquisition_mode':'fully_standalone_headed','headed':True,'operator_assisted':False,'authorization_sha256':e.digest(Path(authorization).read_bytes()),'script_sha256':scriptsha,'accepted':False,'full_document':False,'capture_kind':'exact legal-content DOM subtree','capture_selector':'#codeContent','full_collection_verified':False,'expected_customer_id':customer,'passive_wait_limit_seconds':seconds}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(channel='chrome',headless=False);ctx=browser.new_context();page=ctx.new_page();r['runtime']={'python':sys.version,'platform':platform.platform(),'browser':browser.version,'playwright':__import__('importlib.metadata').metadata.version('playwright'),'channel':'chrome','fresh_context':True,'storage_state_imported':False}
  def restrict(route):
   if rate and urlsplit(route.request.url).hostname=='ecode360.com':route.abort()
   else:route.continue_()
  ctx.route('**/*',restrict)
  def response(resp):
   nonlocal last_doc_status
   if urlsplit(resp.url).hostname!='ecode360.com':return
   event={'time':e.now(),'url':public_url(resp.url),'status':resp.status,'resource_type':resp.request.resource_type,'method':resp.request.method,'headers':{k:v for k,v in resp.headers.items() if k.lower() in {'retry-after','content-type','cf-ray','etag','last-modified'}}};events.append(event)
   if resp.request.resource_type=='document':last_doc_status=resp.status
   if resp.status==429 and not rate:
    rate.update(event);e.dump(stop,{'status':'stop_all_ecode360_network','observed_at':e.now(),'event':event,'automatic_retry':False,'receipt_path':str(out/'receipt.json')})
    try:data=resp.body();(out/'rate-limit-response.html').write_bytes(data);rate['body_sha256']=e.digest(data)
    except Exception as ex:rate['body_capture_error']=str(ex)
  ctx.on('response',response)
  try:
   response0=page.goto(url,wait_until='domcontentloaded',timeout=30000);initial_status=response0.status if response0 else None
   if rate:raise e.ValidationError('429 hard stop; no passive wait or further navigation')
   page.screenshot(path=str(out/'initial.png'));deadline=time.monotonic()+seconds
   while time.monotonic()<deadline:
    if rate:raise e.ValidationError('429 hard stop during passive verification')
    snap=state(page)
    legal=bool(not snap['challenge'] and snap['identity'].get('customer_id')==customer and all(snap['identity'].values()) and snap['heading_node_id']==r['job']['expected_node_id'] and snap['html'] and snap['section_bodies'] and snap['toc'])
    if legal:
     before=snap;page.wait_for_timeout(500)
     if rate:raise e.ValidationError('429 hard stop during source settling')
     after=state(page)
     if before['html']==after['html'] and before['identity']==after['identity'] and before['heading_node_id']==after['heading_node_id']:
      source=before['html'].encode('utf-8');r['accepted']=True;break
    page.wait_for_timeout(500)
   if rate:raise e.ValidationError('429 hard stop')
   if not r['accepted']:r['blocker']='Legal source/readiness not reached in bounded passive wait; not a claim of permanent denial'
   r['final_state']={k:v for k,v in state(page).items() if k!='html'};page.screenshot(path=str(out/'final.png'));(out/'rendered-final.html').write_text(page.content(),encoding='utf-8')
  except Exception as ex:r['error']=str(ex)
  finally:
   r.update(initial_http_status=initial_status,final_document_http_status=last_doc_status,response_chronology=events,rate_limit=rate or None,finished_at=e.now())
   if source is not None:
    (out/'source.html').write_bytes(source);before.pop('html',None);after.pop('html',None);before['sha256']=e.digest(source);after['sha256']=e.digest(source);r.update(browser_state=before,after_capture=after,raw_artifact_path='source.html',sha256=e.digest(source),bytes=len(source),requested_node_ready=True)
   ctx.close();browser.close();e.dump(out/'receipt.json',r)
 return r

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--url',required=True);p.add_argument('--slug',required=True);p.add_argument('--customer',required=True);p.add_argument('--out',required=True);p.add_argument('--authorization',required=True);p.add_argument('--seconds',type=int,default=60);a=p.parse_args()
 if not 1<=a.seconds<=60:p.error('bounded passive wait must be1..60seconds')
 r=probe(a.url,a.slug,a.customer,a.out,a.authorization,a.seconds);print(json.dumps({'accepted':r['accepted'],'initial_http_status':r['initial_http_status'],'final_document_http_status':r['final_document_http_status'],'rate_limit':r['rate_limit'],'blocker':r.get('blocker') or r.get('error'),'receipt':str(Path(a.out)/'receipt.json')},indent=2));return 0 if r['accepted'] else 2
if __name__=='__main__':sys.exit(main())
