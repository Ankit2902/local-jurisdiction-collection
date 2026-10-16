#!/usr/bin/env python3
"""Re-run portable offline regressions and all retained DOM replays (no network)."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
import ecode360 as e
ROOT=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path);p.add_argument('--verify-bundle',action='store_true');args=p.parse_args()
 if args.verify_bundle:
  manifest=e.load(ROOT/'BUNDLE-MANIFEST.json');fail=[]
  for name,sha in manifest['sha256'].items():
   path=e.safe_path(ROOT,name)
   if not path.is_file() or e.digest(path.read_bytes())!=sha:fail.append(name)
  print(json.dumps({'checked_files':len(manifest['sha256']),'mismatches':fail},indent=2))
  return 1 if fail else 0
 if not args.out:p.error('--out is required for replay checks')
 out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
 run=subprocess.run([sys.executable,'-m','unittest','-v','test_ecode360.py'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 (out/'tests.txt').write_text(run.stdout,encoding='utf-8')
 if run.returncode:print(run.stdout);return run.returncode
 reports=[]
 folders=sorted((ROOT/'fixtures/historical').iterdir())+[ROOT/'fixtures/current-santa-monica']
 for folder in folders:
  report=e.replay(folder/'inventory.json',folder/'artifacts.json',out/folder.name)
  reports.append({'fixture':str(folder.relative_to(ROOT)),**report})
 e.dump(out/'offline-validation.json',{'executed_at':e.now(),'tests_exit_code':run.returncode,'fixtures':reports,'included_records':sum(r['included_record_count'] for r in reports),'full_collection_verified':False})
 print(json.dumps({'tests_exit_code':run.returncode,'fixture_count':len(reports),'included_records':sum(r['included_record_count'] for r in reports),'unresolved_nodes':sum(r['unresolved_node_count'] for r in reports),'error_count':sum(len(r['errors']) for r in reports),'report':str(out/'offline-validation.json'),'full_collection_verified':False},indent=2))
 return 1 if any(r['errors'] or r['unresolved_node_count'] for r in reports) else 0
if __name__=='__main__':sys.exit(main())
