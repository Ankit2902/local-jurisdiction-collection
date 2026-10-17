from pathlib import Path
import json, re, collections, hashlib, html

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
STATE_NAMES = dict(x.split(':',1) for x in 'AL:Alabama|AK:Alaska|AZ:Arizona|AR:Arkansas|CA:California|CO:Colorado|CT:Connecticut|DE:Delaware|FL:Florida|GA:Georgia|HI:Hawaii|ID:Idaho|IL:Illinois|IN:Indiana|IA:Iowa|KS:Kansas|KY:Kentucky|LA:Louisiana|ME:Maine|MD:Maryland|MA:Massachusetts|MI:Michigan|MN:Minnesota|MS:Mississippi|MO:Missouri|MT:Montana|NE:Nebraska|NV:Nevada|NH:New Hampshire|NJ:New Jersey|NM:New Mexico|NY:New York|NC:North Carolina|ND:North Dakota|OH:Ohio|OK:Oklahoma|OR:Oregon|PA:Pennsylvania|RI:Rhode Island|SC:South Carolina|SD:South Dakota|TN:Tennessee|TX:Texas|UT:Utah|VT:Vermont|VA:Virginia|WA:Washington|WV:West Virginia|WI:Wisconsin|WY:Wyoming|DC:District of Columbia'.split('|'))
ABBREV = {v:k for k,v in STATE_NAMES.items()}
baseline_path = ROOT/'official-source-update-scraping/config/local_jurisdiction_scope.json'
baseline = json.loads(baseline_path.read_text())['jurisdictions']
existing = {(x.get('name',x.get('jurisdiction')),x['state']) for x in baseline}
counts = collections.Counter(s for n,s in existing)
census = [x for x in json.loads((OUT/'census-city-rankings.json').read_text()) if x[0].isdigit()]
evidence = json.loads((OUT/'discovery-evidence-complete.json').read_text())
source_matches = { (s,n):k for line in (OUT/'source-selection.txt').read_text().splitlines() for s,n,k in [line.split('|')] }
aliases = {'Boise':'Boise City city', 'Indianapolis':'Indianapolis city (balance)', 'Louisville':'Louisville/Jefferson County metro government (balance)', 'Lexington':'Lexington-Fayette urban county', 'Nashville':'Nashville-Davidson metropolitan government (balance)', 'Anchorage':'Anchorage municipality', 'Baltimore City':'Baltimore city', 'New York City':'New York city', 'Saint Paul':'St. Paul city'}
display = {'Honolulu':'City and County of Honolulu','Anchorage':'Municipality of Anchorage','Indianapolis':'Indianapolis / Marion County','Louisville':'Louisville / Jefferson County Metro','Lexington':'Lexington-Fayette Urban County','Nashville':'Nashville-Davidson Metropolitan Government'}
special_notes = {
 'Honolulu':'Collect the City and County of Honolulu ordinances. Urban Honolulu CDP is a statistical area, not a separate municipal government. No CDP population is assigned to the county target.',
 'Indianapolis':'One consolidated city/county code target. Census population is Indianapolis city (balance), not the entire county. Excluded municipalities remain separate jurisdictions.',
 'Louisville':'One metro-government code target. Census population is the metro government balance, not the entire county. Do not count Louisville and Jefferson County as two additions.',
 'Nashville':'One metropolitan-government code target. Census population is the metropolitan government balance. Do not count Nashville and Davidson County twice.',
 'Lexington':'One urban-county government and code target. Do not count Lexington and Fayette County twice.',
 'Jacksonville':'One consolidated-government target. Retain city/county applicability distinctions; the separately incorporated beach municipalities and Baldwin are not additional targets here.',
 'Baton Rouge / East Baton Rouge Parish':'One combined city/parish code target. Preserve whether each provision applies to the city, parish, or an unincorporated area. City-only Census population is not assigned to this combined target.',
 'Baltimore City':'Independent city. Baltimore County is already in scope and does not substitute for Baltimore City.',
 'Miami':'The City of Miami is a separate municipal code target from already-scoped Miami-Dade County.',
 'St. Louis':'Independent city. This recommendation does not include St. Louis County.',
 'Virginia Beach':'Independent city. Do not model it as a subordinate municipality inside a county.',
 'Richmond':'Independent city in Virginia; distinct from already-scoped Richmond, California.',
 'Norfolk':'Independent city. Do not model it as a subordinate municipality inside a county.',
 'Portland':'Portland, Oregon. Already-scoped Portland, Maine is a different jurisdiction.',
 'Arlington':'City of Arlington, Texas. Distinct from the proposed Arlington County, Virginia.',
 'Charleston':'State-specific target; Charleston, South Carolina and Charleston, West Virginia are different jurisdictions.',
}
extra_reasons = {
 'Los Angeles County':'Adds county law alongside existing Los Angeles city coverage and the other scoped municipalities in the county.',
 'San Diego County':'Adds county law alongside existing San Diego city coverage.',
 'Clark County':'Adds the county code alongside Las Vegas and Henderson. These are separate code targets with different territorial applicability.',
 'Westchester County':'Adds a county-level target beyond the current New York City-only New York scope.',
 'Allegheny County':'Adds county law alongside existing Pittsburgh city coverage.',
 'Fairfax County':'Adds a Northern Virginia county jurisdiction alongside the proposed independent Virginia cities.',
 'Arlington County':'Adds a separate Northern Virginia county jurisdiction. It is not the City of Arlington, Texas.',
 'Cambridge':'Adds a separate municipality adjacent to Boston, giving the Massachusetts sample more than its largest city.',
 'Worcester':'Adds another large Massachusetts city beyond the Boston/Cambridge cluster.',
 'Hartford':'Adds Connecticut’s capital alongside Bridgeport and Stamford.',
 'Stamford':'Adds another substantial Connecticut municipality alongside Bridgeport and Hartford.',
 'Albany':'Adds New York’s capital alongside the upstate city targets, extending the existing New York City-only scope.',
 'Birmingham':'Adds a second substantial Alabama city alongside Huntsville.',
 'Savannah':'Adds an eastern Georgia city alongside Atlanta.',
 'Grand Rapids':'Adds a western Michigan city alongside Detroit.',
 'Overland Park':'Adds a Kansas-side Kansas City metropolitan jurisdiction alongside Wichita. Kansas City, Missouri cannot substitute for it.',
 'Eugene':'Adds a second Oregon city beyond Portland.',
 'Chattanooga':'Adds an eastern Tennessee city alongside Nashville and Memphis.',
 'Spokane':'Adds eastern Washington to a scope concentrated in western Washington.',
 'Tacoma':'Adds a major city missing from the existing western Washington cluster.',
 'Reno':'Adds northern Nevada alongside Las Vegas, Henderson and Clark County.',
 'Columbia':'Adds South Carolina’s capital alongside Charleston.',
 'Madison':'Adds Wisconsin’s capital alongside Milwaukee.',
 'Lincoln':'Adds Nebraska’s capital alongside Omaha.',
 'Buffalo':'Adds western New York to a scope currently limited to New York City.',
 'Rochester':'Adds another substantial upstate New York city.',
 'Baton Rouge / East Baton Rouge Parish':'Adds a combined city/parish code target in Louisiana beyond New Orleans.',
}
family_overrides = {'Houston':'Municode (official routing page)','Jacksonville':'Official code-routing page','Austin':'Municode (official routing page)','Charlotte':'Official code-routing page','Raleigh':'Official code-routing page','Miami':'Municode (official routing page)','Atlanta':'Official code-routing page','Las Vegas':'Municode (official routing page)','Cleveland':'American Legal (official routing page)','Cincinnati':'Official code-routing page','Fort Wayne':'American Legal (official routing page)','Lexington':'Municode (official routing page)','Reno':'Municode (official routing page)','Clark County':'Municode (official routing page)','Baton Rouge / East Baton Rouge Parish':'Municode (official routing page)','Bridgeport':'Official code-routing page','Jackson':'Official code-routing page','Burlington':'Code Publishing (official routing document)','Tacoma':'eCode360 (official routing page)','Madison':'Official code-routing page','Lincoln':'enCodePlus','Overland Park':'Municipal code portal'}

