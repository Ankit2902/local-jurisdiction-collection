#!/usr/bin/env python3
"""Portable read-only runtime inventory and one-shot clean browser probe.
No retries, UA override, user profile/cookie import, proxy rotation, or TLS weakening.
"""
import argparse,hashlib,importlib.metadata,json,os,platform,re,ssl,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import getproxies

def sha(value):return hashlib.sha256(value if isinstance(value,bytes) else value.encode()).hexdigest()
def save(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def now():return datetime.now(timezone.utc).isoformat()
def safe_error(value):
 # Errors may echo a configured URL; remove authentication and query values.
 def scrub(match):
  u=urlsplit(match.group(0));return u.scheme+'://'+(u.hostname or '')+u.path+('?[redacted]' if u.query else '')
 return re.sub(r'https?://[^\s\)\]\"\']+',scrub,str(value))
def package(name):
 try:return {'version':importlib.metadata.version(name),'requires_python':importlib.metadata.metadata(name).get('Requires-Python')}
 except importlib.metadata.PackageNotFoundError:return None

def inspect_runtime():
 proxy=[]
 for key,value in sorted(getproxies().items()):
  parsed=urlsplit(value if '://' in value else '//'+value)
  proxy.append({'scheme':key,'configured':bool(value),'has_embedded_credentials':bool(parsed.username or parsed.password)})
 ca={key:{'present':bool(os.environ.get(key)),'referenced_path_exists':Path(os.environ[key]).exists() if os.environ.get(key) else None} for key in ['SSL_CERT_FILE','SSL_CERT_DIR','REQUESTS_CA_BUNDLE','CURL_CA_BUNDLE','NODE_EXTRA_CA_CERTS']}
 system_proxy={'inspection':'not_available_on_this_platform'}
 if sys.platform=='darwin':
  try:
   text=subprocess.run(['scutil','--proxy'],capture_output=True,text=True,timeout=5,check=True).stdout
   system_proxy={'inspection':'scutil --proxy enabled flags only','enabled_flags':{k:int(v) for k,v in re.findall(r'(\w*Enable)\s*:\s*(\d+)',text)}}
  except Exception as exc:system_proxy={'inspection_error':safe_error(exc)}
 chrome=None
 if sys.platform=='darwin':
  app=Path('/Applications/Google Chrome.app/Contents/Info.plist')
  if app.exists():
   import plistlib
   with app.open('rb') as f:chrome=plistlib.load(f).get('CFBundleShortVersionString')
 return {'at':now(),'python':platform.python_version(),'python_implementation':platform.python_implementation(),'operating_system':platform.system(),'os_release':platform.release(),'architecture':platform.machine(),'ssl_backend':ssl.OPENSSL_VERSION,'packages':{n:package(n) for n in ['playwright','requests','urllib3','beautifulsoup4']},'proxy_configuration_presence_only':proxy,'system_proxy_presence_only':system_proxy,'custom_ca_configuration_presence_only':ca,'node_tls_validation_disabled_by_environment':os.environ.get('NODE_TLS_REJECT_UNAUTHORIZED')=='0','browser_cache_override_present':bool(os.environ.get('PLAYWRIGHT_BROWSERS_PATH')),'gui_display_variable_present':bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')),'installed_chrome_version':chrome,'secrets_recorded':False,'user_profile_or_cookie_store_inspected':False}

def probe(args):
 u=urlsplit(args.url)
 if u.scheme!='https' or not u.hostname or u.username or u.password:raise ValueError('Explicit public HTTPS URL without embedded authentication required')
 out=Path(args.out)
 if (out/'receipt.json').exists():raise ValueError('Receipt exists; this diagnostic never silently repeats a probe')
 ledger_path=Path(args.host_ledger) if args.host_ledger else out.parent/'HOST-STOP.json'
 ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {'stopped_hosts':{},'attempts':[]}
 if u.hostname in ledger.get('stopped_hosts',{}):raise ValueError('Host-wide stop recorded; operator review required; no request sent')
 key=sha(json.dumps([args.url,args.engine,args.headed]))
 if any(x['experiment_key']==key for x in ledger.get('attempts',[])):raise ValueError('Distinct experiment already attempted; no repeated request sent')
 out.mkdir(parents=True,exist_ok=True)
 record={'started_at':now(),'requested_url':args.url,'runtime':inspect_runtime(),'engine':args.engine,'headed':args.headed,'fresh_context':True,'persistent_profile_used':False,'explicit_proxy_configuration':False,'user_agent_override':False,'ignore_https_errors':False,'retry_count':0,'script_sha256':sha(Path(__file__).read_bytes()),'result':'not_completed','command':sys.argv}
 browser=None;context=None
 try:
  from playwright.sync_api import sync_playwright
  with sync_playwright() as driver:
   launch={'headless':not args.headed,'timeout':args.timeout*1000}
   if args.engine=='chrome':launch['channel']='chrome'
   browser=driver.chromium.launch(**launch);record['browser_version']=browser.version
   context=browser.new_context();record['cookies_before_count']=len(context.cookies());page=context.new_page()
   try:
    response=page.goto(args.url,wait_until='domcontentloaded',timeout=args.timeout*1000)
    record['http_status']=response.status if response else None
    if response and response.status==429:
     ledger['stopped_hosts'][u.hostname]={'status':429,'at':now(),'retry_after':response.headers.get('retry-after'),'policy':'stop all further host jobs; no automatic retry even after Retry-After; operator review required'}
     save(ledger_path,ledger)
    record['response_headers_allowlist']={k:v for k,v in (response.headers if response else {}).items() if k.lower() in {'server','content-type','cf-mitigated','retry-after'}}
    if response and response.status in {401,403,429,503}:record['result']='stopped_http_denial_or_challenge'
    else:
     if args.expect_selector:
      try:page.locator(args.expect_selector).first.wait_for(state='attached',timeout=args.readiness_seconds*1000);record['expected_selector_found']=True
      except Exception as exc:record['expected_selector_found']=False;record['readiness_error']=safe_error(exc)
     record['result']='public_document_observed' if not args.expect_selector or record.get('expected_selector_found') else 'document_without_expected_content'
    record['final_url']=page.url;record['title']=page.title();html=page.content();record['html_bytes']=len(html.encode());record['raw_sha256']=sha(html);record['raw_path']='page.html';(out/'page.html').write_text(html,encoding='utf8')
    text=page.locator('body').inner_text(timeout=3000).lower()
    record['challenge_or_denial_markers']=[term for term in ['just a moment','attention required','verify you are human','access denied','sorry, you have been blocked'] if term in text or term in (record['title'] or '').lower()]
    if record['challenge_or_denial_markers']:record['result']='stopped_challenge_or_denial_document'
    cookies=context.cookies();record['cookies_after_count']=len(cookies);record['cookie_names_after']=sorted({c['name'] for c in cookies});record['cookie_values_or_storage_exported']=False
    if args.screenshot:
     page.screenshot(path=str(out/'page.png'),full_page=False);record['screenshot_path']='page.png'
   except Exception as exc:record['exact_error']=safe_error(exc);record['result']='runtime_or_navigation_error'
   finally:context.close();browser.close();context=None;browser=None
 except Exception as exc:record['exact_error']=safe_error(exc);record['result']='runtime_launch_error'
 record['finished_at']=now();record['host_stop_ledger']=str(ledger_path);ledger['attempts'].append({'experiment_key':key,'url':args.url,'engine':args.engine,'headed':args.headed,'at':record['finished_at'],'status':record.get('http_status'),'result':record['result']});save(ledger_path,ledger);save(out/'receipt.json',record);print(json.dumps({k:record.get(k) for k in ['result','http_status','browser_version','title','exact_error','cookies_before_count','cookies_after_count']},indent=2))
 return 0

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
 inventory=sub.add_parser('inspect');inventory.add_argument('--out',required=True)
 q=sub.add_parser('probe');q.add_argument('--url',required=True);q.add_argument('--out',required=True);q.add_argument('--engine',choices=['chromium','chrome'],default='chromium');q.add_argument('--headed',action='store_true');q.add_argument('--timeout',type=int,default=30);q.add_argument('--expect-selector');q.add_argument('--readiness-seconds',type=int,default=10);q.add_argument('--screenshot',action='store_true');q.add_argument('--host-ledger',help='Shared stop ledger for all jobs in one run; defaults to output parent/HOST-STOP.json')
 a=p.parse_args()
 if a.mode=='inspect':save(a.out,inspect_runtime());print('Runtime inventory saved without credential/proxy values')
 else:sys.exit(probe(a))
if __name__=='__main__':main()
