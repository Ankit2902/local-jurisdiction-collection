#!/usr/bin/env python3
"""Serial bounded discovery; each browser snapshot is retained, never a substantive pass."""
from pathlib import Path
import json,time
import collect
ROOT=Path(__file__).resolve().parent
jobs=json.loads((ROOT/'jobs.json').read_text())
for slug in ['buffalo','tacoma','rochester','albany','allegheny','eugene']:
 job=jobs[slug]
 if slug=='rochester':job.update(url='https://ecode360.com/RO0104',expected_customer='RO0104')
 if slug=='eugene':job.update(url='https://eugene.municipal.codes/')
 jobs[slug]=job
 collect.save(ROOT/'jobs.json',jobs)
 try:
  collect.browser(job,ROOT/'evidence'/slug/'discovery',discover=True)
  p=ROOT/'evidence'/slug/'discovery'/'source.html';html=p.read_text();s=collect.BeautifulSoup(html,'html.parser')
  print(slug,s.title.get_text(' ',strip=True),flush=True)
  if job['family']=='eCode360':
   inv=collect.ec.inventory_candidate(html,job['url']);collect.save(p.parent/'inventory-candidate.json',inv);print([(x['node_id'],x['display_heading']) for x in inv['nodes'][:12]],flush=True)
  else:print([(a.get_text(' ',strip=True),a['href']) for a in s.select('main a[href]')][:20],flush=True)
 except Exception as e:print(slug,type(e).__name__,str(e),flush=True)
 if (ROOT/'evidence'/'BROWSER-STOP-eCode360.json').exists():break
 time.sleep(3)