def pop_match(name,st):
    if name.endswith('County') or name in ['Honolulu','Baton Rouge / East Baton Rouge Parish']: return None
    target = aliases.get(name,name+' city')+', '+STATE_NAMES[st]
    matches = [r for r in census if r[1]==target]
    assert len(matches)==1,(name,st,target)
    return matches[0]

rows=[]
for line in (OUT/'candidate-selection.txt').read_text().splitlines():
    st,names=line.split('|')
    for name in map(str.strip,names.split(';')):
        pop = pop_match(name,st)
        match = source_matches[(st,name)]
        e = next(x for x in evidence if match.lower() in (x['url']+')').lower())
        url=e['url']
        if 'library.municode.com/' in url:
            source_family='Municode'
            entry=re.match(r'(https://library.municode.com/[^/]+/[^/?]+)',url).group(1)
        elif 'codelibrary.amlegal.com/' in url:
            source_family='American Legal'
            entry=re.match(r'(https://codelibrary.amlegal.com/codes/[^/]+/latest)',url).group(1)+'/overview'
        elif 'ecode360.com/' in url: source_family='eCode360';entry=url
        elif '.municipal.codes' in url: source_family='municipal.codes';entry=url
        else: source_family='Official government source / routing page';entry=url
        source_family=family_overrides.get(name,source_family)
        note=special_notes.get(name,'')
        if name.endswith('County'):
            typ='County'
            note += ' Collect county enactments as a separate legal layer; applicability may differ between incorporated and unincorporated areas. Do not sum county and city populations.'
        elif name in ['Honolulu','Anchorage','Indianapolis','Louisville','Lexington','Nashville','Jacksonville']:
            typ='Consolidated city/county or municipality'
        elif name=='Baton Rouge / East Baton Rouge Parish':typ='Combined city/parish government'
        elif name in ['Baltimore City','St. Louis'] or st=='VA':typ='Independent city'
        else:typ='City'
        rows.append({'jurisdiction':display.get(name,name),'selection_name':name,'state':st,'state_name':STATE_NAMES[st],'entity_type':typ,'existing_local_scope_in_state':counts[st],'new_state_for_local_scope':st not in counts,'population_july_1_2025':int(pop[-1]) if pop else None,'census_place_rank_2025':int(pop[0]) if pop else None,'population_geography':pop[1] if pop else 'Not assigned: county or combined scope differs from city-ranking geography','source_lead_url':entry,'source_evidence_url':url,'source_evidence_title':e['title'],'source_family':source_family,'source_status':'Discovery only; source entry or official routing page located. Acquisition and full-code completeness not tested.','source_discovered_on':'2026-10-17','boundary_note':note.strip()})

