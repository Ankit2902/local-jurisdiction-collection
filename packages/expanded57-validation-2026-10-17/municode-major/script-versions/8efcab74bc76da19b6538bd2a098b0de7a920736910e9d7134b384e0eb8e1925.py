"""Offline normalization, evidence integrity verification and assignment-accurate handoff."""
import argparse,json,hashlib,platform,sys
from pathlib import Path
from normalize import normalize
from native_samples import run as native_replay
from collect_all import URLS
ROOT=Path(__file__).resolve().parents[1]
FAMILIES={
'Fresno':{'families':['Municipal Code with Charter','Chapter15 Citywide Development Code'],'evidence':['evidence/routes/fresno.html'],'additional_scope':'Charter/development provisions inventoried, not independently sampled as complete families.'},
'Atlanta':{'families':['Charter and related laws','Code of ordinances','Land development/subdivision/zoning Parts15/16'],'evidence':['evidence/routes/atlanta.html'],'additional_scope':'Official city route HTTP403; inventory supported by live publisher TOC when acquired.'},
'Kansas City':{'families':['Code of Ordinances VolumesI/II','Charter','Separate Zoning and Development Code product14867/pub945 (Chapter88); PDFenabled'],'evidence':['evidence/routes/kansas-city.html'],'additional_scope':'Live ClientContent confirms separate Zoning and Development Code publication14867/pub945; its download is enabled. Primary general-code sample does not cover this second publication.'},
'Mesa':{'families':['Code of Ordinances','Title11 Zoning Ordinance','Subdivision regulations','City Charter'],'evidence':['evidence/routes/mesa.html'],'additional_scope':'Official routing page HTTP403; publisher inventory used if acquired.'},
'Raleigh':{'families':['City Code including DivisionI Charter','Part10 UDO in Municode','New standalone UDO site'],'evidence':['evidence/routes/raleigh.html','evidence/routes/raleigh-udo.html'],'additional_scope':'New official UDO at https://udo.raleighnc.gov/ is separately routed; no claim Municode Part10 is current/full substitute.'},
'Miami':{'families':['Code of Ordinances','City Charter','Miami21 zoning code on Gridics CodeHUB'],'evidence':['evidence/routes/miami.html'],'additional_scope':'City page blocked in standaloneHTTP; official indexed page confirms Miami21, current planning route https://www.miami.gov/My-Government/Departments/Planning points to CodeHUB https://codehub.gridics.com/us/fl/miami . Miami21 acquisition not validated here.'},
'Omaha':{'families':['Municipal Code and Charter','Chapter53 Subdivisions','Chapter55 Zoning'],'evidence':[],'additional_scope':'Bounded primary sample only; full publisher TOC used to inventory code and charter.'},
'Virginia Beach':{'families':['CityCode','Charter (Virginia LIS controls discrepancies)','AppendicesA-J development ordinances','AppendixA1 Oceanfront Resort District Form-Based Code'],'evidence':['evidence/routes/virginia-beach.html'],'additional_scope':'Independent city; official route lists appendices and controlling Charter https://law.lis.virginia.gov/charters/virginia-beach/ . No full appendix or LIS charter acquisition claim.'},
'Long Beach':{'families':['Municipal Code','City Charter','Title20 Subdivisions','Title21 Zoning Regulations','Title22 Transitional Zoning Code'],'evidence':['evidence/routes/long-beach.html'],'additional_scope':'Official zoning page also links specific plans/design guidelines; these supplemental instruments remain outside bounded sample.'},
'Tulsa':{'families':['Revised ordinances including1989 Amended Charter','Separate Tulsa Zoning Code PDF','Separate Metropolitan Area Subdivision and Development Regulations PDF'],'evidence':['evidence/routes/tulsa.html','evidence/routes/tulsa-zoning.html'],'additional_scope':'Both separate native PDFs acquired in full; bounded pages normalized. PDF table extraction produces fragments and omits some row labels; retain original PDF.'},
'Aurora':{'families':['Code of Ordinances','City Charter','Unified Development Ordinance Chapter146 and separate https://aurora.municipal.codes/ viewer'],'evidence':['evidence/routes/aurora.html'],'additional_scope':'Official routing page links https://aurora.municipal.codes/ for the Unified Development Ordinance. This separate publisher route and linked instruments are not comprehensively acquired.'},
'Wichita':{'families':['Code of Ordinances','Wichita-Sedgwick County Unified Zoning Code','Metropolitan subdivision regulations'],'evidence':['evidence/routes/wichita.html'],'additional_scope':'Separate joint city/county UZC at https://library.municode.com/ks/wichita-sedgwick_county_unified/codes/unified_zoning_code and city planning documents require additional acquisition. Primary citycode sample does not cover joint code.'},
'New Orleans':{'families':['Code of Ordinances','Home Rule Charter','Separate Comprehensive Zoning Ordinance'],'evidence':['native/new-orleans-czo/source.html','evidence/routes/new-orleans-czo.html'],'additional_scope':'Full nativeCZO HTML retained; bounded13 substantive numbered sections including table normalized. CZO text is separate from primary general municipal code.'}}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(ROOT))
def main(offline=False):
 results=[]
 if offline:
  for name in ['new-orleans-czo','tulsa-zoning','tulsa-subdivision']:native_replay(name,True)
 for a in json.loads((ROOT/'assignment.json').read_text()):
  name=a['jurisdiction'].lower().replace(' ','-');d=ROOT/'browser'/name;recovery=ROOT/'recovery'/name;http=ROOT/'http'/name
  if (http/'receipt.json').exists():d=http
  if (recovery/'receipt.json').exists() and json.loads((recovery/'receipt.json').read_text()).get('status')=='acquired':d=recovery
  receipt=json.loads((d/'receipt.json').read_text()) if (d/'receipt.json').exists() else {}
  report=None;errors=[];checks=[]
  for rr in receipt.get('responses',[]):
   p=d/rr['file'];ok=p.exists() and sha(p)==rr['sha256'];checks.append({'check':'raw_response_sha256','path':rel(p),'passed':ok})
   if not ok:errors.append('Raw hash mismatch: '+rel(p))
  if (d/'samples.json').exists():
   try:report=normalize(d)
   except Exception as ex:errors.append(str(ex))
  primary_count=report.get('record_count',0) if report else 0
  native=[]
  for nn in (['tulsa-zoning','tulsa-subdivision'] if name=='tulsa' else ['new-orleans-czo'] if name=='new-orleans' else []):
   nd=ROOT/'native'/nn;vf=nd/'validation.json'
   if vf.exists():
    v=json.loads(vf.read_text());native.append({'name':nn,'validation':v,'evidence_path':rel(nd),'publisher_download_status':'passed','command':f'python3 scripts/native_samples.py --target {nn}','source_url':json.loads((nd/('source.html.receipt.json' if nn=='new-orleans-czo' else 'source.pdf.receipt.json')).read_text())['url']})
  count=primary_count+sum(x['validation']['record_count'] for x in native)
  status='standalone_e2e_pass' if primary_count>=3 and not errors else 'standalone_partial' if count else 'blocked' if receipt else 'untested'
  publisher=receipt.get('publisher_download',{'status':'not_tested','reason':'No completed primary publication-download check'})
  publisher['evidence_paths']=[rel(d/p) for p in ['receipt.json','client-content.json','pdf-url.json','publisher-export.receipt.json','publisher-export.pdf','publisher-export-response.bin','publisher-export-response.bin.receipt.json','publisher-export.validation.json'] if (d/p).exists()]
  if native:publisher['additional_families']=native
  paths=[rel(p) for p in d.rglob('*') if p.is_file()] if d.exists() else []
  if recovery==d:
   paths += [rel(p) for p in (ROOT/'browser'/name).rglob('*') if p.is_file()]
  interrupted=ROOT/'attempts'/(name+'-pre-rate-guard')
  if interrupted.exists():paths += [rel(p) for p in interrupted.rglob('*') if p.is_file()]
  for n in native:paths += [rel(p) for p in (ROOT/n['evidence_path']).rglob('*') if p.is_file()]
  family={**FAMILIES[a['jurisdiction']],'publisher_top_level_nodes':receipt.get('families_top_level',[]),'publisher_publications':receipt.get('publications',[]),'complete_inventory':False}
  script_evidence=[rel(p) for p in (ROOT/'script-versions').glob(receipt.get('script_sha256','missing')+'*') if p.is_file()]
  paths += script_evidence
  paths += [p for p in family['evidence'] if (ROOT/p).exists()]
  lim=['Bounded validation only; complete_corpus=false. Full table of contents is inventory, not downloaded full legal text.','Primary sample selects first three substantive leaf provisions, with a representative additional quality provision where recorded; it does not validate every code family or recent uncodified enactment.','Ordinary Chrome uses fresh context; no imported cookies, account login, fingerprint modifications, or challenge interaction.','Collector aborts image/font/media resources in later runs; linked illustrations and visual tables require separate acquisition.']
  if receipt.get('error'):lim.append('Retained acquisition error: '+receipt['error'])
  if interrupted.exists():lim.append('Initial bootstrap interrupted between completed targets to load3.5second rate guard; incomplete raw evidence retained under attempts.')
  if native:lim.append('Supplemental PDF records are explicitly page records, not inferred section records; detected PDF table fragments are not a fidelity-certified table dataset.')
  command=(f'python3 scripts/collect_http.py --target {name}' if d==http else f'python3 scripts/recover_bootstrap.py {name} && python3 scripts/publisher_download.py recovery/{name}' if d==recovery else f'node scripts/collect_browser.cjs {URLS[a["sequence"]]} browser/{name} 3 && python3 scripts/normalize.py browser/{name} --offline')
  results.append({'sequence':a['sequence'],'jurisdiction':a['jurisdiction'],'state':a['state'],'source_url':URLS[a['sequence']],'source_family':'Municode','executed_collector_sha256':receipt.get('script_sha256'),'script_version_evidence':script_evidence,'runtime':receipt.get('runtime') or {'node':receipt.get('node'),'browser':receipt.get('browser'),'os':receipt.get('os'),'architecture':receipt.get('architecture')},'status':status,'acquisition_method':receipt.get('method','not yet completed'),'publisher_download':publisher,'tested_scope':{'primary_leaf_records':primary_count,'primary_publication':receipt.get('product',{}).get('ProductName'),'job_id':receipt.get('job',{}).get('Id'),'inventory_nodes':receipt.get('inventory_nodes'),'supplemental':[{k:v for k,v in x.items() if k!='validation'}|{'record_count':x['validation']['record_count']} for x in native]},'complete_corpus':False,'record_count':count,'table_count':report.get('table_count',0) if report else 0,'supplemental_table_measures':{x['name']:x['validation'].get('sample_tables') for x in native},'checks':checks+([{'check':'normalized_identifiers_headings_nonempty_bodies','passed':True,'details':report}] if report else [])+[{'check':'normalization_errors','passed':not errors,'details':errors}],'command':command,'offline_command':'python3 scripts/build_results.py --offline','evidence_paths':sorted(set(paths)),'script_paths':['scripts/collect_browser.cjs','scripts/gate_cli.py','scripts/municode_shared.py','scripts/normalize.py','scripts/recover_bootstrap.py','scripts/native_samples.py','scripts/route_audit.py','scripts/collect_all.py','scripts/build_results.py','scripts/collect_http.py','scripts/publisher_download.py','scripts/validate_downloads.py','scripts/verify_package.py','scripts/quality_candidates.py','scripts/quality_sample.py'],'code_family_inventory':family,'limitations':lim,'next_action':'Resolve and separately acquire additional inventoried families, test table-bearing primary sections, and check uncodified ordinance currency before any complete-jurisdiction claim.'})
 (ROOT/'results.json').write_text(json.dumps(results,indent=2));(ROOT/'code-families.json').write_text(json.dumps({r['jurisdiction']:r['code_family_inventory'] for r in results},indent=2))
 print(json.dumps({'assignments':len(results),'statuses':{s:sum(r['status']==s for r in results) for s in sorted({r['status'] for r in results})},'record_count':sum(r['record_count'] for r in results)},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true');main(p.parse_args().offline)
