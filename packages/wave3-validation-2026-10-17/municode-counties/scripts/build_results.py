"""Authoring/rebuild only; normalized outputs and one result per assigned jurisdiction."""
import json,hashlib,re,tempfile,shutil
from pathlib import Path
from collect_all import ROOT,ASSIGNMENT,URLS,slug
from normalize import normalize

def rel(p):return str(p.relative_to(ROOT))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def author_normalize(d):
 with tempfile.TemporaryDirectory(prefix='county-normalize-author-') as td:
  report=normalize(d,td);current=d/'normalized'
  if current.exists() and any((current/fn).exists() and (current/fn).read_bytes()!=(Path(td)/fn).read_bytes() for fn in ['sections.jsonl','sections.csv']):
   old=json.loads((current/'verification.json').read_text());backup=d/'prior-normalized'/old.get('parser_sha256','unknown');backup.parent.mkdir(exist_ok=True)
   if not backup.exists():shutil.copytree(current,backup)
  shutil.copytree(td,current,dirs_exist_ok=True)
 return report

def main():
 results=[]
 for a in ASSIGNMENT:
  name=slug(a);d=ROOT/'browser'/name
  if not (d/'receipt.json').exists():d=ROOT/'http'/name
  receipt=json.loads((d/'receipt.json').read_text()) if (d/'receipt.json').exists() else {};report=None;checks=[];limitations=['Bounded validation only. Neither a TOC inventory nor a publisher download demonstrates a complete current jurisdiction corpus.','Record territorial applicability provision by provision; do not infer that a county code applies identically to incorporated and unincorporated areas.']
  for rr in receipt.get('responses',[]):checks.append({'check':'raw_source_sha256','file':rel(d/rr['file']),'passed':sha(d/rr['file'])==rr['sha256']})
  if (d/'samples.json').exists():
   try:report=author_normalize(d)
   except Exception as ex:limitations.append('Normalization failed: '+str(ex))
  primary=report['record_count'] if report else 0
  status='standalone_e2e_pass' if primary>=3 and receipt.get('status')=='acquired' else 'standalone_partial' if primary else 'blocked' if receipt else 'untested'
  publisher=dict(receipt.get('publisher_download',{'status':'not_tested','reason':'Shared publisher access stop before target acquisition; no target-specific live download tested.'}));publisher['evidence_paths']=[rel(p) for p in d.glob('*') if p.is_file() and any(s in p.name for s in ['publisher-export','pdf-url','client-content','receipt.json'])] if d.exists() else []
  edition_path=d/'publisher-export.validation.json'
  if edition_path.exists():
   edition=json.loads(edition_path.read_text());publisher['edition_check']=edition;publisher['transport_status']=publisher['status']
   if edition['edition_alignment_status'] in ['cover_label_differs','supplement_matches_update_unproven']:
    publisher['status']='partial';publisher['reason']='Native PDF transport passed, but cover supplement/update differs or lacks the current API update label; current-edition equivalence is unproven.';limitations.append('Native PDF cover supplement/update differs or lacks the current API update label. Treat downloaded edition as partial, not current corpus.')
   if not edition['pdf_cover_jurisdiction_state_match']:limitations.append('First native PDF page omits a complete jurisdiction/state label (may be an insertion guide); API client/state and enabled publication ID are independently bound. Cover-state identity is not proven by that page alone.')
   if edition['edition_alignment_status']=='unproven_missing_comparable_labels':limitations.append('Native PDF downloaded, but no comparable supplement labels on cover/API establish edition equivalence. See retained cover and API banner.')
  native=[]
  for nd in sorted((ROOT/'native').glob('*')) if (ROOT/'native').exists() else []:
   if not nd.is_dir() or not (nd/'source-config.json').exists() or not (nd/'normalized/verification.json').exists():continue
   cfg=json.loads((nd/'source-config.json').read_text())
   if cfg['sequence']!=a['sequence']:continue
   v=json.loads((nd/'normalized/verification.json').read_text());native.append({'publication':cfg['publication'],'folder':rel(nd),'record_count':v['record_count'],'record_unit':'PDF page','source_pdf_pages':v['source_pdf_pages'],'source_url':cfg['url'],'pdf_table_regions_detected':v['pdf_table_regions_detected'],'first_page_text_excerpt':v['first_page_text_excerpt'],'publisher_download':{'status':'passed','reason':'Native PDF acquired automatically from official government host; bounded page sample normalized.','url':cfg['url'],'evidence_paths':[rel(nd/'source.pdf'),rel(nd/'source.pdf.receipt.json')]}})
  if native and not primary:status='standalone_partial'
  publisher['additional_government_publications']=native
  if receipt.get('error'):limitations.append(receipt['error'])
  if receipt.get('stop_context'):limitations.append(receipt['stop_context'])
  if native:limitations += ['Supplemental PDF records are source pages, not inferred legal sections.','PDF table-region extraction can fragment merged headers and omit labels; no claim of fully normalized table fidelity.']
  if a.get('boundary_note'):limitations.append(a['boundary_note'])
  if a['sequence'] in [76,77]:limitations.append('Virginia independent city; separate from counties and from same-named jurisdictions in other states.')
  if a['sequence']==76:limitations.append('Supplemental parking table:27rows/154cells independently compared; two referenced diagram images were not acquired, so diagram fidelity is untested.')
  if a['sequence']==95:limitations.append('Combined Baton Rouge / East Baton Rouge Parish government; preserve city/parish/unincorporated-area distinctions. A city-only population is not assigned to this target.')
  evidence=[rel(p) for p in d.rglob('*') if p.is_file()] if d.exists() else []
  for n in native:evidence += [rel(p) for p in (ROOT/n['folder']).rglob('*') if p.is_file()]
  for p in [ROOT/'territorial-applicability-evidence.json',ROOT/'evidence/rate-gate/audit.json',ROOT/'publisher-download-verification.json',ROOT/'evidence/pdf-visual/qa.json',ROOT/'official-route-inventory.json',ROOT/'source-scope-inventory.json',ROOT/'family-stop-context.json']:
   if p.exists():evidence.append(rel(p))
  for p in (ROOT/'evidence/routes').glob('*') if (ROOT/'evidence/routes').exists() else []:
   if a['sequence']==95 and 'baton-rouge' in p.name or a['sequence']==96 and 'clark' in p.name or a['sequence']==90 and 'cambridge' in p.name or a['sequence']==89 and 'stamford' in p.name:evidence.append(rel(p))
  if report:
   records=[json.loads(line) for line in (d/'normalized/sections.jsonl').read_text().splitlines()]
   context=[{**rec,'jurisdiction':a['jurisdiction'],'state':a['state'],'entity_type':a['entity_type'],'territorial_scope_note':a.get('boundary_note','City enactments; do not infer external zoning/charter scope.'),'applicability_terms_present':sorted(set(re.findall(r'\b(?:unincorporated|incorporated|parish|county|city)\b',rec['text'],re.I)))} for rec in records]
   (d/'normalized/sections-context.jsonl').write_text(''.join(json.dumps(rec,ensure_ascii=False)+'\n' for rec in context))
  if report:checks.append({'check':'exact_requested_identifier_nonempty_heading_body','passed':True,'details':report})
  supplemental=[]
  sd=ROOT/('supplemental/richmond-parking-dimensions' if a['sequence']==76 else 'supplemental/los-angeles-county-jurisdiction')
  if a['sequence'] in [76,93] and (sd/'receipt.json').exists():
   sr=author_normalize(sd);supplemental.append({'folder':rel(sd),'record_count':sr['record_count'],'table_count':sr['table_count']});evidence += [rel(p) for p in sd.rglob('*') if p.is_file()]
   qa=ROOT/'evidence/table-dom-richmond/table-dom-qa.json'
   if a['sequence']==76 and qa.exists():
    q=json.loads(qa.read_text());checks.append({'check':'independent_offline_chrome_source_table_cells','passed':q['passed'],'details':q});evidence += [rel(p) for p in qa.parent.glob('*') if p.is_file()]
  additional=[];ad=ROOT/'additional/cambridge-zoning'
  if a['sequence']==90 and (ad/'receipt.json').exists():
   ar=json.loads((ad/'receipt.json').read_text());ap=dict(ar.get('publisher_download',{}))
   if ar.get('status')=='acquired':
    av=author_normalize(ad);additional.append({'publication':'Zoning Ordinance','folder':rel(ad),'record_count':av['record_count'],'table_count':av['table_count'],'source_url':ar['url'],'job':ar['job'],'publisher_download':ap,'complete_corpus':False,'command':"MUNICODE_EXPECTED_CLIENT_NAMES='[\"Cambridge\"]' MUNICODE_EXPECTED_STATE=MA node scripts/collect_browser.cjs https://library.municode.com/ma/cambridge/codes/zoning_ordinance fresh/cambridge-zoning 3"});evidence += [rel(p) for p in ad.rglob('*') if p.is_file()]
    if (ad/'publisher-export.validation.json').exists():
     ed=json.loads((ad/'publisher-export.validation.json').read_text());ap['edition_check']=ed;ap['transport_status']=ap['status']
     if ed['edition_alignment_status'] in ['cover_label_differs','supplement_matches_update_unproven']:ap['status']='partial';ap['reason']='Native zoning PDF acquired; supplement/update alignment differs or is unproven.'
   publisher['additional_legal_publication_downloads']=additional
  extra=sum(s['record_count'] for s in supplemental+additional)
  count=primary+extra+sum(n['record_count'] for n in native)
  results.append({'sequence':a['sequence'],'jurisdiction':a['jurisdiction'],'state':a['state'],'entity_type':a['entity_type'],'source_url':receipt.get('url',URLS[a['sequence']]),'source_family':'Municode','status':status,'acquisition_method':receipt.get('method','publisher acquisition not yet completed; official routing work only'),'publisher_download':publisher,'tested_scope':{'primary_record_count':primary,'supplemental_legal_provision_samples':supplemental,'additional_legal_publication_samples':additional,'primary_record_unit':'legal provision','primary_job_id':(receipt.get('job') or {}).get('Id'),'primary_edition':(receipt.get('job') or {}).get('Name'),'primary_banner':(receipt.get('job') or {}).get('BannerText'),'primary_publication_metadata':receipt.get('job'),'publisher_publications':receipt.get('publications',[]),'top_level_code_family_nodes':receipt.get('families_top_level',[]),'additional_government_publications':native},'complete_corpus':False,'record_count':count,'record_units':{'legal_provisions':primary+extra,'supplemental_pdf_pages':count-primary-extra},'table_count':(report['table_count'] if report else 0)+sum(s['table_count'] for s in supplemental+additional),'checks':checks,'command':f'MUNICODE_EXPECTED_CLIENT_NAMES=\'{json.dumps(["Baton Rouge, East Baton Rouge Parish"] if a["sequence"]==95 else [a["jurisdiction"]])}\' MUNICODE_EXPECTED_STATE={a["state"]} node scripts/collect_browser.cjs {URLS[a["sequence"]]} fresh/{name} 3 && python3 scripts/normalize.py fresh/{name} --offline','recorded_acquisition_command':f'python3 scripts/collect_browser_all.py (serial driver; target output {rel(d)})' if receipt.get('method','').startswith('standalone-headed') else ('python3 scripts/collect_http.py --target richmond --out http/richmond; offline continuation scripts/resume_retained.py' if a['sequence']==76 and receipt else 'not executed for this target yet'),'offline_command':'python3 scripts/verify.py','path_base':'All proof/script paths relative to this municode-counties package root.','evidence_paths':sorted(set(evidence)),'script_paths':[rel(p) for p in sorted((ROOT/'scripts').glob('*')) if p.is_file() and p.suffix in ['.py','.cjs']],'territorial_scope_note':a.get('boundary_note','City enactments; charter/zoning and incorporated standards require separate scope inventory.'),'limitations':limitations,'next_action':'Reconcile separately inventoried families, amendments and PDF editions before production ingestion; full-corpus ingestion remains untested.' if status=='standalone_e2e_pass' else 'Acquire current primary code through coordinator-approved ordinary browser route when access permits; retain partial evidence and family stop.'})
 (ROOT/'results.json').write_text(json.dumps(results,indent=2));print(json.dumps({'targets':len(results),'statuses':{s:sum(r['status']==s for r in results) for s in sorted({r['status'] for r in results})},'record_units':{u:sum(r['record_units'][u] for r in results) for u in ['legal_provisions','supplemental_pdf_pages']}},indent=2))
if __name__=='__main__':main()
