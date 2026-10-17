"""Build conservative per-target results from retained receipts; no network."""
import hashlib,json,re
from pathlib import Path
from run_all import SLUGS,slug
from normalize import normalize
ROOT=Path(__file__).resolve().parent
EXTRA={
 1:['Charter and appendices are embedded top-level families. Other adopted building codes and external technical material are not closed by this sample.'],
 3:['San Antonio Unified Development Code and other separately listed code families require separate acquisition/validation.'],
 6:['Consolidated city/county code applicability remains distinct; beach municipalities and Baldwin are excluded from this target. Charter and zoning families require closure.'],
 7:['Official routing identifies Title25 Land Development and Title30 Austin/Travis County Subdivision Regulations. Current ClientContent separately lists Land Development Code and10 technical/manual publications in addition to Code of Ordinances; all remain outside primary sampled scope.'],
 8:['Charlotte Unified Development Ordinance is a separately maintained development source; primary Code of Ordinances samples do not close UDO coverage.'],
 9:['Code and charter/development families and external referenced standards require separate closure.'],
 10:['Consolidated Indianapolis/Marion County code is one target; excluded municipalities remain distinct. Development/zoning and charter coverage require closure.'],
 11:['Metropolitan Nashville/Davidson is one consolidated target; charter, zoning and other families require separate closure.'],
 12:['Charter, zoning/development and externally adopted standards require separate family inventory closure.'],
 13:['Title 20 Zoning and other unsampled embedded or separately published families remain outside the provision sample.'],
 14:['Official city routing also identifies a Zoning Code route; title/development publications require separate closure.'],
 16:['Detroit charter and zoning/development families require separate closure beyond the primary code sample.'],
 19:['Memphis/Shelby County Unified Development Code and charter are additional families requiring separate source validation.']}
