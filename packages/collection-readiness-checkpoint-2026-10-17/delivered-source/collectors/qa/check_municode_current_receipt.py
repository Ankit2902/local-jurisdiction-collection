#!/usr/bin/env python3
"""Independently bind a current read-only verifier receipt to earlier raw-source audit; no replay/network."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--inventory-audit',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args();r=json.loads(a.receipt.read_text());inventory=json.loads(a.inventory_audit.read_text());cp=json.loads((a.run/'checkpoint.json').read_text());errors=[]
 if not r['result']['passed'] or r['result']['checks']<58 or r['network_requests']!=0 or not r['source_files_unchanged']:errors.append('Current family receipt does not qualify exact read-only verification')
 for name,expected in r['current_implementation'].items():
  if sha(ROOT/'collectors/municode'/name)!=expected:errors.append('Current implementation differs: '+name)
 if not inventory['passed'] or sha(a.run/'checkpoint.json')!=inventory['checkpoint_sha256']:errors.append('Actual proof checkpoint differs from independent raw-source audit')
 for pub in inventory['publications']:
  if sha(a.run/'publications'/pub['product_id']/'sections.jsonl')!=pub['records_sha256']:errors.append('Actual normalized record bytes differ from independently audited source-ID/bodyhash set')
 for name,entry in cp['units'].items():
  receipt=json.loads((a.run/entry['receipt']).read_text());body=a.run/receipt['body_file']
  if sha(body)!=entry['sha256'] or sha(body)!=receipt['sha256'] or receipt['status']!=200 or receipt.get('access_stop'):errors.append('Actual raw source receipt binding '+name)
 files={str(p.relative_to(a.run)):sha(p) for p in sorted(a.run.rglob('*')) if p.is_file()}
 if len(files)!=r['source_file_count']:errors.append('Actual source file count changed')
 report={'schema_version':1,'kind':'Independent current-verifier receipt/current-code/actual-source binding','passed':not errors,'errors':errors,'network_requests_sent':0,'source_writes':False,'family_receipt_sha256':sha(a.receipt),'independent_raw_inventory_audit_sha256':sha(a.inventory_audit),'current_modules_sha256':r['current_implementation'],'family_current_implementation_hash':r['current_implementation_hash'],'family_readonly_result':r['result'],'actual_proof_files_sha256':files,'scope_note':'Consumes exact current family58check replay receipt and independently checks every cited module/raw-unit/body hash plus previous independent full raw-TOC/Doc/record audit. No repeated63second model replay; no new live acquisition or broader scope claimed.'};print(json.dumps(report,indent=2));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