assert len(rows)==len({(r['jurisdiction'],r['state']) for r in rows})==100
assert not {(r['selection_name'],r['state']) for r in rows}&existing
wave1 = [r for r in rows if r['census_place_rank_2025'] is not None and r['census_place_rank_2025']<=50]
represented = set(counts)|{r['state'] for r in wave1}
anchors={}
for r in rows:
    st=r['state']
    if st not in represented:
        if st not in anchors or (r['population_july_1_2025'] or 0)>(anchors[st]['population_july_1_2025'] or 0): anchors[st]=r
for r in rows:
    if r in wave1:
        wave=1; reason=f"Closes a top-50 population gap: Census place rank {r['census_place_rank_2025']} in 2025."
    elif anchors.get(r['state']) is r:
        wave=2; reason=f"Establishes a first local-code target in {r['state_name']}, which currently has no local jurisdictions in scope."
    else:
        wave=3; reason=extra_reasons.get(r['selection_name'],f"Adds another substantial local government in {r['state_name']} to deepen coverage beyond the first anchor cities.")
    if r['selection_name'] in extra_reasons and wave!=3: reason+=' '+extra_reasons[r['selection_name']]
    if r['new_state_for_local_scope'] and wave==1: reason+=f" Also opens local coverage in {r['state_name']}."
    if r['selection_name']=='Baltimore City':reason+=' Existing Baltimore County coverage does not include this independent city.'
    if r['selection_name']=='Miami':reason+=' Existing Miami-Dade County coverage does not include the City of Miami code.'
    r['collection_wave']=wave;r['selection_rationale']=reason
rows.sort(key=lambda r:(r['collection_wave'], -(r['population_july_1_2025'] or 0),r['state'],r['jurisdiction']))
for i,r in enumerate(rows,1):r['sequence']=i

existing_census=set()
for name,st in existing:
    if name.endswith('County'):continue
    target=aliases.get(name,name+' city')+', '+STATE_NAMES[st]
    existing_census.add(target)
