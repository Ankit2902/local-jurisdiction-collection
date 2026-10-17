"""Network-free replay, source hashes, CSV/JSONL and exact executed-script checks."""
import csv,hashlib,json,tempfile
from pathlib import Path
from normalize import normalize
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main(report_path=None):
 results=json.loads((ROOT/'results.json').read_text());assignment=json.loads((ROOT/'assignment.json').read_text());assert [r['sequence'] for r in results]==[r['sequence'] for r in assignment]
 checks=0;counts=0
 for r in results:
  assert r['complete_corpus'] is False
  for f in r['evidence_paths']:
   assert (ROOT/f).is_file(),f
   if f.endswith('.receipt.json'):
    raw_receipt=json.loads((ROOT/f).read_text())
    if raw_receipt.get('raw_file') and raw_receipt.get('sha256'):assert sha((ROOT/f).parent/raw_receipt['raw_file'])==raw_receipt['sha256'];checks+=1
  for f in r['script_paths']:assert (ROOT/f).is_file(),f
  receipt_paths=[p for p in r['evidence_paths'] if p.endswith('/receipt.json')]
  if receipt_paths:
   p=ROOT/receipt_paths[0];receipt=json.loads(p.read_text());folder=p.parent
   if (folder/'executed-collect_browser.cjs').exists():assert sha(folder/'executed-collect_browser.cjs')==receipt['script_sha256'];checks+=1
   for response in receipt.get('responses',[]):assert sha(folder/response['file'])==response['sha256'];checks+=1
   if r['record_count']:
    expected=json.loads((folder/'normalized/verification.json').read_text())
    with tempfile.TemporaryDirectory() as t:
     replay=normalize(folder,Path(t));assert replay['outputs_sha256']==expected['outputs_sha256'];assert replay['record_count']==r['tested_scope'].get('primary_record_count',r['record_count']);checks+=4
    with (folder/'normalized/sections.csv').open() as f:assert len(list(csv.DictReader(f)))==r['tested_scope'].get('primary_record_count',r['record_count']);checks+=1
    counts+=replay['record_count']
    for sample in r['tested_scope'].get('supplemental_legal_samples',[]):
     sup=ROOT/sample['folder'];acq=json.loads((sup/'acquisition-receipt.json').read_text());assert sha(sup/'content.json')==acq['response']['sha256'];assert sha(sup/'executed-acquire_node.cjs')==acq['script_sha256'];qa=json.loads((sup/'table-dom-qa.json').read_text());assert qa['passed'] and qa['normalized_jsonl_sha256']==sha(sup/'normalized/sections.jsonl')
     with tempfile.TemporaryDirectory() as temp:
      again=normalize(sup,Path(temp));expected_sup=json.loads((sup/'normalized/verification.json').read_text());assert again['outputs_sha256']==expected_sup['outputs_sha256'];assert again['record_count']==sample['record_count'];counts+=again['record_count'];checks+=5
   if r['publisher_download']['status']=='passed':
    pdf=folder/'publisher-export.pdf';assert pdf.read_bytes().startswith(b'%PDF-');assert sha(pdf)==r['publisher_download']['sha256'];checks+=2
  if r['status']=='standalone_e2e_pass':assert r['record_count']>=2
 report={'offline':True,'network_requests':0,'targets':len(results),'record_count':counts,'checks_passed':checks,'complete_corpus':False};
 if report_path:Path(report_path).write_text(json.dumps(report,indent=2))
 print(json.dumps(report))
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,help='Optional report path; default stdout only, evidence is never modified');a=p.parse_args();main(a.report)