def rel(p):return str(p.relative_to(ROOT))
def main():
 results=[];inventory=[]
 for row in json.loads((ROOT/'assignment.json').read_text()):
  name=slug(row);folder=ROOT/'samples'/name
  if row['sequence']==1 and (ROOT/'samples/houston-v2/receipt.json').exists():folder=ROOT/'samples/houston-v2'
  receipt=json.loads((folder/'receipt.json').read_text()) if (folder/'receipt.json').exists() else {}
  report={};parser_error=None
  if (folder/'samples.json').exists():
   try:report=normalize(folder)
   except Exception as e:parser_error=str(e)
  primary_publication=next((pub for pub in receipt.get('publications',[]) if pub.get('productId')==receipt.get('product',{}).get('ProductID')),{});primary_count=report.get('record_count',0);count=primary_count;supreport={};supplemental=[]
  if row['sequence']==1 and (ROOT/'supplemental/houston-parking/table-dom-qa.json').exists():
   supfolder=ROOT/'supplemental/houston-parking';qa=json.loads((supfolder/'table-dom-qa.json').read_text());supreport=normalize(supfolder);count+=supreport['record_count'];supplemental=[{'folder':rel(supfolder),'node_id':'COOR_CH26PA_ARTVIIIOREPALO_DIV2REPASPBISP_S26-492PASPCETYUSCL','heading':'Sec. 26-492. - Parking spaces for certain types of use classifications.','record_count':supreport['record_count'],'table_count':supreport['table_count'],'table_rows':qa['row_count'],'table_cells':qa['cell_count'],'independent_dom_comparison_passed':qa['passed']}]
  ok=receipt.get('status')=='acquired' and count>=2
  status='standalone_e2e_pass' if ok else ('standalone_partial' if count or receipt.get('responses') else ('blocked' if receipt else 'untested'))
  pd=receipt.get('publisher_download',{'status':'not_tested','reason':'Acquisition did not reach publisher download eligibility inventory'})
  if row['sequence']==1 and pd.get('status')=='passed':pd={**pd,'currency_comparison':{'online_api_job':'Supplement 93 Update 2, codified through Ordinance 2026-0732 adopted August 19, 2026','pdf_first_cover':'Supplement 92, August 2026, through Ordinance 2026-0650 adopted July 22, 2026','alignment':'First-cover/API discrepancy; latest-online-edition equivalence not established','pdf_pages':2702}}
  if pd.get('publication_id'):pd={**pd,'resolver_url':'https://library.municode.com/api/PublicationPdfDownload/'+str(pd['publication_id']),'download_url_temporary':True}
  pd={**pd,'evidence_paths':[rel(p) for p in [folder/'client-content.json',folder/'pdf-url.json',folder/'publisher-export.receipt.json',folder/'publisher-export.pdf',folder/'publisher-export-response.bin',folder/'publisher-pdf-inspection.json',folder/'publisher-pdf-page1.png'] if p.exists()]}
  checks=['Complete jurisdiction corpus not asserted','Source method does not require Codex/CUA or an imported user browser profile']
  if count:checks+=['Exact requested API document identifiers present and unique','Nonempty legal body and heading retained','Original legal HTML retained with normalized text, links, notes and footnotes','JSONL/CSV counts and SHA256 outputs verified offline']
  if report.get('table_count',0):checks+=['HTML table cell text and rowspan/colspan attributes retained; nested/complex table semantics remain limited']
  if parser_error:checks.append('Parser failed: '+parser_error)
  evidence=[rel(p) for p in [folder/'receipt.json',folder/'executed-collect_browser.cjs',folder/'executed-gate_cli.py',folder/'samples.json',folder/'toc-full.json',folder/'product.json',folder/'job.json',folder/'rendered.html',folder/'rendered.png',folder/'failure.html',folder/'failure.png',folder/'normalized/sections.jsonl',folder/'normalized/sections.csv',folder/'normalized/verification.json'] if p.exists()]
  official=ROOT/'raw'/name/'official.html'
  if row['sequence'] in [8,11,12,19]:evidence.append('source-discovery-notes.json')
  if row['sequence'] in [8,19]:
   prefix='charlotte' if row['sequence']==8 else 'memphis'
   evidence += [rel(f) for folder in (ROOT/'raw/families').glob(prefix+'*') for f in folder.rglob('*') if f.is_file()]
  if supplemental:evidence += [rel(p) for p in (ROOT/supplemental[0]['folder']).rglob('*') if p.is_file()]
  if official.exists():evidence += [rel(official),rel(official.with_name(official.name+'.receipt.json'))]
  evidence=list(dict.fromkeys(['runtime-environment.json','gate-change.json']+evidence+pd.get('evidence_paths',[])+[rel(folder/r['file']) for r in receipt.get('responses',[])]))
  limitations=['Bounded selected provisions only; full TOC inventory is not full-text acquisition','Uncodified legislation, historical versions and external referenced standards not validated','Images/fonts/media omitted by current browser acquisition; legal illustrations/maps not qualified','Table/cross-reference quality applies only to retained selected provisions']+EXTRA.get(row['sequence'],[])
  if primary_publication.get('newOrdCount'):limitations.append(str(primary_publication['newOrdCount'])+' adopted uncodified ordinances are reported by publisher for the primary code and remain outside this sample')
  if receipt.get('error'):limitations.append('Retained acquisition error: '+receipt['error'])
  if not ok:limitations.append('No complete successful bounded live acquisition-to-normalized-output chain demonstrated for this target')
  result={'sequence':row['sequence'],'jurisdiction':row['jurisdiction'],'state':row['state'],'source_url':receipt.get('url',f"https://library.municode.com/{row['state'].lower()}/{SLUGS[row['sequence']]}/codes/code_of_ordinances"),'source_family':'Municode','status':status,'acquisition_method':receipt.get('method','not_tested'),'publisher_download':pd,'tested_scope':{'primary_record_count':primary_count,'supplemental_legal_samples':supplemental,'selection':'First up to three substantive section-shaped leaves of primary publication; charter leaves excluded when non-charter provisions available','selected_nodes':receipt.get('selected_nodes',[]),'product_id':receipt.get('product',{}).get('ProductID'),'job_id':receipt.get('job',{}).get('Id'),'edition_name':receipt.get('job',{}).get('Name'),'online_edition_date':receipt.get('job',{}).get('OnlineDate'),'codification_banner':receipt.get('job',{}).get('BannerText'),'uncodified_ordinance_count_reported':primary_publication.get('newOrdCount'),'toc_inventory_nodes':receipt.get('inventory_nodes'),'acquisition_started_at':receipt.get('started_at'),'acquisition_finished_at':receipt.get('finished_at')},'complete_corpus':False,'record_count':count,'table_count':report.get('table_count',0)+supreport.get('table_count',0),'checks':checks,'command':f"node collect_browser.cjs '{receipt.get('url','https://library.municode.com/'+row['state'].lower()+'/'+SLUGS[row['sequence']]+'/codes/code_of_ordinances')}' '{rel(folder)}' 3 && python3 normalize.py '{rel(folder)}' --offline",'evidence_paths':evidence,'script_paths':['collect_browser.cjs','gate_cli.py','municode_shared.py','normalize.py','run_all.py','verify.py','acquire_node.cjs','normalize_supplemental.py','verify_table.cjs','inspect_pdf.py','test_rate_gate.py'],'limitations':limitations,'next_action':'Close separate/embedded legal families and test representative complex tables/images before any complete-corpus collection claim' if ok else 'Use retained failure evidence to resolve current source/access route, then rerun bounded acquisition and parser with new output directory'}
  result['rerun_command']=f"node collect_browser.cjs '{result['source_url']}' 'samples/new-live-{name}' 3 && python3 normalize.py 'samples/new-live-{name}' --offline"
  result['rerun_note']='Choose a fresh output directory for every live acquisition; existing receipts are protected from overwrite'
  results.append(result)
  inventory.append({'sequence':row['sequence'],'jurisdiction':row['jurisdiction'],'primary':result['source_url'],'publisher_publications':receipt.get('publications',[]),'top_level_inventory':receipt.get('families_top_level',[]),'family_gaps':EXTRA.get(row['sequence'],[]),'family_inventory_complete':False})
 (ROOT/'results.json').write_text(json.dumps(results,indent=2));(ROOT/'scope-inventory.json').write_text(json.dumps(inventory,indent=2));print(json.dumps({'targets':len(results),'statuses':{s:sum(r['status']==s for r in results) for s in sorted({r['status'] for r in results})},'records':sum(r['record_count'] for r in results),'publisher_downloads':sum(r['publisher_download']['status']=='passed' for r in results)}))
if __name__=='__main__':main()