chosen_census={r['population_geography'] for r in rows}
top50=[r for r in census if int(r[0])<=50]
missing=[r[1] for r in top50 if r[1] not in existing_census|chosen_census and not r[1].endswith(', District of Columbia')]
assert missing==[],missing
assert len(set(counts)|{r['state'] for r in rows})==50
newstates=sorted({r['state'] for r in rows}-set(counts))
assert len(newstates)==38
summary={'baseline_local_jurisdictions':74,'baseline_states':12,'baseline_state_counts':dict(sorted(counts.items())),'recommended_additions':100,'recommended_states':len({r['state'] for r in rows}),'new_states':newstates,'expanded_local_jurisdictions':174,'expanded_states':50,'collection_wave_counts':dict(sorted(collections.Counter(r['collection_wave'] for r in rows).items())),'existing_top50_census_places':sum(r[1] in existing_census for r in top50),'new_top50_census_places':len(wave1),'dc_top50_handled_in_existing_state_workstream':1,'county_targets':sum(r['entity_type']=='County' for r in rows),'duplicate_targets':0,'overlap_with_existing_scope':0}
sources=[{'path':str(baseline_path),'sha256':hashlib.sha256(baseline_path.read_bytes()).hexdigest(),'purpose':'74-jurisdiction exclusion baseline'}, {'path':str(ROOT/'outputs/domain-inventory-2026-10-16-active/jurisdiction-coverage.csv'),'purpose':'October 16 cross-check: same 74 local jurisdictions; DC statutes/regulations mapped in state workstreams'}, {'url':'https://www2.census.gov/programs-surveys/popest/tables/2020-2025/cities/totals/SUB-IP-EST2025-ANNRNK.xlsx','purpose':'Census Vintage 2025 incorporated-place ranking and July 1, 2025 population; released May 14, 2026'}]
data={'title':'100 additional local jurisdictions','prepared_on':'2026-10-17','summary':summary,'method':'All 74 already-scoped jurisdictions are excluded, including the 30 outstanding collection targets. Wave 1 fills the Census top-50 gaps. Wave 2 adds one anchor in each state still absent after wave 1. Wave 3 adds county layers and selected secondary cities. Sequence within each wave orders matched Census place populations descending; counties follow because comparable city populations are not assigned. This is an editorial coverage recommendation, not a numerical estimate of legal importance or extraction difficulty.','limits':['Scope representation is not completed full-text collection or statewide local-law coverage.','Population is a scale indicator, not a count of affected employers or a non-overlapping coverage total.','County and combined-government populations are intentionally not substituted with city-only Census figures.','Source discovery is not live acquisition validation. Existing scripts require qualification on each new target.','Territories, tribal governments and special districts are outside this 100-target recommendation.','DC is excluded as a new local target because the October 16 inventory already maps its code and regulations in the state-level workflows.'],'sources':sources,'recommendations':rows}
(OUT/'recommendations.json').write_text(json.dumps(data,indent=2,ensure_ascii=False))
(OUT/'baseline-74.json').write_text(json.dumps(baseline,indent=2,ensure_ascii=False))
print(json.dumps(summary,indent=2))
for wave in [1,2,3]:print('WAVE',wave, '; '.join(r['jurisdiction']+', '+r['state'] for r in rows if r['collection_wave']==wave))

esc=html.escape
table=[]
for r in rows:
    pop=f"{r['population_july_1_2025']:,}" if r['population_july_1_2025'] is not None else '—'
    note=f"<details><summary>Scope note</summary>{esc(r['boundary_note'])}</details>" if r['boundary_note'] else ''
    table.append(f'''<tr data-wave="{r['collection_wave']}" data-new="{str(r['new_state_for_local_scope']).lower()}" data-pop="{r['population_july_1_2025'] or 0}"><td>{r['sequence']}</td><td>{r['collection_wave']}</td><td><strong>{esc(r['jurisdiction'])}</strong><small>{esc(r['entity_type'])}</small>{note}</td><td>{r['state']}<small>{r['state_name']}</small><small>{r['existing_local_scope_in_state']} currently scoped</small></td><td class="num" title="{esc(r['population_geography'])}">{pop}</td><td>{esc(r['selection_rationale'])}</td><td><a href="{esc(r['source_lead_url'])}" target="_blank" rel="noopener">{esc(r['source_family'])}</a><small><a href="{esc(r['source_evidence_url'])}" target="_blank" rel="noopener">Discovery evidence</a></small></td></tr>''')
state_table=[]
for st in sorted(set(counts)|{r['state'] for r in rows},key=lambda s:STATE_NAMES[s]):
    additions=[r['jurisdiction'] for r in rows if r['state']==st]
    state_table.append(f'<tr><td>{STATE_NAMES[st]}</td><td>{counts[st]}</td><td>{len(additions)}</td><td>{counts[st]+len(additions)}</td><td>{esc("; ".join(additions)) or "Existing scope retained"}</td></tr>')
