#!/usr/bin/env python3
"""Bounded live publisher validation; serial requests; retained evidence and offline replay."""
import argparse,csv,datetime,hashlib,json,platform,re,sys,time,fcntl
from pathlib import Path
from urllib.parse import urljoin,urlsplit
sys.path.insert(0,str(Path(__file__).parent/'lib'))
import requests
from bs4 import BeautifulSoup
import municipal_codes_cli as mc, ecode360 as ec, cp_collect as cp
ROOT=Path(__file__).resolve().parent
FIELDS=ec.FIELDS

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,o):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def get(url,out):
 out=Path(out);out.parent.mkdir(parents=True,exist_ok=True);out.with_name(out.name+'.executed.py').write_bytes(Path(__file__).read_bytes())
 gate=ROOT/'evidence'/'http-gate.json';stop=ROOT/'evidence'/'HTTP-STOP.json'
 if stop.exists():raise RuntimeError('Previous HTTP429; network stopped; review receipt before another run')
 if gate.exists():time.sleep(max(0,3-(time.time()-json.loads(gate.read_text())['time'])))
 save(gate,{'time':time.time()})
 r=requests.get(url,timeout=45,allow_redirects=True);out.write_bytes(r.content)
 receipt={'requested_url':url,'url':r.url,'status':r.status_code,'headers':dict(r.headers),'retrieved_at':now(),'sha256':sha(r.content),'bytes':len(r.content),'transport':'standalone requests; public HTTP; no retries','script_sha256':sha(Path(__file__).read_bytes()),'runtime':{'python':platform.python_version(),'requests':requests.__version__},'redirects':[{'url':h.url,'status':h.status_code,'location':h.headers.get('Location')} for h in r.history]}
 save(out.with_suffix('.receipt.json'),receipt)
 if r.status_code==429:save(stop,receipt)
 return receipt

