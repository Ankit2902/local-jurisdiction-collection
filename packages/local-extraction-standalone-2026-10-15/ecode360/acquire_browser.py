#!/usr/bin/env python3
"""Bounded standalone Playwright acquisition, isolated fresh profile, no stealth."""
import argparse,json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import ecode360 as e

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('url');p.add_argument('--out',required=True);p.add_argument('--channel',default='chrome');p.add_argument('--expected-node');a=p.parse_args();url=e.fetch_url(a.url);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 receipt={'requested_url':url,'started_at':e.now(),'transport':'standalone Python Playwright; fresh isolated browser context; no stealth or auth','channel':a.channel,'accepted':False,'full_collection_verified':False};raw=b''
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(channel=a.channel,headless=True)
   context=browser.new_context();page=context.new_page()
   response=page.goto(url,wait_until='domcontentloaded',timeout=30000);receipt['http_status']=response.status if response else None
   try:page.locator('.section_content').first.wait_for(state='attached',timeout=10000)
   except Exception as x:receipt['readiness_error']=str(x)
   receipt.update(final_url=page.url,title=page.title())
   raw=page.content().encode('utf-8');identity,items=e.parse_page(raw.decode(),page.url)
   after=page.content().encode('utf-8');receipt['source_version']=identity;receipt['source_sha256_start']=e.digest(raw);receipt['source_sha256_end']=e.digest(after);receipt['parsed_records']=len(items)
   wanted=a.expected_node or url.rsplit('/',1)[-1]
   from bs4 import BeautifulSoup
   soup=BeautifulSoup(raw,'html.parser');found=soup.find(id=wanted) or soup.find(id=wanted+'_content') or soup.select_one('#pageTitle [data-guid="'+wanted+'"]')
   receipt['expected_node']=wanted;receipt['expected_node_found']=bool(found)
   receipt['accepted']=bool(raw==after and items and found and page.url==url and not receipt.get('readiness_error'))
   context.close();browser.close()
 except Exception as x:receipt['error']=str(x)
 if raw:(out/'source.html').write_bytes(raw);receipt['raw_path']='source.html';receipt['raw_sha256']=e.digest(raw)
 receipt['finished_at']=e.now();e.dump(out/'receipt.json',receipt);print(json.dumps(receipt,indent=2));return 0 if receipt['accepted'] else 2
if __name__=='__main__':sys.exit(main())
