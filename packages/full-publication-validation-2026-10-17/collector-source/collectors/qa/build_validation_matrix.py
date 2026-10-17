#!/usr/bin/env python3
"""Author a compact evidence-level matrix from explicitly selected retained runs; no network."""
import argparse,hashlib,json
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def norm(u):p=urlsplit(u);return p.netloc.lower()+p.path.rstrip('/')
def main():
 p=argparse.ArgumentParser();p.add_argument('--evidence-root',type=Path,required=True);p.add_argument('--runs',type=Path,default=HERE/'selected-runs.json');p.add_argument('--out',type=Path,default=HERE/'validation-matrix.json');a=p.parse_args();targets=read(ROOT/'collectors/registry/targets.json')['targets'];pubs=read(ROOT/'collectors/registry/publications.json')['publications'];proofs=[]
 for selected in read(a.runs)['runs']:
  run=a.evidence_root/selected['run'];family=selected['family'];cov=read(run/'coverage.json');cp=read(run/'checkpoint.json') if (run/'checkpoint.json').exists() else {};matched=[]
  for pub in pubs:
   if pub['publisher']!=family:continue
   if family=='municode':match=pub.get('publisher_product_id') in [int(v) for v in cov['selected_product_ids']] and pub['expected_identity'].get('publisher_client_id')==cp.get('client_id')
   elif family=='american-legal':i=cov['publication_identity'];match=pub.get('selector',{}).get('publication')==i['code_slug'] and urlsplit(pub['source_url']).path.split('/')[2]==i['client_slug']
   elif family=='ecode':match=norm(pub['source_url'])==norm(cp['publication_url'])
   elif family=='encodeplus':match=norm(pub['source_url'])==norm(cp['config']['base'])
   else:match=pub.get('dispatch_config',{}).get('id')==read(run/'config.json')['id']
   if match:matched.append(pub['id'])
  text=cov.get('publication_text_complete',cov.get('publication_html_text_coverage_complete',False));assets=cov.get('attachments_complete',cov.get('attachment_complete',cov.get('publication_attachments_complete',False)))
  if family=='official':assets=bool(cov.get('publication_file_coverage_complete')) and not cov.get('required_assets_unresolved') and not cov.get('required_components_unresolved')
  metrics=cov
  if family=='municode' and len(cov['selected_product_ids'])==1:metrics=read(run/'publications'/cov['selected_product_ids'][0]/'coverage.json')
  proof={'family':family,'evidence_run':selected['run'],'publication_ids':matched,'scope_class':selected['scope_class'],'publication_text_complete':text,'attachments_complete':assets,'full_live_text_and_assets':bool(text and assets and selected.get('unlimited',False)),'edition_complete':cov.get('edition_complete',metrics.get('publication_edition_consistent',False)),'jurisdiction_complete':False,'native_files_or_pages_complete':cov.get('native_publication_files_complete',cov.get('pdf_page_extraction_complete',False)),'coverage_sha256':hashlib.sha256((run/'coverage.json').read_bytes()).hexdigest(),'counts':{k:v for k,v in metrics.items() if k in ['inventory_count','acquired_count','inventory_nodes','inventory_node_count','source_document_count','parsed_container_count','body_nodes','record_count','expected_document_count','acquired_document_count','parsed_record_count','image_omission_count','image_marker_count','image_placeholders','image_placeholder_count']},'gap_counts':{k:len(metrics[k]) for k in ['missing_ids','missing_assets','missing_document_ids','unresolved_required_assets'] if k in metrics},'limitations':selected.get('limitations',[])}
  proofs.append(proof)
 report=read(HERE/'offline-report.json');passed_families={'municode','american-legal','ecode','encodeplus','official'} if report['passed'] else set();rows=[]
 for t in targets:
  live=[r for r in proofs if t['primary_publication_id'] in r['publication_ids']];full=any(r['full_live_text_and_assets'] for r in live);rows.append({'target_id':t['id'],'jurisdiction':t['jurisdiction'],'state':t['state'],'publisher':t['publisher'],'runnable_primary':t['runnable'],'primary_publication_id':t['primary_publication_id'],'validation_level':'full_live_publication_text_and_assets_verified' if full else 'family_implementation_tested' if t['publisher'] in passed_families else 'mapped_only','primary_full_live_verified':full,'primary_live_proof_indices':[proofs.index(r) for r in live],'prior_bounded_status':t['prior_validation']['sample_status'],'jurisdiction_complete':False})
 a.out.write_text(json.dumps({'schema_version':1,'scope_note':'Exact primary live proof, family implementation tests and mapping-only status are separate. Native-file/page completion is not section/table/OCR semantic completion. No jurisdiction is complete. Base registry flags remain conservative historical mappings.','offline_qa_passed':report['passed'],'targets':rows,'selected_live_or_retained_proofs':proofs},indent=2)+'\n')
if __name__=='__main__':main()
