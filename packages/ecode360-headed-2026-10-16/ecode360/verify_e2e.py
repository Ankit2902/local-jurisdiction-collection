#!/usr/bin/env python3
"""Offline re-verification of all14 exact current supported-browser source captures."""
import argparse,json,subprocess,sys
from pathlib import Path
import ecode360 as e
from ingest_cua import ingest
ROOT=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve()
 if out.exists() and any(out.iterdir()):p.error('use a fresh empty output directory; retained evidence is immutable')
 out.mkdir(parents=True,exist_ok=True)
 tests=subprocess.run([sys.executable,'-m','unittest','-v','test_ecode360.py','test_e2e.py'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 (out/'tests.txt').write_text(tests.stdout,encoding='utf-8')
 if tests.returncode:print(tests.stdout);return tests.returncode
 selections={r['slug']:r for r in e.load(ROOT/'live/ingest-results.json')};results=[]
 for city in e.load(ROOT/'current-routes.json'):
  chosen=selections[city['slug']];r=ingest(ROOT/chosen['receipt'],city['jurisdiction'],out/city['slug'])
  results.append({'slug':city['slug'],'source_receipt':chosen['receipt'],'source_url':r['source_url'],'supported_browser_e2e_verified':r['supported_browser_e2e_verified'],'records':r['parsed_records'],'result_path':city['slug']+'/e2e-result.json','source_sha256':r['source_sha256']})
 summary={'verified_at':e.now(),'network_used':False,'kind':'replay of exact current supported-CUA source acquisitions, not fresh acquisition','tests_exit_code':0,'jurisdictions':results,'source_count':len(results),'records':sum(r['records'] for r in results),'all_pass':all(r['supported_browser_e2e_verified'] for r in results),'inventory_verified':False,'full_collection_verified':False}
 e.dump(out/'summary.json',summary);print(json.dumps(summary,indent=2));return 0 if summary['all_pass'] else 2
if __name__=='__main__':sys.exit(main())
