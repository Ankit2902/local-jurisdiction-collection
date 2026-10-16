#!/usr/bin/env python3
"""Seal final, completed live runs and their explicit remaining semantic gates."""
import hashlib,json,re
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def main():
 tests=(ROOT/'final-test-results-v2.txt').read_text()
 if not re.search(r'Ran 20 tests in .*?\n\nOK\s*$',tests,re.S):raise ValueError('Final20-test suite has not completed successfully')
 names=['final-rockland-http-v2','final-portland-playwright-v2','final-portland-cua-v2'];runs=[]
 for name in names:
  run=ROOT/'live-e2e'/name;report=read(run/'E2E-VALIDATION.json')
  if report['live_acquisition_status']!='passed_bounded' or not report['inventory_recheck']['coherent']:raise ValueError('Live run not complete/coherent: '+name)
  for rel,digest in report['input_hashes'].items():
   if sha(run/rel)!=digest:raise ValueError('Live raw input changed: '+name+'/'+rel)
  for rel,digest in report['output_hashes'].items():
   if sha(run/rel)!=digest:raise ValueError('Live export changed: '+name+'/'+rel)
  for file,digest in report['code_hashes'].items():
   if sha(ROOT/file)!=digest:raise ValueError('Final live run used another script revision: '+file)
  runs.append({'run':name,'report_path':str((run/'E2E-VALIDATION.json').relative_to(ROOT)),'report_sha256':sha(run/'E2E-VALIDATION.json'),'live_status':report['live_acquisition_status'],'runtime':report['runtime'],'jurisdiction':report['jurisdiction'],'started_at':report['started_at'],'finished_at':report['finished_at'],'environment':report['environment'],'inventory_recheck':report['inventory_recheck'],'parse_integrity_status':'PASS','semantic_completion_status':'requires_review','records':report['validation']['record_count'],'unresolved_exceptions':report['validation']['unresolved_exception_count'],'commands':report['commands']})
 # The two Portland acquisition paths must produce the same ordered provisions.
 standalone=read(ROOT/'live-e2e/final-portland-playwright-v2/package/aggregate-fulltext.json')['provisions'];cua=read(ROOT/'live-e2e/final-portland-cua-v2/package/aggregate-fulltext.json')['provisions']
 if standalone!=cua:raise ValueError('Standalone and supported CUA ordered provisions differ')
 qa={
  'reviewer':'Codex agent visual comparison; not human signoff','source':'Fresh live acquired official PDFs, Poppler page renders and reviewed output render','selected_cases':[
   {'jurisdiction':'portland-me','pages':[37],'result':'selected_rent_table_semantic_headers_and_all_values_verified','recovery_id':'portland-p37-rent-columns'},
   {'jurisdiction':'portland-me','pages':[37,38],'result':'food_table_header_and_household1_to8_rows_merged_and_verified_once','recovery_id':'portland-p37-p38-food-continuation'},
   {'jurisdiction':'portland-me','pages':[48],'result':'readable_missing_line_transcribed; unknown_symbol_preserved_unresolved','recovery_id':'portland-p48-visible-line'},
   {'jurisdiction':'rockland-me','pages':[3],'result':'actual_Charter_locator_box_obscures_body; native_recovery_and_review_gate_retained'}],
  'recovery_config':{'path':'reviewed-recoveries.json','sha256':sha(ROOT/'reviewed-recoveries.json')},
  'evidence':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in sorted((ROOT/'live-e2e/qa').glob('*')) if p.suffix in ('.png','.pdf','.html')]}
 write(ROOT/'E2E-SOURCE-COMPARISON.json',qa)
 report={'phase':2,'generated_at':datetime.now(timezone.utc).isoformat(),'status':'fresh_bounded_live_acquisition_and_verified_exports_pass','corpus_complete':False,'semantic_complete':False,'live_runs':runs,'standalone_cua_ordered_provisions_equal':True,'tests':{'command':'python -m unittest -v test_civicplus test_e2e','count':20,'result':'PASS','path':'final-test-results-v2.txt','sha256':sha(ROOT/'final-test-results-v2.txt')},'frozen_code_hashes':{p.name:sha(p) for p in sorted(ROOT.glob('*')) if p.suffix in ('.py','.mjs')},'source_visual_comparison':'E2E-SOURCE-COMPARISON.json','fresh_probe_boundaries':{'portland_plain_requests':'Certificate chain verification failed with certifi and system CA bundle; retained failed-request receipts. Verified isolated Chrome is the qualified index transport. No ignore_https_errors or verify=False used.','rockland_http':'Current direct official index/PDF requests returned200. Earlier404 is historical, not a current blocker.','bundled_chromium_cross_platform':'Supported option/documented dependency, not live-qualified on other platforms.'},'remaining_gates':['Unreadable printed symbol on Portland p48; readable words recovered but intended character not guessed.','Other Portland table fragments/semantics outside the specifically reviewed cases.','Rockland Charter source locator boxes obscure legal text; native extraction retained but alternate source/human review required.','Microscopic Rockland heading glyphs and unnumbered-body classification.','Unacquired publications/documents and independent full legal-node coverage, coherent legal edition/currency, full-corpus completion.'],'historical_baseline':'Copied samples/ and prior VALIDATION-REPORT.json are retained baseline, not fresh live evidence.'}
 write(ROOT/'E2E-VALIDATION.json',report)
 for slug in ['portland-me','rockland-me']:
  city=ROOT/'live-e2e'/slug;city.mkdir(exist_ok=True);write(city/'E2E-VALIDATION.json',dict(report,live_runs=[r for r in runs if r['jurisdiction']==slug]))
 hashes={str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='E2E-ARTIFACT-HASHES.json'};write(ROOT/'E2E-ARTIFACT-HASHES.json',hashes)
 print(json.dumps({'final_live_runs':len(runs),'tests':20,'artifact_hashes':len(hashes),'semantic_complete':False}))
if __name__=='__main__':main()
