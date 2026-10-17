#!/usr/bin/env python3
"""Read-only current-policy image-byte audit for the explicit selected-run ledger."""
import argparse,json
from pathlib import Path
from audit_images import audit
HERE=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser();p.add_argument('--evidence-root',type=Path,required=True);p.add_argument('--runs',type=Path,default=HERE/'selected-runs.json');p.add_argument('--out',type=Path);a=p.parse_args();results=[]
 for row in json.loads(a.runs.read_text())['runs']:
  r=audit(a.evidence_root/row['run']);r.update(family=row['family'],evidence_run=row['run']);results.append(r)
 report={'schema_version':1,'network_requests_sent':0,'read_only_sources':True,'passed':all(r['passed'] for r in results),'selected_runs':len(results),'separate_image_binary_count':sum(r['separate_image_binary_count'] for r in results),'results':results}
 if a.out:a.out.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
