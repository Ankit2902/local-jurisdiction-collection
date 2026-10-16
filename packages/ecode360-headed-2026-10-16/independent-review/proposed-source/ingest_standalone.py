#!/usr/bin/env python3
"""Verify a standalone capture receipt, import exact DOM, replay and compare text."""
import argparse,re,sys,html as html_lib
from pathlib import Path
from bs4 import BeautifulSoup
import ecode360 as e
from source_controls import verify_route_binding,acquisition_transport,comparison_text

def ingest(receipt_path,jurisdiction,out,publication_id='municipal-code'):
 receipt_path=Path(receipt_path);r=e.load(receipt_path);out=Path(out)
 if not r.get('accepted'):raise e.ValidationError('capture was not accepted; no publication or import')
 rawpath=e.safe_path(receipt_path.parent,r['raw_artifact_path']);raw=rawpath.read_bytes();sha=e.digest(raw)
 before=r['browser_state'];after=r['after_capture'];url=r['job']['url'];e.fetch_url(url)
 if sha!=r['sha256'] or sha!=before['sha256'] or sha!=after['sha256']:raise e.ValidationError('capture/raw/start/end SHA256 mismatch')
 if before['identity']!=after['identity'] or before['url']!=url or after['url']!=url:raise e.ValidationError('capture URL/version changed')
 if r.get('navigation_error') or r.get('readiness_error') or before.get('challenge'):raise e.ValidationError('capture navigation/readiness/challenge failure')
 verify_route_binding(r,jurisdiction,publication_id)
 transport_label=acquisition_transport(r,standalone=True)
 html=raw.decode('utf-8')
 if not r.get('full_document',True):
  attrs=' '.join('data-'+key+'="'+html_lib.escape(value,quote=True)+'"' for key,value in [('cust-id',before['identity']['customer_id']),('code-id',before['identity']['code_id']),('code-date',before['identity']['currency_raw'])])
  html='<!DOCTYPE html><html><head><title>'+html_lib.escape(before['title'])+'</title><link rel="canonical" href="'+html_lib.escape(url,quote=True)+'"></head><body '+attrs+'>'+html+'</body></html>'
 candidate=e.inventory_candidate(html,url);identity,items=e.parse_page(html,url,before['identity'])
 bodies={i['node_id']:i for i in items};nodes=candidate['nodes']
 if not nodes:raise e.ValidationError('no independent on-page TOC nodes')
 for n in nodes:
  n['classification']='substantive' if n['node_id'] in bodies else 'unresolved'
  n['classification_evidence']='raw source exact header/body '+n['node_id']+'_content' if n['node_id'] in bodies else ''
  n['hierarchy']={'chapter':BeautifulSoup(html,'html.parser').title.get_text().split(' - ')[0]}
 inv={'jurisdiction_slug':r['job']['slug'],'jurisdiction':jurisdiction,'publication_id':publication_id,'code_name':'Municipal Code','identity':identity,'source_version':'publisher-code-'+identity['code_id']+'-date-'+identity['currency_raw'],'inventory_complete':False,'inventory_scope':'current rendered on-page chapter TOC only; not full publication','inventory_evidence':{'receipt_sha256':e.digest(receipt_path.read_bytes()),'raw_sha256':sha,'selector':'#toc .contentTitle[data-code-content-type][data-guid]','independently_observed_toc':before['toc']},'scrape_date':r['finished_at'][:10],'source_retrieval_date':r['finished_at'],'nodes':nodes,'acquisition_units':[{'url':url,'evidence':'accepted capture receipt SHA256 '+e.digest(receipt_path.read_bytes())+'; '+transport_label}]}
 out.mkdir(parents=True,exist_ok=True);e.dump(out/'inventory.json',inv)
 (out/'retained-source.html').write_bytes(raw);(out/'source-document.html').write_text(html,encoding='utf-8');e.dump(out/'capture-receipt.json',r)
 imported=e.import_snapshot(out/'inventory.json',out/'source-document.html',url,out/'imported',r['finished_at'],transport=transport_label)
 manifest=e.load(out/'imported/artifacts.json')
 for artifact in manifest['artifacts']:artifact['transport']=transport_label
 e.dump(out/'imported/artifacts.json',manifest)
 report=e.replay(out/'inventory.json',out/'imported/artifacts.json',out/'exports')
 records=e.load(out/'exports/aggregate-fulltext.json')['provisions'];source=BeautifulSoup(html,'html.parser');comparisons=[]
 norm=comparison_text
 for record in records:
  nid=record['source_url'].split('#')[-1];body=source.find(id=nid+'_content')
  body=BeautifulSoup(str(body),'html.parser')
  for ignored in body.select('script,style,button,input,svg,noscript'):ignored.decompose()
  for image in body.select('img'):image.replace_with('[IMAGE]'+(' '+image.get('alt') if image.get('alt') else ''))
  raw_text=norm(body.get_text(' ',strip=True));export_text=norm(BeautifulSoup(record['full_text'],'html.parser').get_text(' ',strip=True))
  comparisons.append({'node_id':nid,'source_plaintext_sha256':e.digest(raw_text.encode()),'export_plaintext_sha256':e.digest(export_text.encode()),'comparison_rule':'Unicode lexical tokens and punctuation; word boundaries and source list markers retained','normalized_source_text_matches_export':raw_text==export_text})
 passed=not report['errors'] and report['unresolved_node_count']==0 and len(records)==len(nodes) and all(c['normalized_source_text_matches_export'] for c in comparisons)
 result={'status':'bounded_standalone_import_parse_exports_verified' if passed else 'failed_closed','transport':'standalone capture -> delivered importer -> parser -> CSV/JSON exports','standalone_automated_acquisition_verified':passed and not r.get('operator_assisted',False),'standalone_e2e_verified':passed,'acquisition_transport':transport_label,'acquisition_mode':r.get('acquisition_mode','supported_cua'),'operator_assisted':r.get('operator_assisted'),'source_url':url,'source_sha256':sha,'source_capture_kind':r.get('capture_kind','full document outerHTML'),'source_capture_selector':r.get('capture_selector','html'),'synthetic_wrapper_added':not r.get('full_document',True),'receipt_sha256':e.digest(receipt_path.read_bytes()),'source_version_start':before['identity'],'source_version_end':after['identity'],'source_version_stable_during_capture':True,'raw_import_sha256':imported['sha256'],'observed_toc_nodes':len(nodes),'parsed_records':len(records),'unresolved_nodes':report['unresolved_node_count'],'record_source_text_comparisons':comparisons,'inventory_verified':False,'full_collection_verified':False,'export_hashes':{str(p.relative_to(out)):e.digest(p.read_bytes()) for p in sorted((out/'exports').rglob('*')) if p.is_file()},'errors':report['errors']}
 e.dump(out/'e2e-result.json',result);return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',required=True);p.add_argument('--jurisdiction',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 try:r=ingest(a.receipt,a.jurisdiction,a.out);print(__import__('json').dumps(r,indent=2));return 0 if r['standalone_e2e_verified'] else 2
 except (e.ValidationError,OSError,KeyError) as x:print(str(x),file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
