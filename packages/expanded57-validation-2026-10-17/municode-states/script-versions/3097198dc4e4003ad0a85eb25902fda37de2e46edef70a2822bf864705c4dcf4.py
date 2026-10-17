#!/usr/bin/env python3
import json,pathlib,sys,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def load(p,default=None):return json.loads(p.read_text()) if p.exists() else default
slug=lambda r:r['jurisdiction'].lower().replace(' ','_')+'-'+r['state'].lower()
PDF={'Jackson':'jackson-ms','Huntsville':'huntsville-al','Providence':'providence-ri','Cheyenne':'cheyenne-wy','Charleston':'charleston-wv'}
FAMILIES={41:['General municipal code','Separate official city Zoning Ordinance PDF; extra-territorial and subdivision documents not exhaustively inventoried'],44:['Municipal code includes Chapter134 Zoning and Chapter135 Planning and Design as individual TOC leaves; own bodies/attachments not sampled; current separate official compilations not qualified'],45:['Municipal code with Chapter36 Zoning; separately adopted amendments not exhaustively inventoried'],46:['Municipal code and charter tree to inventory','Separate current official city Zoning Ordinance PDF and zoning map PDF'],47:['Municode Code of Ordinances','Separate Municode Zoning publication','MuniDocs document repository not collected'],48:['Official city route links municipal code and charter using legacy-library query clientId=16075; current API identity resolved independently by organization endpoint','Separate zoning regulations require current authoritative source qualification'],49:['Municipal code','Official city zoning/ordinance routes; linked regulatory inventory not assumed exhaustive'],50:['Municipal code includes Chapter20 Land Development Code','City links 2026 Fargo LDC project; project materials are not proof of adopted replacement'],51:['Billings Montana City Code (BMCC)','Official annual ordinances and ordinance index separate; amendments not reconciled'],53:['Municipal code and city charter families to inventory','Subdivision regulations and zoning maps may require separate official files'],54:['Municipal code','Separate official Unified Development Code; official page says amended through2022, not qualified current'],55:['Municipal code and charter','Separate official city Zoning Ordinance PDF; recency unqualified']}
results=[]
for r in load(ROOT/'assignment.json'):
 key=slug(r);d=ROOT/'direct'/key;b=ROOT/'live'/key.replace('_','-');rec=load(d/'receipt.json',{});brec=load(b/'receipt.json',{})
 if rec.get('status')!='acquired' and brec.get('status')=='acquired':d=b;rec=brec
 norm=load(d/'normalized/verification.json',{});paths=[str(p.relative_to(ROOT)) for p in d.rglob('*') if p.is_file()] if d.exists() else []
 status='standalone_e2e_pass' if rec.get('status')=='acquired' and norm.get('record_count',0)>=2 else ('blocked' if rec or brec else 'untested')
 limitations=['Bounded sample only; full jurisdiction corpus, incorporated standards, pending ordinances, maps and supplemental families not collected or reconciled.','Current source versions are observed acquisition metadata, not independent proof of legal currentness.','Normalized CSV has core text fields; semantic HTML, table spans, links, lists and notes are retained in JSONL and raw API evidence.']
 if rec.get('error'):limitations.append('Direct/live acquisition: '+rec['error'])
 if brec.get('error'):limitations.append('Initial standalone browser attempt: '+brec['error'])
 pub=rec.get('publisher_download',{'status':'not_tested','reason':'No primary publication download completed'})
 inspection=load(d/'publisher-export-inspection.json',{})
 if inspection:
  pub['currency_alignment']=inspection.get('currency_alignment');pub['pdf_pages']=inspection.get('pdf_pages');pub['first_pages_supplement_number']=inspection.get('first_pages_supplement_number');pub['online_job_name']=inspection.get('online_job_name')
  if inspection.get('cover_version_mismatch'):limitations.append('Native PDF first pages show a different supplement number from current online API job. Later pages and update sheets not audited; PDF/API currency equivalence not established.')
 pub['evidence_paths']=[p for p in paths if any(x in p for x in ('client-content','publisher-export','pdf-url','receipt.json'))]
 altkey=PDF.get(r['jurisdiction']);alt=ROOT/'official-pdf'/str(altkey)
 # Charleston official PDF belongs only to WV.
 if r['jurisdiction']=='Charleston' and r['state']!='WV':alt=ROOT/'no-alternative'
 alternatives=[]
 if (alt/'source.pdf.receipt.json').exists():
  meta=load(alt/'source.pdf.receipt.json');rep=load(alt/'report.json',{});alternatives=[{'kind':'official-native-pdf','status':'passed' if meta.get('status')==200 else 'blocked','url':meta['url'],'reason':'Original official PDF; parse is bounded page records, not section reconstruction.','scope':rep.get('scope'),'pdf_pages':rep.get('pdf_pages'),'record_count':rep.get('record_count',0),'evidence_paths':[str(p.relative_to(ROOT)) for p in alt.iterdir() if p.is_file()]}]
  if status in ('blocked','untested') and rep.get('passed'):status='standalone_partial';limitations.append('Only official alternative PDF page records passed; primary municipal publication acquisition not qualified.')
 routepaths=[str(p.relative_to(ROOT)) for p in (ROOT/'routes').glob('*/*') if p.is_file() and (key.replace('_','-') in str(p) or (r['jurisdiction']=='Charleston' and r['state'].lower() in str(p)))]
 checks=norm.get('checks',[])
 quality=load(d/'quality.json',{})
 if quality:checks=checks+[{'name':'source_heading_table_and_full_attribute_cross_reference_checks','passed':quality.get('passed'),'evidence_path':str((d/'quality.json').relative_to(ROOT))}]
 supplemental=[]
 if r['sequence']==44:
  for sd in (ROOT/'supplemental').glob('des_moines*'):
   tr=load(sd/'table-verification.json',{})
   supplemental.append({'scope':tr.get('scope'),'table_count':tr.get('table_count',0),'table_QA_passed':tr.get('passed',False),'evidence_paths':[str(p.relative_to(ROOT)) for p in sd.rglob('*') if p.is_file()]})
  paths+=[p for item in supplemental for p in item['evidence_paths']]
 obj={'sequence':r['sequence'],'jurisdiction':r['jurisdiction'],'state':r['state'],'source_url':rec.get('url',r['source_lead_url']),'source_family':'Municode / official city source alternatives','status':status,'acquisition_method':rec.get('method','Standalone direct HTTP and ordinary headed browser attempt'),'acquisition_metadata':{k:rec.get(k) for k in ['started_at','finished_at','runtime','os','script_sha256']},'code_job':rec.get('job',{}),'final_normalization_phase':load(d/'final-normalization-phase.json',{}),'publisher_download':pub,'official_download_alternatives':alternatives,'publication_inventory':rec.get('publications',[]),'top_level_families':rec.get('families_top_level',[]),'supplemental_samples':supplemental,'additional_family_inventory_or_gaps':FAMILIES[r['sequence']],'tested_scope':{'selected_nodes':rec.get('selected_nodes',[]),'toc_nodes':rec.get('inventory_nodes'),'publisher_pdf':'Native export acquisition only if passed; not complete parsed corpus','official_alternatives':[a.get('scope') for a in alternatives]},'complete_corpus':False,'record_count':norm.get('record_count',0) or (sum(a['record_count'] for a in alternatives) if status=='standalone_partial' else 0),'primary_section_record_count':norm.get('record_count',0),'table_count':norm.get('table_count',0),'checks':checks,'command':f'python3 scripts/acquire.py --sequence {r["sequence"]} --out /tmp/municode-{key}-fresh','evidence_paths':paths+routepaths+[p for a in alternatives for p in a['evidence_paths']],'script_paths':['scripts/acquire.py','scripts/municode_shared.py','scripts/normalize.py','scripts/official_pdf.py','scripts/routes.py','scripts/run_browser.py','scripts/collect_browser.cjs','scripts/gate_cli.py','scripts/normalize_final.py','scripts/quality.py','scripts/table_sample.py','scripts/inspect_downloads.py','scripts/verify.py'],'limitations':limitations,'next_action':'Qualify additional publications and amendments, then define complete source-node dispositions before production collection.' if status=='standalone_e2e_pass' else 'Resolve retained transport/publication blocker; rerun bounded live command without retrying denied paths in a cooldown.'}
 results.append(obj)
(ROOT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'targets':len(results),'statuses':{s:sum(r['status']==s for r in results) for s in sorted(set(r['status'] for r in results))}},indent=2))
