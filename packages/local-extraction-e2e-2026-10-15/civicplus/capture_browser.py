#!/usr/bin/env python3
"""Fresh isolated Chrome capture; TLS checks stay enabled. Requires playwright."""
import argparse,hashlib,json,sys,platform,shutil
from importlib.metadata import version
from datetime import datetime,timezone
from pathlib import Path
from playwright.sync_api import sync_playwright
from civicplus import ROOTS

def stamp(): return datetime.now(timezone.utc).isoformat()
def digest(b): return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--jurisdiction',choices=ROOTS,required=True);p.add_argument('--out',required=True);p.add_argument('--channel',choices=['chrome','chromium'],default='chrome');p.add_argument('--executable-path');args=p.parse_args()
 out=Path(args.out);out.mkdir(parents=True,exist_ok=False); started=stamp();receipt={'started_at':started,'runtime':'standalone_playwright','jurisdiction':args.jurisdiction,'requested_url':ROOTS[args.jurisdiction],'ignore_https_errors':False,'files':{}}
 try:
  with sync_playwright() as pw:
   if args.executable_path: executable=Path(args.executable_path).expanduser().resolve()
   elif args.channel=='chromium': executable=Path(pw.chromium.executable_path)
   elif platform.system()=='Darwin': executable=Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
   else:
    found=shutil.which('google-chrome') or shutil.which('google-chrome-stable') or shutil.which('chrome')
    if not found: raise ValueError('Installed Chrome path not detected; pass --executable-path or install/select bundled Chromium explicitly')
    executable=Path(found)
   if not executable.is_file(): raise ValueError('Browser executable missing: '+str(executable)+'; install Chrome, pass --executable-path, or run python -m playwright install chromium and select --channel chromium')
   receipt['browser_executable']=str(executable);receipt['browser_channel']=args.channel;receipt['playwright_version']=version('playwright')
   browser=pw.chromium.launch(executable_path=str(executable),channel=args.channel,headless=True)
   try:
    context=browser.new_context(accept_downloads=True)
    page=context.new_page();response=page.goto(ROOTS[args.jurisdiction],wait_until='domcontentloaded',timeout=60000)
    if response is None or response.status!=200:raise RuntimeError('Official index did not return HTTP200')
    receipt.update(browser_version=browser.version,playwright_version=version('playwright'),browser_channel=args.channel,status=response.status,final_url=page.url,headers={k:v for k,v in response.all_headers().items() if k.lower() not in ('set-cookie',)})
    raw=response.body();(out/'index.html').write_bytes(raw);receipt['files']['index.html']=digest(raw)
    if args.jurisdiction=='portland-me':
     heading=page.get_by_role('heading',name='City Code Documents',exact=True);heading.wait_for(state='visible',timeout=30000)
     rendered=heading.evaluate('(e)=>e.parentElement.parentElement.outerHTML').encode()
     (out/'widget.html').write_bytes(rendered);receipt['files']['widget.html']=digest(rendered)
    else:
     page.get_by_role('heading',name='Code Chapters',exact=True).wait_for(state='visible',timeout=30000)
    receipt.update(finished_at=stamp(),result='captured')
   finally:browser.close()
 except Exception as e:
  receipt.update(finished_at=stamp(),result='blocked',error=str(e));(out/'capture-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt));return 2
 (out/'capture-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt));return 0
if __name__=='__main__':sys.exit(main())
