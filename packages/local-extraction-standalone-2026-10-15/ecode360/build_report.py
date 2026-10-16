#!/usr/bin/env python3
"""Rebuild the qualification index from retained evidence (does not fetch sources)."""
from pathlib import Path
import ecode360 as e
ROOT=Path(__file__).resolve().parent

def evidence(path):
 p=ROOT/path
 return {'path':path,'sha256':e.digest(p.read_bytes()),'bytes':p.stat().st_size}

def main():
 historical={r['slug']:r for r in e.load(ROOT/'evidence/historical-fixtures.json')}
 browser={r['slug']:r for r in e.load(ROOT/'evidence/live-browser/baseline12-observations.json')}
 official={r['slug']:r for r in e.load(ROOT/'evidence/official-routing/results.json')}
 http={r['slug']:r for r in e.load(ROOT/'evidence/live-http/probe-results.json')}
 rows=[]
 for route in e.load(ROOT/'routes.json'):
  slug=route['slug'];h=historical[slug];b=browser[slug];o=official[slug];t=http[slug]
  candidate=e.load(ROOT/'fixtures/historical'/slug/'toc-candidate.json')
  report=e.load(ROOT/'examples'/slug/'validation-report.json')
  files=['fixtures/historical/'+slug+'/'+n for n in ['chapter.html','inventory.json','artifacts.json','origin.json','toc-candidate.json']]
  files+=['examples/'+slug+'/'+n for n in ['validation-report.json','aggregate-fulltext.csv','record-provenance.jsonl','node-dispositions.jsonl']]
  if o.get('raw_path'):files+=[o['raw_path']]
  receipt='evidence/live-http/'+slug+'/receipt.json';files+=[receipt]
  if t.get('raw_path'):files+=['evidence/live-http/'+slug+'/'+t['raw_path']]
  currentness='official_ecode_link_verified' if b['current_official_route_verified'] else ('legacy_official_link_redirect_unreconciled' if slug=='half-moon-bay-ca' else 'unverified')
  rows.append({'slug':slug,'jurisdiction':route['jurisdiction'],'checked_on':'2026-10-15','mapped_url':route['discovery_url'],
   'route_verified':True,'route_evidence_kind':'current supported public browser DOM attributes/title; not full DOM archive',
   'official_route_currentness':currentness,'official_ecode_route_verified':b['current_official_route_verified'],
   'official_page_check':o,'ordinary_http':{'status':t['http_status'],'route_verified':False,'receipt':receipt,'blocked':True},
   'current_browser':b,'current_representative_text_verified':b['representative_text_verified'],
   'parser_verified':True,'parser_validation_scope':'retained historical chapter DOM only'+('; additionally one exact current DOM section excerpt' if slug=='santa-monica-ca' else ''),
   'historical_fixture':{**h,'version':e.load(ROOT/'fixtures/historical'/slug/'inventory.json')['identity'],'original_retrieval_time_known':False,'pilot_context_date':'2026-08-28','replayed_on':'2026-10-15','currentness_verified':False,'observed_navigation_nodes':len(candidate['nodes']),'included_records':report['included_record_count'],'unresolved_nodes':report['unresolved_node_count'],'errors':report['errors']},
   'inventory_verified':False,'inventory_validation_scope':'bounded on-page TOC candidate only; full publication families/hierarchy not independently reconciled',
   'full_collection_verified':False,'release_eligible':False,'evidence':[evidence(f) for f in files]})
 tests=(ROOT/'evidence/tests.txt').read_text()
 if 'Ran 22 tests' not in tests or not tests.rstrip().endswith('OK'):raise RuntimeError('final test log does not show22 passing')
 report={'schema_version':1,'family':'ecode360','created_at':e.now(),'validation_date':'2026-10-15','package_status':'completed portable method-validation package; production/full-inventory qualification incomplete',
  'parser_version':e.VERSION,'parser_sha256':e.digest((ROOT/'ecode360.py').read_bytes()),'python_runtime_tested':'3.9','requirements':evidence('requirements.txt'),
  'summary':{'baseline_jurisdictions':12,'current_publisher_route_identities_verified':12,'current_official_municipal_ecode_links_verified':3,'retained_real_historical_DOM_parser_verified':12,'historical_records':115,'current_representative_text_observed':4,'current_exact_section_DOM_excerpts_parser_verified':1,'inventory_verified':0,'full_collection_verified':0,'additional_current_routes_observed':1,'offline_fixture_records_including_current_excerpt':116,'tests_passed':22,'tests_failed':0},
  'validation_definitions':{'route_verified':'publisher route rendered exact jurisdiction/customer/code/date identity during bounded browser check; independent official-route currentness is separate','parser_verified':'all expected source node/body pairs in a bounded retained DOM fixture emitted and passed tests; does not establish current/full-publication coverage','inventory_verified':'independent complete version-bound publication/family inventory reconciled; not achieved here','full_collection_verified':'complete inventory/acquisition/semantic review/end-version reconciliation achieved; not attempted here'},
  'tests':{'command':'python -m unittest -v test_ecode360.py','passed':22,'failed':0,'evidence':evidence('evidence/tests.txt'),'offline_replay_command':'python validate_local.py --out replay-check','executed_offline_report':evidence('examples/offline-validation.json'),'coverage':['distinct source nodes with repeated printed citations','same node repeated across artifacts deduplicated with all origins','parent own and unnumbered operative bodies','exact body association and navigation exclusion','merged tables, nested native/eCode lists, sup/sub, images/order, history','version/strict publication scope/challenge/raw hash refusal','resume identical deterministic content and parser-file/inventory/source binding','partial inventory publication refusal','all12 retained real chapter DOMs and1 exact current section DOM excerpt']},
  'historical_count_reconciliation':{'source_counts':{s:h['node_count'] for s,h in historical.items()},'sum':115,'initial_test_literal':123,'resolution':'Initial123 was a handwritten summation error. Exact per-source TOC/body identities reconcile115; no nodes or bodies removed. Current excerpt contributes a separate1 record.'},
  'jurisdictions':rows,'additional_current_route':e.load(ROOT/'evidence/live-browser/additional-foster-city-observation.json'),
  'common_evidence':[evidence(f) for f in ['routes.json','evidence/historical-fixtures.json','evidence/live-browser/baseline12-observations.json','evidence/live-browser/additional-foster-city-observation.json','fixtures/current-santa-monica/capture.json','fixtures/current-santa-monica/header-excerpt.html','fixtures/current-santa-monica/body-excerpt.html','fixtures/current-santa-monica/wrapped-excerpt.html','examples/current-santa-monica/validation-report.json']],
  'limitations':['No full corpus collection/import was performed. All inventories and exports remain validation samples; release is disabled.','Current public HTTP requests returned403 for all12 roots; supported IAB rendered root identities but several legal child routes still challenged. No challenge/access-control bypass was attempted.','Only Burlingame, Malibu and SantaMonica official city eCode links independently verified. HalfMoonBay official legacy CodePublishing redirect unresolved; seven official-page requests403 and ssf.gov attempted URL unverified/DNS failure.','Current browser root/body counts are retained derived DOM observations, not saved full DOM evidence. Current SantaMonica header/body are exact small subtree excerpts with an explicitly assembled wrapper. No full-document/complete-chapter claim is made for this fixture.','Raw historical source capture times unavailable; historical pilot context2026-08-28 and replay date2026-10-15 do not prove currentness.','Several mapped routes begin at Title1, not a publication root. Complete charters/code families, lazy trees, attachments/amendments and scope remain to review.','Native semantic markup and ordered image sidecars retained. Diagram transcription and broad rendered-source human comparisons remain outstanding.','No real source repeated-number multi-publication comparison was completed; synthetic collision regression and observed Sunnyvale Charter family are separate evidence.','Python3.9 originating runtime uses LibreSSL and emitted urllib3 compatibility warning; supported Python/OpenSSL deployment recommended.'],
  'next_actions':['Resolve official route currentness; review complete publication families and all scope exclusions.','Obtain supported ordinary access or authorized official exports for challenged legal routes.','Freeze independent complete inventory with source-node parent/order/classification evidence.','Perform separately authorized full collection with every-node disposition/provenance reconciliation and start/end version comparison.','Complete source-sensitive human review for complex formatting/images/repeated citations and add separate production release attestation.']}
 e.dump(ROOT/'VALIDATION-REPORT.json',report)
 manifest={str(p.relative_to(ROOT)):e.digest(p.read_bytes()) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='BUNDLE-MANIFEST.json' and '__pycache__' not in p.parts and '.venv' not in p.parts and '.DS_Store' not in p.parts}
 e.dump(ROOT/'BUNDLE-MANIFEST.json',{'created_at':e.now(),'algorithm':'sha256','excludes':['BUNDLE-MANIFEST.json','__pycache__','.venv','.DS_Store'],'sha256':manifest})
 print('Wrote report and manifest for',len(rows),'jurisdictions;',len(manifest),'files')
if __name__=='__main__':main()