page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>100 additional local jurisdictions | CompliSolv</title><style>
:root{color-scheme:light;font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#152938;background:#f6f8fa}body{margin:0}main{max-width:1560px;margin:auto;padding:32px}h1{font-size:34px;line-height:1.15;max-width:850px}h2{font-size:23px;margin-top:32px}p{max-width:1050px;line-height:1.6}a{color:#005c83}small{display:block;color:#536776;font-size:12px;margin-top:5px}header{border-bottom:3px solid #138383;padding-bottom:16px}.eyebrow{letter-spacing:.06em;font-size:12px;font-weight:700;color:#467078}.metrics{display:flex;gap:40px;flex-wrap:wrap;margin:24px 0}.metrics strong{display:block;font-size:30px}.metrics span{font-size:14px}.controls{display:flex;flex-wrap:wrap;gap:12px;align-items:end;margin:20px 0}label{font-size:13px}input,select{display:block;margin-top:5px;padding:10px;border:1px solid #a7b6c2;border-radius:5px;background:white;color:#152938;font:inherit}input{min-width:300px}.tablewrap{overflow:auto;background:white;border:1px solid #d9e0e5;border-radius:6px}table{border-collapse:collapse;width:100%;font-size:14px}th{background:#173c52;color:white;text-align:left;padding:12px;white-space:nowrap}td{padding:12px;border-bottom:1px solid #e2e9ed;vertical-align:top;line-height:1.45}tbody tr:nth-child(even){background:#f5f8fa}td:nth-child(3){min-width:190px}td:nth-child(6){min-width:280px}td:nth-child(7){min-width:160px}.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}details{margin-top:9px;font-size:12px;max-width:340px}summary{cursor:pointer;color:#005c83}li{max-width:1050px;margin:7px 0;line-height:1.5}.note{border-left:4px solid #d39528;padding:8px 16px;background:#fff7e7}footer{font-size:12px;color:#536776;margin-top:24px}#shown{font-size:13px;margin:10px 0}@media print{.controls{display:none}main{padding:10px}table{font-size:10px}td{padding:5px}.tablewrap{overflow:visible}a{color:inherit}}
</style></head><body><main><header><div class="eyebrow">COMPLISOLV · COVERAGE PLANNING · 17 OCTOBER 2026</div><h1>100 additional local jurisdictions</h1><p>A proposed expansion beyond all 74 currently scoped jurisdictions, including the 30 awaiting collection. The October 16 inventory confirms the same baseline. This recommendation balances major-city coverage, first coverage in absent states, and selected county and secondary-city codes.</p></header><div class="metrics"><div><strong>74 → 174</strong><span>Local jurisdictions in scope</span></div><div><strong>12 → 50</strong><span>States with a local target</span></div><div><strong>0</strong><span>Duplicates or existing-scope overlaps</span></div></div>
<p><b>Collection order:</b> Wave 1 fills the __W1__ missing jurisdictions in the Census top 50. Wave 2 adds __W2__ anchors to reach every state. Wave 3 adds __W3__ county and secondary-city targets. Within waves, matched Census place populations are ordered largest first; county targets follow because city-only population figures are not assigned to them. This is a coverage recommendation, not a score of legal importance.</p><p class="note"><b>Source discovery only.</b> Each row has a code-source lead or official routing page. These 100 targets have not undergone end-to-end acquisition or full-code completeness validation. A state with one local target is represented, not comprehensively covered. D.C. remains in its existing state-level code and regulations workstreams.</p>
<div class="controls"><label>Search jurisdictions, states or sources<input id="search" type="search" placeholder="e.g. Texas, county, eCode360"></label><label>Collection wave<select id="wave"><option value="">All waves</option><option value="1">1 · Major-city gaps</option><option value="2">2 · Remaining state anchors</option><option value="3">3 · Regional depth and counties</option></select></label><label>Current state coverage<select id="newstate"><option value="">All states</option><option value="true">States with no local target today</option><option value="false">States already represented</option></select></label><label>Order<select id="order"><option value="sequence">Suggested sequence</option><option value="state">State</option><option value="population">Population</option></select></label></div><div id="shown" aria-live="polite">100 jurisdictions shown</div>
<div class="tablewrap"><table id="shortlist"><thead><tr><th>No.</th><th>Wave</th><th>Jurisdiction</th><th>State</th><th>2025 population*</th><th>Why collect</th><th>Source lead</th></tr></thead><tbody>__TABLE__</tbody></table></div>
<p><small>* Census July 1, 2025 place estimates, Vintage 2025, released May 14, 2026. Hover over a population for its exact Census geography. Consolidated-government balance populations retain their Census definitions. A dash means no comparable city population has been assigned to a county or combined target. Populations are not summed because county/city geographies overlap.</small></p>
<h2>State coverage before and after</h2><div class="tablewrap"><table><thead><tr><th>State</th><th>Current</th><th>Additions</th><th>Proposed total</th><th>New targets</th></tr></thead><tbody>__STATES__</tbody></table></div>
<h2>Selection and collection notes</h2><ul><li>The 39 California targets already in scope warrant limiting further city expansion there to four top-50 omissions: Fresno, Sacramento, Long Beach and Bakersfield. Los Angeles County and San Diego County add separate county law.</li><li>New York expands beyond New York City with Buffalo, Rochester, Albany and Westchester County. Washington gains Spokane and Tacoma; Maryland gains Baltimore City in addition to its existing counties.</li><li>The seven stand-alone county additions are Los Angeles, San Diego, Clark, Westchester, Allegheny, Fairfax and Arlington. County applicability must remain distinct from city applicability.</li><li>Consolidated or combined city/county targets count once. Honolulu means the City and County of Honolulu, not Urban Honolulu CDP. No separate Davidson County, Jefferson County or Marion County duplicate is added.</li><li>For each accepted target, inventory the general code, charter, zoning/development code, separately published regulations, and uncodified amendments. Preserve publisher currency dates and supplements. Incorporated model codes require a separate scope decision.</li><li>Source families are discovery leads, not evidence that a previously tested extractor will work unchanged. Resolve the current publication from the official routing page before qualification.</li><li>This list does not add further targets in Illinois, Maine, Minnesota or New Mexico because each already has local coverage and the available slots first address absent states and larger omissions. Territories, tribal governments and special districts are outside this recommendation.</li></ul>
<h2>Evidence</h2><p>Baseline: local_jurisdiction_scope.json (74 targets), cross-checked against jurisdiction-coverage.csv in the October 16 active domain inventory. Population: <a href="https://www.census.gov/data/tables/time-series/demo/popest/2020s-total-cities-and-towns.html">U.S. Census Bureau, City and Town Population Totals</a>, <a href="https://www2.census.gov/programs-surveys/popest/tables/2020-2025/cities/totals/SUB-IP-EST2025-ANNRNK.xlsx">Vintage 2025 ranked-place table</a>. Source leads were discovered on October 17, 2026; search-index discovery does not establish current site availability. Exact evidence URLs and baseline provenance are in <a href="recommendations.json">the structured shortlist</a>.</p><footer>Prepared for collection planning. Existing scope and collection records were not changed.</footer></main><script>
const body=document.querySelector('#shortlist tbody'),rows=[...body.rows];const search=document.querySelector('#search'),wave=document.querySelector('#wave'),newstate=document.querySelector('#newstate'),order=document.querySelector('#order');function update(){let q=search.value.toLowerCase();let sorted=[...rows].sort((a,b)=>order.value==='state'?a.cells[3].textContent.localeCompare(b.cells[3].textContent)||Number(a.cells[0].textContent)-Number(b.cells[0].textContent):order.value==='population'?Number(b.dataset.pop)-Number(a.dataset.pop):Number(a.cells[0].textContent)-Number(b.cells[0].textContent));let n=0;for(let r of sorted){r.hidden=!((r.cells[2].querySelector('strong').textContent+' '+r.cells[3].textContent+' '+r.cells[6].textContent).toLowerCase().includes(q)&&(!wave.value||r.dataset.wave===wave.value)&&(!newstate.value||r.dataset.new===newstate.value));if(!r.hidden)n++;body.append(r)}document.querySelector('#shown').textContent=n+' jurisdictions shown'}[search,wave,newstate,order].forEach(x=>x.addEventListener('input',update));
</script></body></html>'''
for k,v in {'__W1__':str(summary['collection_wave_counts'][1]),'__W2__':str(summary['collection_wave_counts'][2]),'__W3__':str(summary['collection_wave_counts'][3]),'__TABLE__':''.join(table),'__STATES__':''.join(state_table)}.items():page=page.replace(k,v)
(OUT/'jurisdiction-shortlist.html').write_text(page)
