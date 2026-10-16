#!/usr/bin/env python3
"""Bounded, isolated, ordinary Playwright transport. No challenge bypass or shared profile."""
import argparse, hashlib, json, platform
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
from cp_collect import allowed

def sha(b): return hashlib.sha256(b).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def run(jobs, out, channel='chrome', headed=False):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    if not 1 <= len(jobs) <= 20: raise ValueError('1–20 explicit source-observed jobs required')
    source=Path(__file__).read_bytes(); (out/'acquisition-script.py').write_bytes(source)
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel=channel,headless=not headed)
        context=browser.new_context() # isolated; no user profile, cookies or CDP
        try:
            for job in jobs:
                if not allowed(job['root_url'],job['url']) or urlsplit(job['url']).scheme!='https': raise ValueError('out-of-scope job')
                if any(not str(job[k]).replace('-','').isalnum() for k in ('slug','id')): raise ValueError('unsafe slug/id')
                folder=out/job['slug']; folder.mkdir(exist_ok=True)
                page=context.new_page(); start=now(); error=None; status=None
                try:
                    response=page.goto(job['url'],wait_until='domcontentloaded',timeout=20000)
                    status=response.status if response else None
                    page.locator(job['wait_selector']).first.wait_for(state='attached',timeout=12000)
                except Exception as e: error=str(e)
                html=page.content(); raw=html.encode('utf-8'); title=page.title()
                headers=page.locator('#mainContent h3.Cite').evaluate_all('(els)=>els.map(e=>({id:e.id,text:e.textContent.trim()}))')
                again=page.content().encode('utf-8'); url=page.url
                challenge=bool(page.locator('#challenge-form,#cf-error-details').count()) or any(x in title.lower() for x in ('just a moment','attention required','access denied'))
                accepted=not error and not challenge and (status is None or status<400) and url==job['url'] and sha(raw)==sha(again) and (job['kind']!='legal' or bool(headers)) and (not job.get('expected_id') or any(h['id']==job['expected_id'] for h in headers))
                path=folder/(job['id']+'.html'); path.write_bytes(raw)
                receipt=dict(schema_version=1,job=job,started_at=start,finished_at=now(),transport='standalone Python Playwright isolated new_context',runtime={'python':platform.python_version(),'channel':channel,'headed':headed,'browser_version':browser.version},acquisition_script_sha256=sha(source),raw_artifact_path=path.name,bytes=len(raw),sha256=sha(raw),second_read_sha256=sha(again),final_url=url,title=title,legal_headings=headers,http_status=status,error=error,challenge=challenge,accepted=accepted,whole_corpus_complete=False)
                (folder/(job['id']+'.receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n')
                results.append({'slug':job['slug'],'accepted':accepted,'http_status':status,'error':error,'bytes':len(raw)})
                page.close()
        finally: context.close(); browser.close()
    return results
if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--jobs',required=True);a.add_argument('--out',required=True);a.add_argument('--channel',default='chrome');a.add_argument('--headed',action='store_true'); args=a.parse_args()
    print(json.dumps(run(json.loads(Path(args.jobs).read_text()),args.out,args.channel,args.headed),indent=2))
