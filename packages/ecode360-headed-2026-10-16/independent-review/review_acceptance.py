#!/usr/bin/env python3
"""Offline receipt acceptance regressions; adversarial metadata is never live proof."""
import argparse,copy,hashlib,importlib,json,sys
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',required=True);p.add_argument('--receipt',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 package=Path(a.package).resolve();sys.path.insert(0,str(package));s=importlib.import_module('source_controls');e=importlib.import_module('ecode360');r=json.loads(Path(a.receipt).read_text());registry=json.loads((package/'route-registry.json').read_text());row=next(x for x in registry if x['slug']==r['job']['slug']);results=[]
 def verify(x):s.verify_route_binding(x,row['jurisdiction'],'municipal-code');s.acquisition_transport(x,standalone=True)
 verify(r);results.append({'name':'actual_fresh_receipt_accepts','passed':True,'kind':'acceptance metadata only; source semantic review separate'})
 cases=[('wrong_customer',lambda x:x['browser_state']['identity'].__setitem__('customer_id','WRONG')),('unreviewed_code_edition',lambda x:x['browser_state']['identity'].__setitem__('code_id','999999999')),('cross_city_slug',lambda x:x['job'].__setitem__('slug','burlingame-ca')),('wrong_acquisition_route',lambda x:x['job'].__setitem__('url','https://ecode360.com/999999999')),('operator_assisted_label',lambda x:x.__setitem__('operator_assisted',True)),('missing_runtime_mode',lambda x:x.pop('acquisition_mode')),('imported_storage_state',lambda x:x['runtime'].__setitem__('storage_state_imported',True)),('not_fresh_context',lambda x:x['runtime'].__setitem__('fresh_context',False)),('non200_final_document',lambda x:x.__setitem__('final_document_http_status',403)),('intermediate429',lambda x:x['response_chronology'].append({'status':429})),('rate_limit_marked',lambda x:x.__setitem__('rate_limit',{'status':429}))]
 for name,mutate in cases:
  x=copy.deepcopy(r);mutate(x)
  try:verify(x);rejected=False;error=None
  except (e.ValidationError,ValueError,KeyError) as exc:rejected=True;error=str(exc)
  results.append({'name':name,'passed':rejected,'error':error,'kind':'offline adversarial receipt metadata'})
 x=copy.deepcopy(r);x['browser_state']['identity']['currency_raw']='2099-01-01';verify(x);results.append({'name':'calendar_currency_not_pinned_to_historical_date','passed':True,'kind':'metadata registry check only; raw/start/end identity must still match during ingest'})
 results.append({'name':'comparison_preserves_word_boundaries','passed':s.comparison_text('the rapist')!=s.comparison_text('therapist') and s.comparison_text('a b')!=s.comparison_text('ab'),'kind':'offline negative text regression'})
 results.append({'name':'comparison_preserves_punctuation','passed':s.comparison_text('shall not')!=s.comparison_text('shall, not'),'kind':'offline negative text regression'})
 results.append({'name':'comparison_ignores_rendering_whitespace','passed':s.comparison_text('a\n b')==s.comparison_text('a b'),'kind':'offline normalization regression'})
 out=Path(a.out)
 if out.exists():raise ValueError('Review evidence is immutable; use fresh output')
 out.parent.mkdir(parents=True,exist_ok=True);report={'publisher_network_calls':0,'source_hashes':{n:hashlib.sha256((package/n).read_bytes()).hexdigest() for n in ['source_controls.py','ecode360.py','route-registry.json']},'receipt_sha256':hashlib.sha256(Path(a.receipt).read_bytes()).hexdigest(),'checks':results,'all_passed':all(x['passed'] for x in results)};out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(results),'all_passed':report['all_passed']}));sys.exit(not report['all_passed'])
if __name__=='__main__':main()
