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

def is_publisher_host(host):
 return bool(host and (host=='ecode360.com' or host.endswith('.ecode360.com')))

def inspect_export_ui(page,ctx,out,rate):
 meta=page.evaluate("()=>({flags:Object.fromEntries(Array.from(document.body.attributes).filter(a=>/pdf|word|export|download/.test(a.name)).map(a=>[a.name,a.value])),sections:Array.from(document.querySelectorAll('.section_content')).map(x=>({id:x.id.replace('_content',''),text:x.innerText.length})).sort((a,b)=>a.text-b.text)})")
 result={'method':'ordinary standalone headed UI; observed content checkbox then Download selected content','metadata_before':meta,'file_acquired':False}
 try:
  if rate:raise e.ValidationError('host stopped before export action')
  result['consent_actions']=[]
  for consent_selector in ['#silktide-banner button.reject-all','#silktide-modal button.preferences-reject-all']:
   consent=page.locator(consent_selector)
   if consent.is_visible():
    if rate:raise e.ValidationError('host stopped before ordinary consent action')
    result['consent_actions'].append({'selector':consent_selector,'text':consent.inner_text(),'action':'ordinary click Reject non-essential'})
    consent.click(timeout=10000);page.locator('#silktide-backdrop').wait_for(state='hidden',timeout=10000);break
  if rate:raise e.ValidationError('host stopped before selection')
  nid=meta['sections'][0]['id'];selector='#guid_'+nid+'_content_checkbox';page.locator(selector).check(timeout=10000);result['selected_ids']=[nid];result['selected_citations']=page.locator('[id="'+nid+'"]').inner_text(timeout=5000)
  downloads=[];popups=[]
  page.on('download',lambda download:downloads.append(download));ctx.on('page',lambda popup:popups.append(popup))
  if rate:raise e.ValidationError('host stopped after local selection')
  page.get_by_role('button',name='Download selected content',exact=True).click(timeout=10000);page.wait_for_timeout(1500)
  if rate:raise e.ValidationError('host stopped during export UI')
  (out/'download-ui.html').write_text(page.content(),encoding='utf-8');page.screenshot(path=str(out/'download-ui.png'))
  result['visible_dialogs']=[]
  for dialog in page.locator('[role="dialog"],[role="menu"]').all():
   if dialog.is_visible():result['visible_dialogs'].append({'text':dialog.inner_text(),'html':dialog.evaluate('(e)=>e.outerHTML')})
  result['visible_controls']=page.get_by_role('button').all_text_contents();result['edition_after']=state(page)['identity']
  pdf=page.get_by_role('button',name='PDF',exact=True)
  if pdf.is_visible() and pdf.is_enabled():
   if rate:raise e.ValidationError('host stopped before observed PDF action')
   result['requested_format']='PDF';result['format_action']='ordinary click observed enabled PDF button'
   pdf.click(timeout=10000)
   for tick in range(15):
    if rate:raise e.ValidationError('host stopped during PDF generation')
    page.wait_for_timeout(1000)
    if downloads:break
   (out/'pdf-action-final.html').write_text(page.content(),encoding='utf-8');page.screenshot(path=str(out/'pdf-action-final.png'))
   result['format_dialogs']=[]
   for dialog in page.locator('[role="dialog"],[role="menu"]').all():
    if dialog.is_visible():result['format_dialogs'].append({'text':dialog.inner_text(),'html':dialog.evaluate('(e)=>e.outerHTML')})
   result['edition_after_format_action']=state(page)['identity']
  result['popup_urls']=[public_url(popup.url) for popup in popups]
  result['downloads']=[]
  for i,download in enumerate(downloads):
   if rate:raise e.ValidationError('host stopped before retaining download')
   target=out/('publisher-download-'+str(i)+Path(download.suggested_filename).suffix)
   download.save_as(str(target));result['downloads'].append({'suggested_filename':download.suggested_filename,'path':target.name,'bytes':target.stat().st_size,'sha256':e.digest(target.read_bytes()),'url':public_url(download.url)})
  result['file_acquired']=bool(result['downloads'])
 except Exception as ex:result['error']=str(ex)
 e.dump(out/'download-observation.json',result);return result

