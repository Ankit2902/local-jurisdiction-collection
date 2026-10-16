#!/usr/bin/env python3
"""Offline receipt/hash/text checks for actual publisher downloads. Makes no network requests."""
from __future__ import annotations
import argparse,datetime as dt,hashlib,json
from pathlib import Path
from export_intake import Rejected,write_result

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def qualify(file:Path,receipt_path:Path,out:Path):
 receipt=json.loads(receipt_path.read_text())
 for key in ('source_url','jurisdiction','publication','selection_scope','retrieved_at','artifact_kind','acquisition_mode','edition_evidence','artifact_sha256','upstream_receipt_path','upstream_receipt_sha256','acquisition_script_sha256','acquisition_script_path'):
  if not isinstance(receipt.get(key),str) or not receipt[key].strip():raise Rejected('missing canonical receipt field '+key)
 if receipt.get('download_status')!='acquired':raise Rejected('actual acquired download required; visible button/print preview/login dialog does not qualify')
 if receipt['artifact_kind']!='publisher-export':raise Rejected('only a publisher-generated export can qualify this download method; browser print and preview remain separate')
 citations=receipt.get('selected_citations')
 if not isinstance(citations,list) or not citations or any(not isinstance(c,str) or not c.strip() for c in citations):raise Rejected('at least one expected selected citation required')
 if not isinstance(receipt.get('artifact_bytes'),int) or receipt['artifact_bytes']!=file.stat().st_size:raise Rejected('file byte length disagrees with acquisition receipt')
 upstream=(receipt_path.parent/receipt['upstream_receipt_path']).resolve()
 if not upstream.is_file() or digest(upstream)!=receipt['upstream_receipt_sha256']:raise Rejected('upstream acquisition receipt absent or SHA256 mismatch')
 script=(receipt_path.parent/receipt['acquisition_script_path']).resolve()
 if not script.is_file() or digest(script)!=receipt['acquisition_script_sha256']:raise Rejected('executed acquisition script absent or SHA256 mismatch')
 if digest(file)!=receipt['artifact_sha256']:raise Rejected('download SHA256 disagrees with acquisition receipt')
 proof=receipt.get('currentness_check',{})
 if not isinstance(proof,dict):raise Rejected('currentness_check must be an object')
 # Identity and citations are required. A publisher date, when supplied, must occur in actual extracted bytes.
 expected=[receipt['jurisdiction'],*citations]
 if proof.get('expected_export_text'):expected.append(proof['expected_export_text'])
 result=write_result(file,receipt,out,expected_sha=receipt['artifact_sha256'],expected_format=receipt.get('format'),pages=receipt.get('sample_pdf_pages'),expect=expected)
 classification='PASS_BOUNDED_DOWNLOADED_FILE_CHECKS' if result['sample_status']=='PASS' else 'REVIEW_REQUIRED_FILE_ACQUIRED'
 report={'schema_version':1,'checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),'classification':classification,'file_sha256':result['input']['sha256'],'canonical_receipt_sha256':digest(receipt_path),'upstream_receipt_sha256':digest(upstream),'selected_citations_checked':citations,'acquisition_mode':receipt['acquisition_mode'],'publisher_export':True,'sample_status':result['sample_status'],'currentness_check':proof,'currentness_status':'MATCHED_EXPECTED_EXPORT_TEXT_REQUIRES_SOURCE_RECONCILIATION' if proof.get('expected_export_text') else 'NO_EXPORT_DATE_EXPECTATION_MANUAL_REVIEW','legal_semantic_status':'MANUAL_REVIEW_REQUIRED','whole_publication_complete':False,'method_acquisition_claim':'Recorded by external acquisition receipt; local intake does not authenticate the browser session or prove whole-code extraction.'}
 (out/'download-checks.json').write_text(json.dumps(report,indent=2)+'\n');(out/'canonical-receipt.json').write_bytes(receipt_path.read_bytes());return report

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--file',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
 try:r=qualify(args.file,args.receipt,args.out);print(json.dumps(r));return 0 if r['sample_status']=='PASS' else 2
 except (Rejected,OSError,ValueError) as e:print(json.dumps({'status':'REJECTED','error':str(e)}));return 1
if __name__=='__main__':raise SystemExit(main())
