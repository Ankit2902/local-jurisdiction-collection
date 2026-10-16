"""One-time provenance-preserving fixture import; never used by portable tests or CLI."""
import json
import hashlib
import shutil
from bs4 import BeautifulSoup
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
for route in json.loads((HERE/'routes.json').read_text()):
    slug = route['slug']
    origin = PROJECT/'municipal-code-batch/cache/live-browser-snapshots/codepublishing'/slug
    receipt = PROJECT/'municipal-code-batch/validation/collector-completion/browser-vendors'/(slug+'.json')
    r = json.loads(receipt.read_text())
    target = HERE/slug/'historical'
    (target/'raw').mkdir(parents=True, exist_ok=True)
    artifacts = []
    for name in ('toc', 'section'):
        raw = (origin/(name+'.html')).read_bytes()
        (target/'raw'/(name+'.html')).write_bytes(raw)
        artifacts.append({'path':'raw/'+name+'.html','sha256': hashlib.sha256(raw).hexdigest(),
                          'origin_project_relative_path': str((origin/(name+'.html')).relative_to(PROJECT)),
                          'url':r['live_sample'][name+'_url'], 'historical_observation_date':'2026-08-28'})
    shutil.copyfile(receipt,target/'historical-collector-receipt.json')
    pubs = [{'publication_id':'city-code','title':route['jurisdiction']+(' City Code' if slug == 'flagstaff-az' else ' Municipal Code'),
             'scope_decision':'bounded historical sample only', 'scope_evidence':'historical-collector-receipt.json',
             'currency_raw': None, 'scope_status':'unresolved_full_inventory'}]
    if slug == 'flagstaff-az':
        pubs += [{'publication_id':p,'title':t,'scope_decision':'unresolved; must inventory separately',
                  'scope_evidence':'prior handoff identifies family; no raw family root retained', 'currency_raw':None}
                 for p,t in [('charter','Charter'),('employee-handbook','Employee Handbook')]]
    toc_heading = BeautifulSoup((origin/'toc.html').read_bytes(), 'html.parser').select_one('#mainContent h1')
    page = dict(artifacts[1], publication_id='city-code', content_selector='#mainContent',
                publisher_version=None, hierarchy={'title':toc_heading.get_text(' ', strip=True)} if toc_heading else {})
    snapshot = {'jurisdiction_slug':slug,'jurisdiction':route['jurisdiction'], 'root_url':route['discovery_url'],
                'snapshot_id':'retained-2026-08-28-'+artifacts[1]['sha256'][:16], 'retrieved_at':'2026-08-28',
                'coherent_publication_version':False, 'inventory_complete':False,
                'publications':pubs, 'pages':[page], 'navigation_evidence':artifacts[:1],
                'provenance_note':'Historical rendered DOM retained by earlier collector; date/URL from collector receipt. No fresh route or edition validation implied.'}
    (target/'snapshot.json').write_text(json.dumps(snapshot,indent=2))
    (target/'import-provenance.json').write_text(json.dumps(artifacts,indent=2))

    plan = {key:snapshot[key] for key in ('jurisdiction_slug','jurisdiction','root_url','snapshot_id','publications')}
    page['expected_heading_id'] = BeautifulSoup((origin/'section.html').read_bytes(), 'html.parser').select_one('#mainContent h3[id]')['id']
    snapshot['pages'][0] = page
    (target/'snapshot.json').write_text(json.dumps(snapshot,indent=2))
    planned = dict(page, navigation_evidence=artifacts[0], rendered_artifact={
        'path':page['path'], 'sha256':page['sha256'], 'rendered_url':page['url'], 'retrieved_at':'2026-08-28'})
    plan['pages'] = [planned]
    (target/'acquisition-plan.json').write_text(json.dumps(plan,indent=2))
