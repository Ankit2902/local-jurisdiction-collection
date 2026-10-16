"""Offline regeneration of delivered historical replay and bounded validation reports."""
import json
from pathlib import Path
from bs4 import BeautifulSoup
import cp_collect as cp

base=Path(__file__).resolve().parent
live=json.loads((base/'live-browser-observations.json').read_text())
summary=[]
for route in json.loads((base/'routes.json').read_text()):
    slug=route['slug'];d=base/slug
    observed=next(r for r in live['roots'] if r['slug']==slug)
    report=cp.replay(d/'historical/snapshot.json',d/'replay')
    s=json.loads((d/'historical/snapshot.json').read_text())
    p=s['pages'][0];raw=(d/'historical'/p['path']).read_bytes()
    dom=BeautifulSoup(raw,'html.parser')
    toc={a['href'].split('#')[-1] for a in dom.select('#mainContent .CiteTOC a[href]')}
    parsed=cp.parse_page(raw,p,s)
    identities={n['locator']['value'] for n in parsed['nodes'] if n['node_kind']=='section'}
    assert toc==identities
    # Chapter inventory links remain distinct from compatibility output TOC.
    navigation=cp.links((d/'historical/raw/toc.html').read_text(),s['navigation_evidence'][0]['url'],s['root_url'])
    cp.save(d/'historical/observed-title-links.json',{'coverage':'one retained title only','links':navigation,'inventory_complete':False})
    files={str(f.relative_to(base)):cp.digest(f.read_bytes()) for f in sorted(d.rglob('*')) if f.is_file() and f.name!='VALIDATION-REPORT.json'}
    files['live-browser-observations.json']=cp.digest((base/'live-browser-observations.json').read_bytes())
    files['test-results.txt']=cp.digest((base/'test-results.txt').read_bytes())
    result={'schema_version':1,'jurisdiction_slug':slug,'jurisdiction':route['jurisdiction'],
       'prepared_on':'2026-10-15','implementation_version':cp.VERSION,
       'status':'bounded_implementation_validation_only','production_ready':False,
       'current_route':observed,'current_publisher_currency_raw':observed.get('currency_raw'),
       'current_currency_assigned_to_historical_artifacts':False,
       'current_representative_text_validation':{'status':'passed_bounded_agent_DOM_comparison' if slug in ('renton-wa','flagstaff-az') else ('migration_confirmed_legacy_current_collection_disabled' if slug=='foster-city-ca' else 'not_performed'),
           'human_visual_review':False,'evidence_kind':'selected CUA DOM/AX observations; no whole-current-DOM claim'},
       'historical_parser_validation':report,
       'inventory_validation':{'historical_chapters_checked':1,'chapter_numbered_TOC_nodes':len(toc),
           'parsed_numbered_nodes':len(identities),'chapter_TOC_reconciled':toc==identities,
           'retained_title_observed_links':len(navigation),'current_root_observation_only':True,
           'whole_publication_inventory_complete':False,'scope_decisions_complete':False},
       'automated_tests':{'suite':'test_cp_collect.py','test_count':27,'passed':True,
           'evidence':'test-results.txt','coverage':'synthetic family-sensitive cases plus actual retained DOM for all seven'},
       'whole_corpus_validation':{'performed':False,'complete':False,'full_collection_run':False},
       'limitations':['No complete current independent publication inventory or coherent edition validation.',
           'Live browser source excerpts/observations are bounded; historical DOM is not current edition proof.',
           'Real difficult tables/images, all additional families and human visual QA remain unqualified.',
           'Direct HTTPS roots returned403; use ordinary supported browser route where needed.',
           'Browser driving remains operator-supported; package imports hash-bound rendered DOM and does not automate the browser.'],
       'evidence_sha256':files}
    if slug=='foster-city-ca':result['limitations'].append('Current municipal code migrated to eCode360 FO4449; Estero district family has separate unresolved scope.')
    if slug=='flagstaff-az':result['limitations'].append('Charter and Employee Handbook separately inventoried, not parsed; Title1 unlinked repealed node requires disposition in full inventory.')
    cp.save(d/'VALIDATION-REPORT.json',result)
    summary.append({'slug':slug,'historical_records':report['records'],'historical_source_nodes':report['source_nodes'],'route_status':observed['current_route_status'],'whole_corpus_complete':False})
cp.save(base/'VALIDATION-REPORT.json',{'schema_version':1,'status':'bounded_family_implementation_validated','test_count':27,
    'tests_passed':True,'historical_record_count':sum(r['historical_records'] for r in summary),'jurisdictions':summary,
    'whole_corpus_complete':False,'current_route_corrections':['Foster City municipal code migrated to eCode360 FO4449; Estero family unresolved.',
    'Fremont and San Carlos live roots use hashes; Foster City also uses frames.'],
    'report_paths':[r['slug']+'/VALIDATION-REPORT.json' for r in summary]})
files={str(f.relative_to(base)):cp.digest(f.read_bytes()) for f in sorted(base.rglob('*')) if f.is_file() and
       '__pycache__' not in f.parts and '.venv' not in f.parts and 'work' not in f.parts and f.name!='PACKAGE-SHA256.json'}
cp.save(base/'PACKAGE-SHA256.json',{'algorithm':'sha256','files':files})
print(json.dumps({'jurisdictions':len(summary),'historical_records':sum(r['historical_records'] for r in summary),'files_hashed':len(files)},indent=2))
