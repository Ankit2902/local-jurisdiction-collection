#!/usr/bin/env python3
"""Probe a source-observed public Code Publishing Print/Save form once, without browser state.
No authentication/cookie transfer, automatic redirect, retry or challenge bypass.
"""
import argparse,hashlib,json,platform,sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import cp_collect as cp
HERE=Path(__file__).resolve().parent
SLUGS=['flagstaff-az','fremont-ca','san-carlos-ca','burien-wa','renton-wa']
def now():return datetime.now(timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def observed_form(slug):
    name='family-toc' if slug=='flagstaff-az' else 'chapter'
    source=HERE/'current-cua'/slug/(name+'.html');receipt=json.loads(source.with_suffix('.receipt.json').read_text())
    raw=source.read_bytes()
    if sha(raw)!=receipt['sha256'] or not receipt['accepted']:raise ValueError('Untrusted observed form source')
    soup=BeautifulSoup(raw,'html.parser');form=soup.select_one('form#myForm' if slug=='flagstaff-az' else 'form#saveForm')
    if not form or form.get('method','get').lower()!='post':raise ValueError('Expected source-observed POST export form missing')
    value=next(i['value'] for i in form.select('input[type=checkbox][name=code]') if '01/' in i['value'])
    endpoint=urljoin(receipt['job']['url'],form['action']);root=receipt['job']['root_url']
    if not cp.allowed(root,endpoint):raise ValueError('Observed form endpoint outside jurisdiction')
    data=[(i['name'],i.get('value','')) for i in form.select('input[type=hidden][name]')]
    data.append(('code',value))
    submit=form.select_one('input[type=submit][name]');data.append((submit['name'],submit.get('value','')))
    return {'slug':slug,'endpoint':endpoint,'root_url':root,'method':'POST','data':data,'observed_selection':value,'source_artifact':str(source.relative_to(HERE)),'source_sha256':sha(raw),'source_url':receipt['job']['url']}
def probe(job,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);folder=out/job['slug']
    if folder.exists():raise ValueError('Immutable probe output exists; choose fresh --out')
    folder.mkdir();script=Path(__file__).read_bytes();(folder/'executed-script.py').write_bytes(script)
    started=now();err=None;status=None;headers={};raw=b'';url=job['endpoint']
    try:
        with requests.Session() as session:
            response=session.post(job['endpoint'],data=job['data'],timeout=30,allow_redirects=False,stream=True)
            status=response.status_code;headers=dict(response.headers);url=response.url
            for chunk in response.iter_content(65536):
                raw+=chunk
                if len(raw)>20*1024*1024:raise ValueError('Bounded20MiB acquisition limit reached')
    except Exception as e:err=str(e)
    (folder/'response.bin').write_bytes(raw)
    soup=BeautifulSoup(raw,'html.parser');title=soup.title.get_text(' ',strip=True) if soup.title else ''
    challenge=bool(soup.select_one('#challenge-form,#cf-error-details,#cf-wrapper')) or bool(cp.BLOCKED.search(title))
    accepted=not err and status==200 and not challenge and bool(soup.select('form,a'))
    r={'schema_version':1,'job':job,'started_at':started,'finished_at':now(),'http_status':status,'response_url':url,'response_headers':headers,'error':err,'title':title,'challenge':challenge,'accepted_menu_response':accepted,'download_acquired':False,'raw_sha256':sha(raw),'bytes':len(raw),'raw_path':'response.bin','acquisition_script_sha256':sha(script),'runtime':{'python':platform.python_version(),'requests':requests.__version__},'cookies_imported':False,'retries':0,'tls_verify':True,'operator_assistance':False,'response_forms':[{'action':f.get('action'),'method':f.get('method'),'fields':[dict(i.attrs) for i in f.select('input,select,option')]} for f in soup.select('form')] if accepted else []}
    (folder/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');return {'slug':job['slug'],'status':status,'challenge':challenge,'menu_accepted':accepted,'error':err,'bytes':len(raw)}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);p.add_argument('--slug',choices=SLUGS,action='append');p.add_argument('--plan-only',action='store_true');a=p.parse_args();jobs=[observed_form(s) for s in (a.slug or SLUGS)]
    print(json.dumps(jobs if a.plan_only else [probe(j,a.out) for j in jobs],indent=2))