def parse(job,out):
 out=Path(out);meta=json.loads((out/'acquisition.json').read_text());raw=(out/'source.html').read_bytes()
 assert sha(raw)==meta['sha256'],'raw hash mismatch'
 html=raw.decode('utf-8');rows=[];details={}
 if job['family']=='municipal.codes':
  rec,notes=mc.parse_page(html,meta['url'],job['base']);details={'notes':notes}
  for r in rec:
   row=dict.fromkeys(FIELDS,'');row.update(jurisdiction=job['jurisdiction'],code_name=job['code_name'],section_number=r['section_number'],section_name=r['section_name'],citation=r['citation'],full_text=r['full_text'],source_url=r['source_url'],scrape_date=meta['retrieved_at'][:10]);rows.append(row)
  details['source_records']=rec
 elif job['family']=='eCode360':
  identity,rec=ec.parse_page(html,meta['url'],job.get('expected_identity'));
  expected_node=job.get('expected_node')
  if expected_node and not BeautifulSoup(html,'html.parser').select_one('header .contentTitle[data-guid=\"'+str(expected_node)+'\"]'):raise ValueError('Requested heading GUID absent')
  if job.get('expected_customer') and identity['customer_id']!=job['expected_customer']:raise ValueError('Expected publisher customer mismatch')
  details={'identity':identity,'source_records':rec}
  for r in rec:
   row=dict.fromkeys(FIELDS,'');row.update(jurisdiction=job['jurisdiction'],code_name=job['code_name'],section_number=r['display_number'],section_name=r['display_heading'],citation=r['citation'],full_text=r['full_text'],source_url=r['source_url'],scrape_date=meta['retrieved_at'][:10]);rows.append(row)
 else:
  page={'url':meta['url'],'publication_id':'municipal-code','path':'source.html','sha256':sha(raw),'content_selector':job.get('selector','#mainContent')}
  snap={'jurisdiction_slug':job['slug'],'jurisdiction':job['jurisdiction'],'snapshot_id':'fresh-2026-10-17','publications':[{'publication_id':'municipal-code','title':job['code_name']}],'retrieved_at':meta['retrieved_at']}
  details=cp.parse_page(raw,page,snap);rows=details['records']
 if not rows:raise ValueError('No substantive records')
 (out/'records.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
 with (out/'records.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
 with (out/'records.csv').open(encoding='utf-8-sig',newline='') as f:assert list(csv.DictReader(f))==rows
 assert len({r['source_url'] for r in rows})==len(rows),'duplicate source URLs'
 assert all(r['citation'] and r['full_text'] and len(r['full_text'])>len(r['citation']) for r in rows)
 text='\n'.join(r['full_text'] for r in rows)
 tables=sum(len(BeautifulSoup(r.get('content_html',r.get('semantic_html','')),'html.parser').select('table')) for r in details.get('source_records',[]))
 if job['family']=='CodePublishing':tables=sum(len(BeautifulSoup(r['full_text'],'html.parser').select('table')) for r in rows)
 checks={'record_count':len(rows),'table_count':tables,'cross_reference_links':len(BeautifulSoup(html,'html.parser').select('main a[href],#codeContent a[href],#mainContent a[href]')),'csv_jsonl_equal':True,'raw_sha256_verified':True,'unique_source_urls':True,'citations_and_bodies_nonempty':True,'replacement_characters':text.count('\ufffd'),'complete_corpus':False,'output_sha256':{p.name:sha(p.read_bytes()) for p in [out/'records.jsonl',out/'records.csv']},'parser_sha256':{p.name:sha(p.read_bytes()) for p in (ROOT/'lib').glob('*.py')}}
 save(out/'parse-details.json',details);save(out/'checks.json',checks);print(json.dumps(checks));return checks

def browser(job,out,export=False,discover=False):
 from playwright.sync_api import sync_playwright
 stopfile=ROOT/'evidence'/('BROWSER-STOP-'+job['family'].replace('.','-')+'.json')
 historic=ROOT/'evidence'/'BROWSER-STOP.json'
 if historic.exists() and job['family']=='municipal.codes':raise RuntimeError('municipal.codes429 stop retained; no retry in this run')
 if stopfile.exists():raise RuntimeError('Publisher family429 stop exists')
 out=Path(out)
 if out.exists() and any(out.iterdir()):raise RuntimeError('Fresh empty output directory required for live browser acquisition')
 out.mkdir(parents=True,exist_ok=True);(out/'executed-collect.py').write_bytes(Path(__file__).read_bytes());events=[];blocked=[];downloads=[]
 with sync_playwright() as p:
  b=p.chromium.launch(channel='chrome',headless=False);ctx=b.new_context(accept_downloads=True);page=ctx.new_page()
  def response(r):
   if urlsplit(r.url).hostname==urlsplit(job['url']).hostname:
    events.append({'url':r.url,'status':r.status,'type':r.request.resource_type,'retry_after':r.headers.get('retry-after')})
    if r.status==429:blocked.append(events[-1]);save(stopfile,events[-1])
  ctx.on('response',response);ctx.route('**/*',lambda route:route.abort() if blocked and urlsplit(route.request.url).hostname==urlsplit(job['url']).hostname else route.continue_())
  ctx.on('download',lambda d:downloads.append(d))
  started=now();error=None
  try:
   page.goto(job['url'],wait_until='domcontentloaded',timeout=45000)
   deadline=time.monotonic()+45
   while time.monotonic()<deadline:
    if blocked:raise RuntimeError('HTTP429; stopped')
    if (discover and page.locator('#toc').count()) or (job['family']=='eCode360' and page.locator('.section_content').count() and page.locator('body[data-cust-id]').count()) or (job['family']!='eCode360' and (page.locator('main').count() or page.locator('#mainContent').count() or page.locator('frame').count()) and (not job.get('ready_text') or job['ready_text'] in page.locator('body').inner_text())):break
    page.wait_for_timeout(1000)
   if ec.BeautifulSoup(page.content(),'html.parser').title and mc.challenge(page.content()):raise RuntimeError('Access challenge; stopped without retry')
   page.wait_for_timeout(750)
   html=page.content();(out/'source.html').write_text(html);page.screenshot(path=str(out/'source.png'),full_page=False)
   meta={'requested_url':job['url'],'url':page.url,'retrieved_at':started,'sha256':sha((out/'source.html').read_bytes()),'runtime':{'python':platform.python_version(),'platform':platform.platform(),'browser':b.version,'playwright':__import__('importlib.metadata').metadata.version('playwright')},'transport':'ordinary standalone headed Chrome; fresh browser context; no operator assistance','script_sha256':sha(Path(__file__).read_bytes()),'events':events,'blocked':blocked}
   save(out/'acquisition.json',meta)
   if export and not blocked and job['family']=='municipal.codes':
    exp={'downloads':[]}
    try:
     page.get_by_role('button',name='Save, share, bookmark or print this page or your selections.',exact=True).click(timeout=10000);page.wait_for_timeout(1000)
     page.get_by_role('link',name='This Page',exact=True).click(timeout=10000);page.wait_for_timeout(1500)
     (out/'export-menu.html').write_text(page.content());page.screenshot(path=str(out/'export-menu.png'))
     exp['visible_links']=[{'text':a.inner_text(),'href':a.get_attribute('href')} for a in page.locator('a:visible').all() if any(x in a.inner_text().lower() for x in ['save','download','print'])]
     page.locator('#share-save-tab').click(timeout=10000);page.wait_for_timeout(500)
     exp['selected_format']='publisher HTML';exp['download_url']=page.locator('#share-save a[data-share-format=html]').get_attribute('href')
     page.locator('#share-save a[data-share-format=html]').click(timeout=10000)
     for _ in range(25):
      if blocked:raise RuntimeError('HTTP429 stopped export')
      if downloads:break
      page.wait_for_timeout(1000)
     for i,d in enumerate(downloads):
      target=out/f'publisher-export-{i}{Path(d.suggested_filename).suffix}';d.save_as(target);exp['downloads'].append({'path':target.name,'url':d.url,'filename':d.suggested_filename,'sha256':sha(target.read_bytes()),'bytes':target.stat().st_size})
     exp['file_acquired']=bool(downloads)
     (out/'export-final.html').write_text(page.content())
    except Exception as e:exp['error']=str(e)
    save(out/'publisher-export.json',exp)
   if export and not blocked and job['family']=='CodePublishing':
    exp={'downloads':[]}
    try:
     page.locator("span[onclick=\"openLevel('Burlington01');\"]").click(timeout=10000)
     page.locator('#divBurlington01 input[name=code]').first.wait_for(timeout=15000)
     exp['selected_values']=[]
     for leaf in page.locator('#divBurlington01 input[name=code]').all()[:3]:
      exp['selected_values'].append(leaf.get_attribute('value'));leaf.check(timeout=10000)
     page.locator('#printSubmit').click(timeout=10000);page.wait_for_timeout(2500)
     exp['pages']=[]
     for i,pop in enumerate(ctx.pages):
      artifact=out/f'export-page-{i}.html';artifact.write_text(pop.content());pop.screenshot(path=str(out/f'export-page-{i}.png'))
      sp=BeautifulSoup(pop.content(),'html.parser');exp['pages'].append({'url':pop.url,'path':artifact.name,'forms':[str(f) for f in sp.select('form')],'links':[{'text':a.get_text(' ',strip=True),'href':a.get('href')} for a in sp.select('a[href]')]})
     exportpage=next(pop for pop in ctx.pages if pop.locator('#saveAsSubmit').count())
     exportpage.locator('select[name=type]').select_option('HTML');exportpage.locator('#saveAsSubmit').click(timeout=10000)
     for _ in range(25):
      if blocked:raise RuntimeError('HTTP429 stopped export')
      if downloads:break
      page.wait_for_timeout(1000)
     for i,d in enumerate(downloads):
      target=out/f'publisher-export-{i}{Path(d.suggested_filename).suffix}';d.save_as(target);exp['downloads'].append({'path':target.name,'url':d.url,'filename':d.suggested_filename,'sha256':sha(target.read_bytes()),'bytes':target.stat().st_size})
     exp['file_acquired']=bool(downloads);exp['native_format']='HTML';exp['selected_scope']='first three observed chapter 1 leaf checkboxes'
    except Exception as e:exp['error']=str(e)
    save(out/'publisher-export.json',exp)
   if export and not blocked and job['family']=='eCode360':
    exp={'downloads':[]}
    try:
     for sel in ['#silktide-banner button.reject-all','#silktide-modal button.preferences-reject-all']:
      if page.locator(sel).is_visible():page.locator(sel).click();page.wait_for_timeout(600);break
     ids=page.locator('.section_content').evaluate_all('(els)=>els.map(x=>({id:x.id.replace("_content",""),length:x.innerText.length})).sort((a,b)=>a.length-b.length)');nid=ids[0]['id'];
     if job.get('export_prefer_table'):
      tables=page.locator('.section_content').evaluate_all('(els)=>els.filter(x=>x.querySelector(\"table\")).map(x=>x.id.replace(\"_content\",\"\"))')
      if tables:nid=tables[0]
     exp['selected_id']=nid
     page.locator('#guid_'+nid+'_content_checkbox').check(timeout=10000)
     page.get_by_role('button',name='Download selected content',exact=True).click(timeout=10000);page.wait_for_timeout(1000)
     (out/'export-menu.html').write_text(page.content());page.screenshot(path=str(out/'export-menu.png'))
     page.get_by_role('button',name='PDF',exact=True).click(timeout=10000)
     for _ in range(20):
      if blocked:raise RuntimeError('HTTP429 stopped export')
      if downloads:break
      page.wait_for_timeout(1000)
     for i,d in enumerate(downloads):
      target=out/f'publisher-export-{i}{Path(d.suggested_filename).suffix}';d.save_as(target);exp['downloads'].append({'path':target.name,'url':d.url,'filename':d.suggested_filename,'sha256':sha(target.read_bytes()),'bytes':target.stat().st_size})
     exp['file_acquired']=bool(downloads)
    except Exception as e:exp['error']=str(e)
    (out/'export-final.html').write_text(page.content());save(out/'publisher-export.json',exp)
  except Exception as e:error=str(e);save(out/'browser-failure.json',{'error':error,'events':events,'retrieved_at':started})
  finally:
   if (out/'acquisition.json').exists():
    final_meta=json.loads((out/'acquisition.json').read_text());final_meta['events']=events;final_meta['finished_at']=now();final_meta['blocked']=blocked;save(out/'acquisition.json',final_meta)
   ctx.close();b.close()
 if error:raise RuntimeError(error)
 return None if discover else parse(job,out)

def main():
 a=argparse.ArgumentParser();a.add_argument('--job',required=True);a.add_argument('--out');a.add_argument('--offline',action='store_true');a.add_argument('--get');a.add_argument('--browser',action='store_true');a.add_argument('--export',action='store_true');a.add_argument('--discover',action='store_true');x=a.parse_args();job=json.loads((ROOT/'jobs.json').read_text())[x.job];out=Path(x.out or ROOT/'evidence'/x.job)
 if x.get:print(json.dumps(get(x.get,out)));return
 if x.offline:parse(job,out);return
 if x.browser:
  with (ROOT/'evidence'/'browser.lock').open('a') as gate:
   fcntl.flock(gate,fcntl.LOCK_EX);time.sleep(3);browser(job,out,x.export,x.discover)
  return
 out.mkdir(parents=True,exist_ok=True);m=get(job['url'],out/'source.html');save(out/'acquisition.json',m)
 if m['status']!=200:raise RuntimeError('HTTP '+str(m['status']))
 parse(job,out)
if __name__=='__main__':main()
