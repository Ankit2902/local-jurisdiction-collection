#!/usr/bin/env python3
from pathlib import Path
import json,time
import collect
R=Path(__file__).resolve().parent;j=json.loads((R/'jobs.json').read_text())
for slug in ['tacoma','albany']:
 o=R/'evidence'/slug/'scope-discovery'
 try:
  collect.browser(j[slug],o,discover=True);p=o/'source.html';inv=collect.ec.inventory_candidate(p.read_text(),j[slug]['url']);collect.save(o/'inventory-candidate.json',inv);print(slug,len(inv['nodes']),[(x['node_id'],x['display_heading']) for x in inv['nodes'][:30]],flush=True)
 except Exception as e:print(slug,str(e),flush=True)
 if (R/'evidence'/'BROWSER-STOP-eCode360.json').exists():break
 time.sleep(3)
