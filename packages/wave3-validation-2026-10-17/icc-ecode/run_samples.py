#!/usr/bin/env python3
"""Serial bounded substantive acquisition with native exports; stops family on429."""
import argparse,json,time
from pathlib import Path
import collect
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--job',action='append');a=p.parse_args();jobs=json.loads((R/'jobs.json').read_text())
for slug in a.job or list(jobs):
 try:collect.browser(jobs[slug],R/'evidence'/slug/'sample',export=True)
 except Exception as e:print(slug,type(e).__name__,str(e),flush=True)
 if (R/'evidence'/'BROWSER-STOP-eCode360.json').exists() and jobs[slug]['family']=='eCode360':break
 if (R/'evidence'/'BROWSER-STOP-municipal-codes.json').exists() and jobs[slug]['family']=='municipal.codes':break
 time.sleep(3)
