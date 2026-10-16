#!/usr/bin/env python3
"""Offline verify the current headed pilot receipts, raw bytes, and CSV/JSON outputs."""
import csv,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 report=read(ROOT/'HEADED-VALIDATION.json');rows=report['jurisdictions']
 assert len(rows)==14 and len({r['slug'] for r in rows})==14
 revisions={sha(p):p for p in (ROOT/'headed-live').glob('executed-r*/headed_probe.py')}
 total=0;downloads=0
 for row in rows:
  receipt_path=ROOT/row['pipeline_acquisition_receipt'];receipt=read(receipt_path)
  assert receipt['accepted'] and not receipt.get('rate_limit'),row['slug']
  assert receipt['initial_http_status']==200 and receipt['final_document_http_status']==200
  assert all(e['status']!=429 for e in receipt['response_chronology'])
  assert receipt['script_sha256'] in revisions,'Executed source revision missing'
  assert sha(receipt_path)==row['pipeline_acquisition_receipt_sha256']
  raw=receipt_path.parent/receipt['raw_artifact_path'];assert sha(raw)==receipt['sha256']==row['source_sha256']
  assert receipt['browser_state']['sha256']==receipt['after_capture']['sha256']==sha(raw)
  assert receipt['browser_state']['identity']==receipt['after_capture']['identity']==row['edition']
  result_path=ROOT/row['pipeline_report_path'];result=read(result_path)
  assert result['standalone_e2e_verified'] and not result['errors'] and result['unresolved_nodes']==0
  assert result['receipt_sha256']==sha(receipt_path) and result['parsed_records']==row['output_records']>0
  for relative,expected in result['export_hashes'].items():assert sha(result_path.parent/relative)==expected,relative
  export=result_path.parent/'exports';records=read(export/'aggregate-fulltext.json')['provisions']
  with (export/'aggregate-fulltext.csv').open(encoding='utf-8-sig',newline='') as f:assert list(csv.DictReader(f))==records
  assert len(records)==row['output_records'];total+=len(records)
  if row['publisher_download']['file_acquired']:
   d=row['publisher_download'];assert sha(ROOT/d['path'])==d['sha256'];assert (ROOT/d['path']).stat().st_size==d['bytes'];downloads+=1
  assert not row['full_collection_verified'] and not row['publication_inventory_verified']
 assert total==report['unique_city_output_records']==134
 assert downloads==report['publisher_pdf_files_acquired']
 print(json.dumps({'status':'PASS','cities':len(rows),'unique_city_records':total,'publisher_pdf_files':downloads,'live_network_requests':0}))
if __name__=='__main__':main()
