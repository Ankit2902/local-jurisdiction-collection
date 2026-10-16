#!/usr/bin/env python3
"""Offline visual source QA; this screenshot is not a publisher export or browser-print PDF."""
import argparse,hashlib,importlib.metadata,json
from pathlib import Path
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('--file',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--channel',choices=['chrome','chromium'],default='chromium');p.add_argument('--executable-path');p.add_argument('--body',action='store_true',help='render full body for a short section export only');args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as pw:
 launch={'headless':True}
 if args.channel=='chrome':launch['channel']='chrome'
 if args.executable_path:launch['executable_path']=args.executable_path
 browser=pw.chromium.launch(**launch);context=browser.new_context(java_script_enabled=False,viewport={'width':1000,'height':1000});blocked=[]
 def stop(route):blocked.append(route.request.url);route.abort()
 context.route('**/*',stop);page=context.new_page();page.set_content(args.file.read_text(),wait_until='domcontentloaded')
 for selector,name in ([('body','source-body.png')] if args.body else [('table','source-first-table.png'),('#current','source-currentness.png')]):
  loc=page.locator(selector).first
  if loc.count():loc.screenshot(path=str(args.out/name))
 r={'input':str(args.file),'input_sha256':hashlib.sha256(args.file.read_bytes()).hexdigest(),'browser_version':browser.version,'channel':args.channel,'executable_path':args.executable_path or ('Playwright bundled Chromium' if args.channel=='chromium' else 'installed Google Chrome channel'),'playwright_version':importlib.metadata.version('playwright'),'javascript_enabled':False,'network_requests_blocked':blocked,'purpose':'offline visual inspection only; not acquisition/export evidence'};browser.close()
(args.out/'render-receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
