"""Optional isolated standalone Playwright capture, with ordinary publisher readiness checks.

Requires playwright from requirements-browser.txt and installed Chrome or Chromium.
No persisted user profile, certificate bypass, challenge handling or stealth options.
"""
from __future__ import annotations
import argparse,json,hashlib
from pathlib import Path
from datetime import datetime,timezone

def capture(url,out,ready,channel='chrome'):
    from playwright.sync_api import sync_playwright
    out=Path(out)
    if out.exists():raise ValueError('Use a new immutable capture filename')
    with sync_playwright() as p:
        browser=p.chromium.launch(channel=channel or None,headless=True)
        page=browser.new_page();response=page.goto(url,wait_until='domcontentloaded',timeout=45000)
        if response is None or response.status>=400:raise RuntimeError('Browser navigation failed')
        page.locator(ready).wait_for(state='visible',timeout=45000)
        html=page.content();text=page.locator(ready).inner_text();final=page.url
        if '[Truncated]' in html:raise ValueError('Truncated capture')
        if any(x in page.title().lower() for x in ['access denied','just a moment','attention required']):raise RuntimeError('Access challenge; operator action required')
        browser.close()
    data=html.encode();out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
    meta={'url':url,'final_url':final,'status':response.status,'retrieved_at':datetime.now(timezone.utc).isoformat(),'transport':'standalone Playwright isolated browser','sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'ready_selector':ready,'ready_text':text,'original_http_bytes':False,'channel':channel}
    out.with_suffix(out.suffix+'.capture.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');return meta
if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--url',required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--ready-selector',required=True);a.add_argument('--channel',default='chrome');x=a.parse_args();print(json.dumps(capture(x.url,x.out,x.ready_selector,x.channel),ensure_ascii=False,indent=2))
