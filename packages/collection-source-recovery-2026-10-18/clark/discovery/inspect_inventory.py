"""Retained authoritative source only. No requests/native parse/image access."""
import contextlib,copy,hashlib,importlib.util,json,pathlib,socket,sys
from unittest.mock import patch
from bs4 import BeautifulSoup
HERE=pathlib.Path(__file__).resolve().parent
PROJECT=HERE.parent.parent.parent
REPO=PROJECT/'github/local-jurisdiction-collection'
PRIOR=PROJECT/'outputs/wave3-validation-2026-10-17/municode-counties'
URL='https://www.clarkcountynv.gov/government/departments/comprehensive_planning_department/library/title-30'
HEADER='Title 30 - Effective 9/17/2026'
GROUP='main .document-center > div:has(> div:first-child:-soup-contains("Title 30 - Effective 9/17/2026"))'
SELECTOR=GROUP+' > div:nth-of-type(2) a[href]'
sha=lambda b:hashlib.sha256(b).hexdigest()
html=(PRIOR/'evidence/routes/clark-title30.html').read_bytes();receipt=json.loads((PRIOR/'evidence/routes/clark-title30.html.receipt.json').read_text());assert sha(html)==receipt['sha256']=='cf274c87809aef61c4ebf2e9202974015882e111bb1eeacb9a448ed4b7ad4266';assert receipt['http_status']==200 and receipt['url']==URL
s=BeautifulSoup(html,'html.parser');groups=s.select(GROUP);assert len(groups)==1;group=groups[0];assert group.find_all('div',recursive=False)[0].get_text(' ',strip=True)==HEADER
current=[]
for ordinal,a in enumerate(s.select(SELECTOR)):
 current.append({'source_order':ordinal,'label':a.get_text(' ',strip=True),'url':a['href'],'literal_anchor':str(a),'anchor_sha256':sha(str(a).encode()),'source_group_label':HEADER,'source_page_sha256':sha(html),'kind':'native_pdf','role':'core_code' if ordinal==0 else 'associated_map_document','normalization_policy':'Original PDF may intrinsically contain images; retain all available native labels/text and ordered[IMAGE] omissions, no pixels/geometry transcription or blanketno-text exemption.'})
assert len(current)==30 and len({a['url'] for a in current})==30 and current[0]['label']=='Title 30' and all(a['url'].startswith('https://www.clarkcountynv.gov/adobe/assets/') and a['url'].endswith('.pdf') for a in current)
legacy=[]
for g in s.select('main .document-center > div'):
 heading=g.find_all('div',recursive=False)[0].get_text(' ',strip=True)
 if heading=='Title 30 - Effective Through 12/31/2023':legacy=[{'label':a.get_text(' ',strip=True),'url':a['href'],'reason':'Explicit historical group effective through12/31/2023, not currentselectedpublication'}for a in g.select('a[href]')]
assert len(legacy)==66 and not ({a['url'] for a in current}&{a['url'] for a in legacy})
config={'schema':1,'id':'96-clark-title30-current-associated-documents','jurisdiction':'Clark County','state':'NV','publication':'Title 30 Unified Development Code and associated documents in official current group','source_url':URL,'mode':'pdf_set','transport':'http','document_transport':'http','inventory_selector':SELECTOR,'include_url_regex':r'^https://www[.]clarkcountynv[.]gov/adobe/assets/urn:aaid:aem:[0-9a-f-]+/original/as/[^?#]+[.]pdf$','source_currency_selector':GROUP+' > div:first-child','source_identity_tokens':['Title 30 is the Clark County Code related to land use, zoning and development.',HEADER],'coverage_level':'file_pages','pdf_normalization':'coordinate-v1','scope_warning':'Exactlycurrentdocument-center group:corePDF+29associatedmapPDFs. Notlegacy66links,notwholecounty/uncodifiedlaw. Source labels/nativePDFedition vsfilename keptliteral. FullPDFsemantic/section/table/label qualification isnotfilecapture. Rootapproval+gatecheck required before any requests.'}
# Exercise existing standard inventory code using only retainedHTML substitution.
sys.path.insert(0,str(REPO/'collectors/official'));spec=importlib.util.spec_from_file_location('selected_official_collect',REPO/'collectors/official/collect.py');collect=importlib.util.module_from_spec(spec);spec.loader.exec_module(collect);calls=[]
def no(*a,**k):calls.append('forbidden_network_or_native');raise AssertionError(calls[-1])
with patch.object(socket,'socket',no),patch.object(collect,'fetch_raw',return_value=(html,receipt,'raw/retained-discovery.bin')):
 items,identity=collect.discover(HERE,config)
assert [i['url'] for i in items]==[a['url'] for a in current] and len(items)==30 and identity['source_currency']==HEADER
faults=[]
for name,raw in [('remove-current-heading',html.replace(HEADER.encode(),b'Title30unknown')),('legacy-only',str(s.select_one('main .document-center > div:nth-of-type(2)')).encode())]:
 with patch.object(socket,'socket',no),patch.object(collect,'fetch_raw',return_value=(raw,{},'raw/changed.bin')):
  try:collect.discover(HERE,config)
  except ValueError:faults.append(name)
  else:raise AssertionError('Unqualifiedselector accepted'+name)
assert not calls
(HERE/'current-inventory.json').write_text(json.dumps({'source_url':URL,'source_html_sha256':sha(html),'selector':SELECTOR,'source_group_selector':GROUP,'source_header':HEADER,'current_documents':current,'historical_documents_explicitly_outside_current_group':legacy,'all_current_own_source_anchors_retained':True},ensure_ascii=False,indent=2)+'\n')
(HERE/'proposed-official-config.json').write_text(json.dumps(config,indent=2)+'\n')
(HERE/'offline-selector-proof.json').write_text(json.dumps({'standard_discovery_source_sha256':sha((REPO/'collectors/official/collect.py').read_bytes()),'existing_discover_exercised':True,'retained_HTML_substituted_only':True,'current_items':len(items),'legacy_excluded':len(legacy),'identity':identity,'faults_refused':faults,'forbidden_calls':calls,'publication_requests':0,'native_parses':0,'source_image_ops':0,'qualification':'Authoritative explicitcurrentinventory/configcandidate only, notfullpublication orclosing proof'},indent=2)+'\n')
print(json.dumps({'current':len(items),'legacy':len(legacy),'faults':faults,'forbidden_calls':calls}))
