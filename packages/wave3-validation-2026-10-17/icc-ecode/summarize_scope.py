#!/usr/bin/env python3
"""Offline publisher family/edition inventory from retained discovery evidence."""
import json,re
from pathlib import Path
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parent
out=[]
for slug in ['buffalo','tacoma','rochester','eugene','albany','allegheny']:
 folder=R/'evidence'/slug/('scope-discovery' if slug=='albany' else 'discovery');s=BeautifulSoup((folder/'source.html').read_text(),'html.parser');item={'job':slug,'discovery_source':str((folder/'source.html').relative_to(R)),'title':s.title.get_text(' ',strip=True),'complete_inventory':False}
 if slug!='eugene':
  inv=json.loads((folder/'inventory-candidate.json').read_text());item['identity']=inv['identity'];item['inventory_nodes_observed']=len(inv['nodes']);item['families']=[{k:n[k] for k in ['node_id','display_heading','source_url']} for n in inv['nodes'] if any(t in n['display_heading'].lower() for t in ['charter','zoning','development','land use','shoreline','administrative code'])]
 else:
  item['families']=[{'name':'Eugene Code','url':'https://eugene.municipal.codes/EC','scope':'chapters1–9 andTables observed;chapter9 LandUse separately noted withinCode'}];item['chapter_links']=[{'name':a.get_text(' ',strip=True),'href':a['href']} for a in s.select('main a[href]') if a['href'].startswith('/EC/')];item['currency']=[p.get_text(' ',strip=True) for p in s.select('p') if p.get_text(' ',strip=True).startswith('The Eugene Code is current through')]
 item['limitations']=['Observed TOC/publication families only; no full-corpus or expanded-inventory completeness claim.']
 if slug=='eugene':item['limitations'].append('Charter not observed as a separate publisher tab in retained root; official charter route still requires separate inventory.')
 if slug=='allegheny':item['limitations'].append('Publisher includes legislation only throughJune4,2024. County law is separate from Pittsburgh/city law; applicability must be assessed by provision.')
 out.append(item)
(R/'publication-inventory.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
