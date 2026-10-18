"""Observed visible Flagstaff City Code Print/Save workflow, ordinary headed Chrome; no images."""
import argparse,sys,re,traceback
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
from source_common import *
URL='https://www.codepublishing.com/AZ/Flagstaff/'
def snapshot(page,out,stem):
 frames=[]
 for index,frame in enumerate(page.frames):
  raw=frame.content().encode();rel=f'{stem}-frame-{index:02d}.html';transport.atomic(out/rel,raw)
  frames.append({'url':frame.url,'name':frame.name,'path':rel,'sha256':sha(raw),'title':frame.title(),'links':frame.locator('a[href]').evaluate_all("xs=>xs.map(x=>({url:x.href,href:x.getAttribute('href'),text:x.textContent.trim()}))"),'forms':frame.locator('form').evaluate_all("xs=>xs.map(x=>({action:x.action,method:x.method,target:x.target,html:x.outerHTML}))")})
 save(out/(stem+'-frames.json'),frames);return frames

def run(out):
 out=Path(out).resolve()
 if out.exists() and any(out.iterdir()):raise ValueError('Fresh output required')
 out.mkdir(parents=True,exist_ok=True);fp=source_snapshot(out,['flagstaff_full_collect.py','source_common.py','shared_transport.py']);meta={'source_url':URL,'started_at':stamp(),'python':sys.version,'code_fingerprint':fp,'images_downloaded':False,'complete':False,'scope':'Observed primary City Code selection/export workflow; completeness requires independent source normalization/closing reconciliation'};events=[];bodies=[];blocked=[]
 gate=transport.ROOT/sha((urlsplit(URL).hostname or '').encode())[:20]/'state.json'
 if gate.exists() and load(gate).get('stop'):raise RuntimeError('Existing publisher host stop; no browser/request started')
 with sync_playwright() as pw:
  browser=pw.chromium.launch(channel='chrome',headless=False);meta['browser']=browser.version
  try:
   context=browser.new_context(accept_downloads=True,ignore_https_errors=False)
   def route(r):
    if blocked or r.request.resource_type in ['image','font','media']:return r.abort()
    try:
     forbid(r.request.url)
     if r.request.resource_type in ['document','fetch','xhr']:transport.reserve(r.request.url)
    except Exception as e:blocked.append({'url':r.request.url,'message':str(e),'at':stamp()});return r.abort()
    r.continue_()
   context.route('**/*',route)
   def response(r):
    event={'url':r.url,'status':r.status,'headers':r.headers,'method':r.request.method,'resource_type':r.request.resource_type,'post_data':r.request.post_data,'at':stamp()};events.append(event)
    if r.status in [403,429] or r.headers.get('cf-mitigated','').lower()=='challenge' or r.headers.get('retry-after'):
     blocked.append(event);transport.stop(URL,r.status,r.headers,'Observed workflow refusal at '+r.url)
   context.on('response',response)
   def finished(request):
    if request.resource_type not in ['document','xhr','fetch']:return
    try:
     r=request.response();mime=r.headers.get('content-type','')
     if mime.lower().startswith('image/'):return
     if not any(x in mime for x in ['html','json','xml','pdf','text/plain']):return
     raw=r.body();rel=f'network-{len(bodies):04d}.bin';transport.atomic(out/rel,raw);bodies.append({'url':r.url,'status':r.status,'headers':r.headers,'path':rel,'bytes':len(raw),'sha256':sha(raw),'method':request.method,'post_data':request.post_data,'captured_at':stamp()})
    except Exception as e:bodies.append({'url':request.url,'capture_error':str(e)})
   context.on('requestfinished',finished)
   def download(d):
    rel='download-'+str(len(list(out.glob('download-*'))))+'-'+Path(d.suggested_filename).name;d.save_as(out/rel);save(out/(rel+'.receipt.json'),{'url':d.url,'path':rel,'sha256':sha((out/rel).read_bytes()),'bytes':(out/rel).stat().st_size,'native_original':True,'at':stamp()})
   context.on('page',lambda p:p.on('download',download));page=context.new_page();page.on('download',download)
   try:
    r=page.goto(URL,wait_until='domcontentloaded',timeout=180000);page.wait_for_timeout(7000)
    if blocked:raise RuntimeError('Publisher workflow access stop')
    if re.search(r'just a moment|verify.*human|access denied|attention required',page.title(),re.I):transport.stop(URL,r.status,{},'Visible source challenge');raise RuntimeError('Visible source challenge')
    before=snapshot(page,out,'opening');meta['opening_status']=r.status
    toc=next((f for f in page.frames if 'FlagstaffTOC.pl' in f.url),None)
    if toc is None:raise ValueError('Observed native TOC frame absent')
    span=toc.locator('#spanmuni')
    if span.count()!=1:raise ValueError('City Code publication selector absent/nonunique')
    span.click();page.wait_for_timeout(1500)
    inputs=toc.locator('#divmuni > p input[name="code"]').evaluate_all('xs=>xs.map(x=>({value:x.value,label:x.parentElement.textContent.trim()}))');meta['primary_title_selections']=inputs
    if len(inputs)<10 or any('Employee' in x['label'] for x in inputs):raise ValueError('City Code title-selection scope unqualified')
    # Expand publisher-observed roots to retain the complete descendant TOC independently.
    for item in inputs:
     control=toc.locator('input[name="code"][value='+json.dumps(item['value'])+']').first
     span=control.locator('xpath=preceding-sibling::span[1]')
     if span.count() and span.inner_text().strip()=='+':span.click();page.wait_for_timeout(500)
     if blocked:raise RuntimeError('Access stop during source inventory expansion')
    # The native exporter treats root values as title introductions only. Full publication
    # needs every expanded source-observed descendant, just as the native select-tree UI.
    # Set selection together to avoid its legacy asynchronous checkbox reset behavior.
    toc.locator('input[name="code"]').evaluate_all('xs=>xs.forEach(x=>x.checked=false)')
    toc.locator('#divmuni input[name="code"]').evaluate_all('xs=>xs.forEach(x=>x.checked=true)')
    actual=toc.locator('input[name="code"]:checked').evaluate_all('xs=>xs.map(x=>x.value)')
    expected=toc.locator('#divmuni input[name="code"]').evaluate_all('xs=>xs.map(x=>x.value)')
    if len(expected)<=len(inputs) or sorted(actual)!=sorted(expected):raise ValueError('Full descendant form selection differs from independent source TOC')
    meta['whole_publication_selected_values']=expected
    snapshot(page,out,'selected');meta['checked_values']=toc.locator('input[name="code"]:checked').evaluate_all('xs=>xs.map(x=>x.value)')
    toc.locator('input[type="submit"][name="Print/Save Selections"]').click(timeout=60000);page.wait_for_timeout(10000)
    if blocked:raise RuntimeError('Access stop during observed export')
    preview=next((p for p in context.pages if 'menuCompile.pl' in p.url),None)
    if preview is None:raise ValueError('Native preview absent')
    hidden=preview.locator('form[method="post"] input[name="code"]').evaluate_all('xs=>xs.map(x=>x.value)')
    meta['preview_hidden_selections']=hidden
    if set(hidden)!=set(expected):raise ValueError('Native preview selections do not equal complete expanded source TOC')
    preview.locator('select[name="type"]').select_option('HTML')
    with preview.expect_download(timeout=180000) as received:preview.locator('#saveAsSubmit').click(timeout=180000)
    d=received.value
    if not list(out.glob('download-*.receipt.json')):download(d)
    if blocked:raise RuntimeError('Access stop during native download')
    page.goto(URL,wait_until='domcontentloaded',timeout=180000);page.wait_for_timeout(3000)
    snapshot(page,out,'closing')
    results=[]
    results=[]
    for index,p in enumerate(context.pages):
     try:results.append({'url':p.url,'title':p.title(),'frames':snapshot(p,out,f'export-page-{index:02d}')})
     except Exception as e:results.append({'url':p.url,'error':str(e)})
    meta['export_pages']=results
   except Exception as e:meta['error']={'type':type(e).__name__,'message':str(e)}
   finally:
    meta.update(finished_at=stamp(),blocked=blocked,source_native_response_count=len(bodies));save(out/'network-events.json',events);save(out/'network-bodies.json',bodies);save(out/'receipt.json',meta);context.close()
  finally:browser.close()
 return meta
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();r=run(a.out);print(json.dumps({'complete':False,'error':r.get('error'),'blocked':r.get('blocked'),'primary_titles':len(r.get('primary_title_selections',[])),'export_pages':[{ 'url':x['url'],'title':x.get('title')} for x in r.get('export_pages',[])]},indent=2));raise SystemExit(3 if r.get('blocked') else 1 if r.get('error') else 0)
