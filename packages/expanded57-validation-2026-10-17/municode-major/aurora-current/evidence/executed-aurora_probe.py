#!/usr/bin/env python3
"""One explicitly authorized ordinary headed Aurora browser session; no bypass, bounded navigation."""
import argparse,datetime,hashlib,json,platform,sys,time
from pathlib import Path
from urllib.parse import urlsplit,urljoin
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import collect
ROOT=Path(__file__).resolve().parent
HOST='aurora.municipal.codes'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def capture(page,out,name,events):
 html=page.content();raw=html.encode();(out/(name+'.html')).write_bytes(raw);page.screenshot(path=str(out/(name+'.png')))
 sp=BeautifulSoup(html,'html.parser');links=[{'text':a.get_text(' ',strip=True),'url':urljoin(page.url,a['href'])} for a in sp.select('a[href]')]
 o={'url':page.url,'retrieved_at':collect.now(),'sha256':sha(raw),'bytes':len(raw),'title':sp.title.get_text(' ',strip=True) if sp.title else None,'main':bool(sp.select_one('main')),'articles':len(sp.select('main article')),'links':links,'events':list(events)};save(out/(name+'.json'),o);return o

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='evidence');a=ap.parse_args();out=ROOT/a.out
 if out.exists() and any(out.iterdir()):raise ValueError('New empty output required')
 out.mkdir(parents=True);(out/'executed-aurora_probe.py').write_bytes(Path(__file__).read_bytes());events=[];stop=[];downloads=[]
 if (ROOT/'CURRENT-HOST-STOP.json').exists():raise ValueError('Prior Aurora stop retained')
 with sync_playwright() as pw:
  b=pw.chromium.launch(channel='chrome',headless=False);ctx=b.new_context(accept_downloads=True);page=ctx.new_page()
  runtime={'python':sys.version,'platform':platform.platform(),'browser':b.version,'playwright':__import__('importlib.metadata').metadata.version('playwright'),'headed':True,'fresh_context':True,'operator_assistance':False}
  save(out/'runtime.json',runtime)
  def response(r):
   if urlsplit(r.url).hostname==HOST:
    events.append({'url':r.url,'status':r.status,'type':r.request.resource_type,'retry_after':r.headers.get('retry-after'),'at':collect.now()})
    if r.status==429:stop.append(events[-1]);save(ROOT/'CURRENT-HOST-STOP.json',events[-1])
  ctx.on('response',response);ctx.on('download',lambda d:downloads.append(d));ctx.route('**/*',lambda route:route.abort() if stop and urlsplit(route.request.url).hostname==HOST else route.continue_())
  try:
   page.goto('https://'+HOST+'/',wait_until='domcontentloaded',timeout=45000)
   deadline=time.monotonic()+30
   while time.monotonic()<deadline and not stop:
    if page.locator('main').count():break
    page.wait_for_timeout(1000)
   meta=capture(page,out,'root',events)
   if stop:raise RuntimeError('HTTP429 stop')
   if not meta['main'] or collect.mc.challenge(page.content()):raise RuntimeError('Persistent challenge/no legal main; one attempt stopped')
   print(json.dumps({'root':meta},ensure_ascii=False),flush=True)
   # Only exact observed same-host URLs may be followed. At most2 follow-up document navigations.
   for i in range(2):
    print('FOLLOW_OBSERVED_URL_OR_CAPTURE:',flush=True);target=input().strip()
    if target=='CAPTURE':break
    observed={x['url'] for x in meta['links']}
    if target not in observed or urlsplit(target).hostname!=HOST:raise ValueError('URL not present in captured source')
    time.sleep(3);page.goto(target,wait_until='domcontentloaded',timeout=45000);page.wait_for_timeout(1500)
    meta=capture(page,out,'navigation-'+str(i),events)
    if stop or collect.mc.challenge(page.content()):raise RuntimeError('Rate/challenge stop on observed follow-up')
    print(json.dumps({'navigation':meta},ensure_ascii=False),flush=True)
   # Source must contain operative legal records. Observed first URL segment defines publication boundary.
   base='https://'+HOST+'/'+urlsplit(page.url).path.strip('/').split('/')[0]
   job={'slug':'aurora','jurisdiction':'Aurora','family':'municipal.codes','code_name':meta['title'],'base':base,'url':page.url}
   save(ROOT/'jobs.json',{'aurora':job});sample=out/'sample';sample.mkdir();(sample/'source.html').write_text(page.content());page.screenshot(path=str(sample/'source.png'))
   acquire={'url':page.url,'requested_url':page.url,'retrieved_at':collect.now(),'sha256':sha((sample/'source.html').read_bytes()),'transport':'one ordinary standalone headed Chrome session; observed same-host navigation only','runtime':runtime,'script_sha256':sha(Path(__file__).read_bytes()),'events':events};save(sample/'acquisition.json',acquire)
   checks=collect.parse(job,sample)
   exp={'downloads':[],'native_format':'HTML'}
   try:
    page.get_by_role('button',name='Save, share, bookmark or print this page or your selections.',exact=True).click(timeout=10000);page.get_by_role('link',name='This Page',exact=True).click(timeout=10000);page.wait_for_timeout(1500)
    (sample/'export-menu.html').write_text(page.content());page.screenshot(path=str(sample/'export-menu.png'))
    page.locator('#share-save-tab').click(timeout=10000);page.wait_for_timeout(500);exp['observed_url']=urljoin(page.url,page.locator('#share-save a[data-share-format=html]').get_attribute('href'));page.locator('#share-save a[data-share-format=html]').click(timeout=10000)
    for _ in range(25):
     if stop:raise RuntimeError('Rate-limit stopped export')
     if downloads:break
     page.wait_for_timeout(1000)
    for i,d in enumerate(downloads):
     f=sample/('publisher-export-'+str(i)+Path(d.suggested_filename).suffix);d.save_as(f);exp['downloads'].append({'path':f.name,'filename':d.suggested_filename,'sha256':sha(f.read_bytes()),'url':d.url,'bytes':f.stat().st_size})
    exp['file_acquired']=bool(downloads)
   except Exception as e:exp['error']=str(e)
   save(sample/'publisher-export.json',exp);save(out/'final-events.json',events)
  except Exception as e:
   try:capture(page,out,'failure',events)
   except Exception:pass
   save(out/'failure.json',{'error':str(e),'events':events,'at':collect.now()});print(str(e),flush=True)
  finally:ctx.close();b.close()
if __name__=='__main__':main()
