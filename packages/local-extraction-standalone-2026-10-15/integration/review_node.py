#!/usr/bin/env python3
"""Run the delivered offline JavaScript acquisition and scope checks."""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITES = [('ecode360','test_capture.mjs',11),('codepublishing','test_acquire_cua.mjs',10),('municipal-codes','test_checksum.mjs',6),('municipal-codes','test_transport_guards.mjs',10)]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--node',default='node')
    args=ap.parse_args()
    out=ROOT/'integration/independent-review'
    out.mkdir(exist_ok=True)
    results=[]
    for package,script,count in SUITES:
        path=ROOT/package/script
        before=hashlib.sha256(path.read_bytes()).hexdigest()
        p=subprocess.run([args.node,script],cwd=path.parent,capture_output=True,text=True)
        log=out/(package+'-'+Path(script).stem+'.txt')
        log.write_text(p.stdout+p.stderr)
        results.append({'package':package,'command':'node '+script,'checks':count,'exit_code':p.returncode,'passed':p.returncode==0 and before==hashlib.sha256(path.read_bytes()).hexdigest(),'source_sha256':before,'log':str(log.relative_to(ROOT))})
    report={'reviewed_at':datetime.now(timezone.utc).isoformat(),'node_version':subprocess.check_output([args.node,'--version'],text=True).strip(),'checks':sum(r['checks'] for r in results),'all_passed':all(r['passed'] for r in results),'suites':results}
    (out/'NODE-REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if report['all_passed'] else 1

if __name__=='__main__':raise SystemExit(main())
