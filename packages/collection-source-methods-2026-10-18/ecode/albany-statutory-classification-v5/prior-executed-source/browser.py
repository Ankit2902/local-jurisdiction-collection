"""Ordinary headed Chrome. Public same-context fetch; redirect:error; no challenge retries."""
import base64,platform,sys
from pathlib import Path
from urllib.parse import urlsplit
from .common import *
class Browser:
 def __init__(self,family,out,gate_dir=None):self.family=family;self.out=Path(out);self.gate=Gate(family,gate_dir);self.events=[];self.blocked=False
 def __enter__(self):
  from playwright.sync_api import sync_playwright
  self.gate.check();self.pw=sync_playwright().start();self.browser=self.pw.chromium.launch(channel='chrome',headless=False);self.context=self.browser.new_context(accept_downloads=True);self.page=self.context.new_page()
  self.runtime={'python':sys.version,'platform':platform.platform(),'chrome':self.browser.version,'playwright':__import__('importlib.metadata').metadata.version('playwright'),'beautifulsoup4':__import__('importlib.metadata').metadata.version('beautifulsoup4'),'requests':__import__('importlib.metadata').metadata.version('requests'),'headed':True,'storage_imported':False}
  def route(r):
   u=urlsplit(r.request.url)
   if self.blocked:return r.abort()
   if r.request.resource_type in ['image','font','media']:return r.abort()
   if u.scheme not in ['http','https']:return r.continue_()
   if u.hostname and (u.hostname.endswith('ecode360.com') or u.hostname.endswith('municipal.codes') or u.hostname=='challenges.cloudflare.com'):
    try:
     if r.request.resource_type in ['document','fetch','xhr']:self.gate.reserve(r.request.url)
    except AccessStop:self.blocked=True;return r.abort()
   elif r.request.resource_type not in ['document','fetch','xhr']:return r.abort()
   return r.continue_()
  self.context.route('**/*',route)
  def response(r):
   if not (urlsplit(r.url).hostname or '').endswith(('ecode360.com','municipal.codes')):return
   event={'url':r.url,'status':r.status,'resource_type':r.request.resource_type,'at':now(),'retry_after':r.headers.get('retry-after'),'cf_mitigated':r.headers.get('cf-mitigated')};self.events.append(event);save(self.out/'network-events.json',self.events)
   if r.status in [403,429] or (r.status==503 and r.headers.get('retry-after')) or r.headers.get('cf-mitigated')=='challenge':self.blocked=True;self.gate.stop(event)
  self.context.on('response',response);save(self.out/'runtime.json',self.runtime);return self
 def _check(self,raw,url,status,headers):
  from bs4 import BeautifulSoup
  if status in [403,429] or (status==503 and headers.get('retry-after')) or headers.get('cf-mitigated')=='challenge':self.gate.stop({'url':url,'status':status,'retry_after':headers.get('retry-after'),'reason':'access refusal'});self.blocked=True;raise AccessStop('HTTP access refusal '+str(status))
  if 'html' in headers.get('content-type',''):
   sp=BeautifulSoup(raw,'html.parser');title=sp.title.get_text(' ',strip=True).lower() if sp.title else ''
   if any(t in title for t in ['just a moment','attention required','access denied','verify you are human']) or sp.select_one('#challenge-form,#cf-challenge-running,#challenge-running,#cf-error-details,.cf-error-details'):
    self.gate.stop({'url':url,'status':status,'reason':'challenge document'});self.blocked=True;raise AccessStop('Access challenge')
  if status!=200:raise QualificationError('HTTP '+str(status)+' '+url)
 def bootstrap(self,url):
  self.gate.check();r=self.page.goto(url,wait_until='domcontentloaded',timeout=60000)
  # The ordinary publisher may reload after passive browser checks. Wait locally;
  # never retry a navigation or lose the current DOM by demanding an old response body.
  try:self.page.wait_for_load_state('load',timeout=30000)
  except Exception:pass
  self.page.wait_for_timeout(8000)
  try:self.page.wait_for_load_state('load',timeout=30000)
  except Exception:pass
  raw=self.page.content().encode();event=next((e for e in reversed(self.events) if e['resource_type']=='document' and e['url']==self.page.url),None)
  meta={'url':self.page.url,'requested_url':url,'status':event['status'] if event else (r.status if r else None),'headers':{'content-type':'text/html','cf-mitigated':event.get('cf_mitigated') if event else None},'retrieved_at':now(),'transport':'ordinary-headed-Chrome stable DOM snapshot','initial_document_url':r.url if r else None}
  return raw,meta
 def fetch(self,url,method='GET'):
  self.gate.check()
  # The context route applies the shared gate to this same-browser fetch. Redirects fail without following.
  result=self.page.evaluate("""async u=>{const c=new AbortController();const t=setTimeout(()=>c.abort(),60000);try{const r=await fetch(u.url,{redirect:'error',method:u.method,signal:c.signal});const b=new Uint8Array(await r.arrayBuffer());let s='';for(let i=0;i<b.length;i+=16384)s+=String.fromCharCode(...b.subarray(i,i+16384));return {url:r.url,status:r.status,headers:Object.fromEntries(r.headers),data:btoa(s)}}finally{clearTimeout(t)}}""",{'url':url,'method':method})
  raw=base64.b64decode(result.pop('data'));meta={**result,'requested_url':url,'method':method,'retrieved_at':now(),'transport':'ordinary-headed-Chrome public same-context fetch; redirects rejected'}
  # Return refusal bytes too, so the caller can persist before raising.
  return raw,meta
 def check(self,raw,meta):return self._check(raw,meta['url'],meta['status'],meta['headers'])
 def native_html(self):
  self.gate.check();p=self.page
  p.get_by_role('button',name='Save, share, bookmark or print this page or your selections.',exact=True).click(timeout=10000);p.get_by_role('link',name='This Page',exact=True).click(timeout=10000);p.wait_for_timeout(1000);p.locator('#share-save-tab').click(timeout=10000);p.wait_for_timeout(300)
  a=p.locator('#share-save a[data-share-format=html]');observed=a.get_attribute('href')
  with p.expect_download(timeout=120000) as pending:a.click(timeout=10000)
  d=pending.value;ev=next((e for e in reversed(self.events) if e['url']==d.url),None);tmp=self.out/'native-download.tmp';d.save_as(tmp);raw=tmp.read_bytes();tmp.unlink();return raw,{'url':d.url,'observed_href':observed,'suggested_filename':d.suggested_filename,'http_status':ev['status'] if ev else None,'download_completed':True,'retrieved_at':now(),'transport':'observed Share/ThisPage/Save/WebPage native publisher export'}
 def __exit__(self,*args):
  save(self.out/'network-events.json',self.events);save(self.out/'runtime.json',self.runtime)
  try:self.context.close()
  finally:
   try:self.browser.close()
   finally:self.pw.stop()