def probe(url,slug,customer,out,authorization,seconds=60,code_id=None,inspect_download=False):
 if not 1<=seconds<=60:raise e.ValidationError('bounded passive wait must be1..60seconds')
 url=e.fetch_url(url);out=Path(out)
 registry={x['slug']:x for x in e.load(ROOT/'route-registry.json')}
 planned=registry.get(slug)
 if not planned or planned['discovery_url']!=url or planned['customer_id']!=customer:raise e.ValidationError('job slug/route/customer registry mismatch')
 code_id=code_id or planned['code_id']
 if code_id!=planned['code_id']:raise e.ValidationError('unreviewed publication code edition')
 if out.exists() and any(out.iterdir()):raise e.ValidationError('new empty output directory required')
 auth=e.load(authorization)
 if not auth.get('explicit_user_authorized_resumption'):raise e.ValidationError('explicit resumption authorization required')
 stop=ROOT/'headed-live/CURRENT-HOST-STOP.json'
 if stop.exists():raise e.ValidationError('new-phase host stop exists; no browser launch permitted')
 out.mkdir(parents=True,exist_ok=True)
 scriptsha=e.digest(Path(__file__).read_bytes());events=[];rate={};initial_status=None;last_doc_status=None;before=None;after=None;source=None
 r={'schema_version':1,'job':{'slug':slug,'id':'source','url':url,'kind':'legal','expected_node_id':url.rsplit('/',1)[-1]},'started_at':e.now(),'transport':'standalone Python Playwright ordinary headed Chrome; fresh isolated context; passive verification only','acquisition_mode':'fully_standalone_headed','headed':True,'operator_assisted':False,'authorization_sha256':e.digest(Path(authorization).read_bytes()),'script_sha256':scriptsha,'accepted':False,'full_document':False,'capture_kind':'exact legal-content DOM subtree','capture_selector':'#codeContent','full_collection_verified':False,'expected_customer_id':customer,'expected_code_id':code_id,'registry_sha256':e.digest((ROOT/'route-registry.json').read_bytes()),'state_helper_sha256':e.digest((ROOT/'standalone.py').read_bytes()),'core_helper_sha256':e.digest((ROOT/'ecode360.py').read_bytes()),'passive_wait_limit_seconds':seconds}
 with sync_playwright() as pw:
  browser=pw.chromium.launch(channel='chrome',headless=False);ctx=browser.new_context();page=ctx.new_page();r['runtime']={'python':sys.version,'platform':platform.platform(),'browser':browser.version,'playwright':__import__('importlib.metadata').metadata.version('playwright'),'channel':'chrome','fresh_context':True,'storage_state_imported':False}
  def restrict(route):
   if rate and is_publisher_host(urlsplit(route.request.url).hostname):route.abort()
   else:route.continue_()
  ctx.route('**/*',restrict)
  def response(resp):
   nonlocal last_doc_status
   if not is_publisher_host(urlsplit(resp.url).hostname):return
   event={'time':e.now(),'url':public_url(resp.url),'status':resp.status,'resource_type':resp.request.resource_type,'method':resp.request.method,'headers':{k:v for k,v in resp.headers.items() if k.lower() in {'retry-after','content-type','cf-ray','etag','last-modified'}}};events.append(event)
   if resp.request.resource_type=='document':last_doc_status=resp.status
   if resp.status==429 and not rate:
    rate.update(event);e.dump(stop,{'status':'stop_all_ecode360_network','observed_at':e.now(),'event':event,'automatic_retry':False,'receipt_path':str(out/'receipt.json')})
    rate['body_capture_status']='not_read_in_callback; headers retained and future publisher requests aborted immediately'
  ctx.on('response',response)
  try:
   response0=page.goto(url,wait_until='domcontentloaded',timeout=30000);initial_status=response0.status if response0 else None
   if rate:raise e.ValidationError('429 hard stop; no passive wait or further navigation')
   page.screenshot(path=str(out/'initial.png'));deadline=time.monotonic()+seconds
   while time.monotonic()<deadline:
    if rate:raise e.ValidationError('429 hard stop during passive verification')
    snap=state(page)
    legal=bool(not snap['challenge'] and snap['url']==url and snap['identity'].get('customer_id')==customer and snap['identity'].get('code_id')==code_id and all(snap['identity'].values()) and snap['heading_node_id']==r['job']['expected_node_id'] and snap['html'] and snap['section_bodies'] and snap['toc'])
    if legal:
     before=snap;page.wait_for_timeout(500)
     if rate:raise e.ValidationError('429 hard stop during source settling')
     after=state(page)
     if before['html']==after['html'] and before['identity']==after['identity'] and before['heading_node_id']==after['heading_node_id'] and after['url']==url and not after['challenge']:
      source=before['html'].encode('utf-8');r['accepted']=True;break
    page.wait_for_timeout(500)
   if rate:raise e.ValidationError('429 hard stop')
   if not r['accepted']:r['blocker']='Legal source/readiness not reached in bounded passive wait; not a claim of permanent denial'
   r['final_state']={k:v for k,v in state(page).items() if k!='html'};page.screenshot(path=str(out/'final.png'));(out/'rendered-final.html').write_text(page.content(),encoding='utf-8')
   if inspect_download and r['accepted'] and not rate:r['download_inspection']=inspect_export_ui(page,ctx,out,rate)
  except Exception as ex:r['accepted']=False;r['error']=str(ex)
  finally:
   if rate:r['accepted']=False
   r.update(initial_http_status=initial_status,final_document_http_status=last_doc_status,response_chronology=events,rate_limit=rate or None,finished_at=e.now())
   if source is not None:
    (out/'source.html').write_bytes(source);before.pop('html',None);after.pop('html',None);before['sha256']=e.digest(source);after['sha256']=e.digest(source);r.update(browser_state=before,after_capture=after,raw_artifact_path='source.html',sha256=e.digest(source),bytes=len(source),requested_node_ready=True)
   try:ctx.close();browser.close()
   except Exception as ex:r['accepted']=False;r['close_error']=str(ex)
   if rate:r['accepted']=False
   e.dump(out/'receipt.json',r)
 return r

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--url',required=True);p.add_argument('--slug',required=True);p.add_argument('--customer',required=True);p.add_argument('--out',required=True);p.add_argument('--authorization',required=True);p.add_argument('--seconds',type=int,default=60);a=p.parse_args()
 if not 1<=a.seconds<=60:p.error('bounded passive wait must be1..60seconds')
 r=probe(a.url,a.slug,a.customer,a.out,a.authorization,a.seconds);print(json.dumps({'accepted':r['accepted'],'initial_http_status':r['initial_http_status'],'final_document_http_status':r['final_document_http_status'],'rate_limit':r['rate_limit'],'blocker':r.get('blocker') or r.get('error'),'receipt':str(Path(a.out)/'receipt.json')},indent=2));return 0 if r['accepted'] else 2
if __name__=='__main__':sys.exit(main())
