#!/usr/bin/env python3
"""Offline-only independent safety controls. Actual baseline fixture; adversarial metadata
and mocked HTTP are negative tests, never fresh legal acquisition evidence.
"""
import argparse,contextlib,copy,hashlib,importlib,io,json,shutil,sys
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def run(package,out):
 package=Path(package).resolve();out=Path(out).resolve()
 if out.exists() and any(out.iterdir()):raise ValueError('Use new review output directory')
 out.mkdir(parents=True);sys.path.insert(0,str(package));e=importlib.import_module('ecode360');ing=importlib.import_module('ingest_cua');fixture=HERE/'fixtures/baseline-foster';results=[]
 with patch('requests.sessions.Session.request',side_effect=AssertionError('Network disabled by offline review')):
  raw=(fixture/'source-document.html').read_text();inv=e.load(fixture/'inventory.json')
  bad=copy.deepcopy(inv['identity']);bad['currency_raw']='wrong-edition-negative-test'
  try:e.parse_page(raw,inv['acquisition_units'][0]['url'],bad);accepted=True
  except e.ValidationError:accepted=False
  results.append({'control':'unexpected_edition_rejected','passed':not accepted,'evidence_kind':'actual baseline DOM with adversarial expected edition'})
  inp=out/'resume-input';shutil.copytree(fixture,inp);manifest=e.load(inp/'artifacts.json');rawpath=inp/manifest['artifacts'][0]['path'];replayout=out/'resume-output'
  first=e.replay(inp/'inventory.json',inp/'artifacts.json',replayout);original=rawpath.read_bytes();rawpath.write_bytes(original+b'\n<!-- review mutation after processed checkpoint -->')
  failure=None
  try:
   second=e.replay(inp/'inventory.json',inp/'artifacts.json',replayout);rejected=bool(second.get('errors'))
  except e.ValidationError as x:failure=str(x);rejected=True
  results.append({'control':'processed_raw_mutation_rejected_on_resume','passed':rejected,'error':failure,'original_raw_sha256':hashlib.sha256(original).hexdigest(),'changed_raw_sha256':sha(rawpath),'first_included_records':first.get('included_record_count'),'evidence_kind':'actual baseline DOM; local intentionally mutated test copy'})
  spoof=out/'mislabel-input';shutil.copytree(fixture,spoof);r=e.load(spoof/'relocated-receipt.json');r['job']['slug']='burlingame-ca';save(spoof/'spoofed-receipt.json',r);error=None
  try:
   result=ing.ingest(spoof/'spoofed-receipt.json','Burlingame',out/'mislabel-output');accepted=bool(result.get('supported_browser_e2e_verified'))
  except (e.ValidationError,ValueError) as x:error=str(x);accepted=False
  results.append({'control':'cross_city_receipt_mislabel_rejected','passed':not accepted,'error':error,'actual_source_customer':r['browser_state']['identity']['customer_id'],'adversarial_slug':'burlingame-ca','evidence_kind':'actual baseline source, deliberately spoofed local metadata; output is not trusted legal data'})
  response=type('Mock429',(),{'status_code':429,'headers':{'Retry-After':'120'},'is_redirect':False,'content':b'LOCAL MOCK429 - not a publisher response'})()
  error=None
  with patch.object(e,'HOST_STOP_PATH',out/'mock429-host-stop.json',create=True),patch.object(e.requests,'get',return_value=response) as get,patch.object(e.time,'sleep') as sleep:
   try:r=e.acquire('https://ecode360.com/51404426',out/'mock429')
   except (e.ValidationError,ValueError) as x:error=str(x)
   results.append({'control':'429_no_automatic_retry','passed':get.call_count<=1 and sleep.call_count==0,'mock_request_count':get.call_count,'sleep_calls':sleep.call_count,'error':error,'evidence_kind':'mocked negative transport response, zero live network'})
  routes=[{'slug':'one','discovery_url':'https://ecode360.com/51404426'},{'slug':'two','discovery_url':'https://ecode360.com/44507298'}];save(out/'mock-routes.json',routes)
  with patch.object(e,'acquire',return_value={'route_verified':False,'http_status':429}),patch.object(e.time,'sleep'),contextlib.redirect_stdout(io.StringIO()) as stdout:
   acquire=e.acquire
   code=e.main(['probe','--routes',str(out/'mock-routes.json'),'--out',str(out/'mock-probe'),'--delay','0'])
  results.append({'control':'429_stops_cross_city_probe_queue','passed':acquire.call_count<=1,'mock_acquire_calls':acquire.call_count,'exit_code':code,'evidence_kind':'mocked negative CLI queue; zero live network'})
 report={'scope':'Independent offline-only controls; no fresh acquisition claimed','package_source':str(package),'source_hashes':{n:sha(package/n) for n in ['ecode360.py','ingest_cua.py']},'fixture_origin':str(fixture/'origin.json'),'publisher_network_calls':0,'controls':results,'all_controls_passed':all(r['passed'] for r in results)}
 save(out/'controls.json',report);print(json.dumps(report,indent=2));return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',default=str(HERE/'baseline-source'));p.add_argument('--out',required=True);a=p.parse_args();run(a.package,a.out)
