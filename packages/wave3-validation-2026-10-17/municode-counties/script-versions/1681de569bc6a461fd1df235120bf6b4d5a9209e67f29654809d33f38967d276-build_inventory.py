"""Authoring inventory from retained publication APIs and official route evidence."""
import json,re
from collect_all import ROOT,ASSIGNMENT,slug
notes={76:'Independent city, Virginia. Charter and code are distinct TOC families; no Richmond California substitution.',77:'Independent city. Not subordinate to a county.',90:'Official Cambridge zoning page identifies a separately published Zoning Ordinance, print version plus later amendments controlling discrepancies; primary municipal-code sample does not validate zoning corpus.',93:'County enactments are a separate layer from Los Angeles city. Applicability to incorporated and unincorporated areas must be determined from each provision; no county/city population sum.',95:'Combined city/parish code. Official route warns not every Metropolitan Council ordinance/resolution is included. Separate UDC chapters and appendices are inventoried; sampled native chapters1 and9. Preserve city/parish/unincorporated qualifiers, no city-only Census population.',96:'County separate from Las Vegas/Henderson. Official clerk route lists amendments not yet codified. Separate current government Title30 native PDF sampled; government page label9/17/2026, filename10.7.2026, PDF cover latest amendment9/2/2026 effective9/17/2026: filename alone is not edition proof.',97:'County law separate from New York City and incorporated municipalities; territory and function vary provision by provision.'}
routes=json.loads((ROOT/'official-route-inventory.json').read_text())
rows=[]
for a in ASSIGNMENT:
 d=ROOT/'browser'/slug(a)
 if not (d/'receipt.json').exists():d=ROOT/'http'/slug(a)
 receipt=json.loads((d/'receipt.json').read_text()) if (d/'receipt.json').exists() else {}
 cc=json.loads((d/'client-content.json').read_text()) if (d/'client-content.json').exists() else {}
 additional=[]
 for arpath in (ROOT/'additional').glob('*/receipt.json'):
  ar=json.loads(arpath.read_text());client=(ar.get('product') or {}).get('Client',{})
  if client.get('ClientName','').lower()==a['jurisdiction'].lower() and client.get('State',{}).get('StateAbbreviation')==a['state']:additional.append({'folder':str(arpath.parent.relative_to(ROOT)),'status':ar['status'],'selected_nodes':ar.get('selected_nodes',[]),'job':ar.get('job'),'families':ar.get('families_top_level',[]),'complete_corpus':False})
 families=[]
 if (d/'toc-full.json').exists():
  def walk(n,path=[]):
   if n.get('HasChildren') and n.get('NodeDepth',999)<=4 and re.search(r'charter|zoning|development|appendix|building|code of ordinances|city code|county code',n.get('Heading',''),re.I):families.append({'id':n['Id'],'heading':n['Heading'],'path':path+[n['Heading']],'tested_as_full_family':False})
   for c in n.get('Children',[]):walk(c,path+[n['Heading']])
  walk(json.loads((d/'toc-full.json').read_text()))
 rows.append({'tested_additional_publications':additional,'client_content_catalog_keys':list(cc),'additional_publisher_catalog_sections':{k:v for k,v in cc.items() if k not in ['codes','features']},'historical_codebank_versions_collected':False,'family_headings_within_primary_toc':families,'sequence':a['sequence'],'jurisdiction':a['jurisdiction'],'entity_type':a['entity_type'],'tested_primary':{'folder':str(d.relative_to(ROOT)),'selected_nodes':receipt.get('selected_nodes',[]),'status':receipt.get('status','untested'),'job':receipt.get('job')},'all_publisher_publications':receipt.get('publications',[]),'primary_full_toc_top_level_families':receipt.get('families_top_level',[]),'additional_official_routes':[r for r in routes if (a['sequence']==95 and r['name'].startswith('baton')) or (a['sequence']==96 and r['name'].startswith('clark')) or (a['sequence']==90 and r['name'].startswith('cambridge')) or (a['sequence']==89 and r['name'].startswith('stamford'))],'scope_note':notes.get(a['sequence'],'Municipal code sample only. Separately published charter/zoning/development families and later ordinances require their own applicability/currency review.'),'complete_corpus':False})
(ROOT/'source-scope-inventory.json').write_text(json.dumps(rows,indent=2))
